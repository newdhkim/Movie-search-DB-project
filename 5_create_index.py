from db_connect import open_db, close_db


INDEXES = [
    ("idx_movie_name", "movie", ("movie_name",)),
    ("idx_movie_year_id", "movie", ("production_year", "movie_id")),
    ("idx_movie_director_director_movie", "movie_director", ("director_id", "movie_id")),
]


def index_exists(cur, index_name, table_name):
    cur.execute(
        """
        SELECT COUNT(*) AS index_count
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND index_name = %s
        """,
        (table_name, index_name)
    )
    row = cur.fetchone()
    return row["index_count"] > 0


def main():
    conn, cur = open_db()

    try:
        for index_name, table_name, column_names in INDEXES:
            if index_exists(cur, index_name, table_name):
                print(f"{index_name}: 이미 존재")
                continue

            column_sql = ", ".join(column_names)
            cur.execute(
                f"CREATE INDEX {index_name} ON {table_name}({column_sql})"
            )
            print(f"{index_name}: 생성 완료")

        conn.commit()
        print("인덱스 확인 완료")
    finally:
        close_db(conn, cur)


if __name__ == "__main__":
    main()
