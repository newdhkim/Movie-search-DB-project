from db_connect import open_db, close_db


def split_values(value):
    if value is None:
        return []

    value = str(value).strip()
    if value == "":
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


def clean_text(value):
    if value is None:
        return None

    return (
        str(value)
        .replace("\ufeff", "")  # BOM
        .replace("\u200b", "")  # zero-width space
        .replace("\u200c", "")  # zero-width non-joiner
        .replace("\u200d", "")  # zero-width joiner
        .replace("\u2060", "")  # word joiner
        .replace("\u00a0", " ")  # non-breaking space
        .replace("\u3000", " ")  # ideographic space
        .strip()
    )


def get_or_create(cur, cache, table_name, id_col, name_col, value):
    if value in cache:
        return cache[value]

    cur.execute(
        f"SELECT {id_col} FROM {table_name} WHERE {name_col} = %s",
        (value,)
    )
    row = cur.fetchone()

    if row:
        cache[value] = row[id_col]
        return row[id_col]

    cur.execute(
        f"INSERT INTO {table_name} ({name_col}) VALUES (%s)",
        (value,)
    )

    new_id = cur.lastrowid
    cache[value] = new_id
    return new_id


def insert_relation(cur, table_name, movie_id, target_col, target_id):
    cur.execute(
        f"""
        INSERT IGNORE INTO {table_name} (movie_id, {target_col})
        VALUES (%s, %s)
        """,
        (movie_id, target_id)
    )


def main():
    read_conn, read_cur = open_db()
    write_conn, write_cur = open_db()

    genre_cache = {}
    nation_cache = {}
    director_cache = {}
    company_cache = {}

    read_cur.execute("""
        SELECT *
        FROM movie_info
        ORDER BY movie_info_id
    """)

    count = 0

    while True:
        row = read_cur.fetchone()

        if row is None:
            break

        write_cur.execute("""
            INSERT INTO movie (
                movie_name,
                movie_name_en,
                production_year,
                movie_type,
                production_status,
                raw_movie_info_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            clean_text(row["movie_name"]),
            clean_text(row["movie_name_en"]),
            row["production_year"],
            clean_text(row["movie_type"]),
            clean_text(row["production_status"]),
            row["movie_info_id"]
        ))

        movie_id = write_cur.lastrowid

        for genre_name in split_values(row["genre"]):
            genre_id = get_or_create(
                write_cur, genre_cache,
                "genre", "genre_id", "genre_name",
                genre_name
            )
            insert_relation(write_cur, "movie_genre", movie_id, "genre_id", genre_id)

        for nation_name in split_values(row["production_country"]):
            nation_id = get_or_create(
                write_cur, nation_cache,
                "nation", "nation_id", "nation_name",
                nation_name
            )
            insert_relation(write_cur, "movie_nation", movie_id, "nation_id", nation_id)

        for director_name in split_values(row["director"]):
            director_id = get_or_create(
                write_cur, director_cache,
                "director", "director_id", "director_name",
                director_name
            )
            insert_relation(write_cur, "movie_director", movie_id, "director_id", director_id)

        for company_name in split_values(row["production_company"]):
            company_id = get_or_create(
                write_cur, company_cache,
                "company", "company_id", "company_name",
                company_name
            )
            insert_relation(write_cur, "movie_company", movie_id, "company_id", company_id)

        count += 1

        if count % 1000 == 0:
            write_conn.commit()
            print(f"{count}개 처리 완료")

    write_conn.commit()

    print("정규화 데이터 insert 완료")
    print(f"movie: {count}개")
    print(f"genre: {len(genre_cache)}개")
    print(f"nation: {len(nation_cache)}개")
    print(f"director: {len(director_cache)}개")
    print(f"company: {len(company_cache)}개")

    close_db(read_conn, read_cur)
    close_db(write_conn, write_cur)


if __name__ == "__main__":
    main()
