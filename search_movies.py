from db_connect import open_db, close_db


def is_empty(value):
    return value is None or str(value).strip() == ""


def parse_year(value):
    if is_empty(value):
        return None

    try:
        return int(value)
    except ValueError:
        return None


def make_like_pattern(value, mode):
    keyword = value.strip()

    if mode == "prefix":
        return f"{keyword}%"

    return f"%{keyword}%"


def search_movies(
    title=None,
    director=None,
    start_year=None,
    end_year=None,
    sort=None,
    page=1,
    page_size=10,
    movie_search_mode="contains",
    director_search_mode="contains"
):
    conn, cur = open_db()

    try:
        start_year = parse_year(start_year)
        end_year = parse_year(end_year)

        sql = """
            SELECT
                m.movie_id,
                m.movie_name,
                m.movie_name_en,
                m.production_year,
                GROUP_CONCAT(DISTINCT n.nation_name ORDER BY n.nation_name SEPARATOR ', ') AS production_country,
                m.movie_type,
                GROUP_CONCAT(DISTINCT g.genre_name ORDER BY g.genre_name SEPARATOR ', ') AS genre,
                m.production_status,
                GROUP_CONCAT(DISTINCT d.director_name ORDER BY d.director_name SEPARATOR ', ') AS director,
                GROUP_CONCAT(DISTINCT c.company_name ORDER BY c.company_name SEPARATOR ', ') AS production_company
            FROM movie m
            LEFT JOIN movie_director md ON m.movie_id = md.movie_id
            LEFT JOIN director d ON md.director_id = d.director_id
            LEFT JOIN movie_genre mg ON m.movie_id = mg.movie_id
            LEFT JOIN genre g ON mg.genre_id = g.genre_id
            LEFT JOIN movie_nation mn ON m.movie_id = mn.movie_id
            LEFT JOIN nation n ON mn.nation_id = n.nation_id
            LEFT JOIN movie_company mc ON m.movie_id = mc.movie_id
            LEFT JOIN company c ON mc.company_id = c.company_id
            WHERE 1=1
        """

        params = []

        if not is_empty(title):
            sql += " AND m.movie_name LIKE %s"
            params.append(make_like_pattern(title, movie_search_mode))

        if not is_empty(director):
            sql += " AND d.director_name LIKE %s"
            params.append(make_like_pattern(director, director_search_mode))

        if start_year is not None:
            sql += " AND m.production_year >= %s"
            params.append(start_year)

        if end_year is not None:
            sql += " AND m.production_year <= %s"
            params.append(end_year)

        sql += """
            GROUP BY
                m.movie_id,
                m.movie_name,
                m.movie_name_en,
                m.production_year,
                m.movie_type,
                m.production_status
        """

        if sort == "year_desc":
            sql += " ORDER BY m.production_year DESC"
        
        elif sort == "name_asc":
            sql += " ORDER BY m.movie_name ASC"

        else:
            sql += " ORDER BY m.movie_id DESC"

        offset = (page - 1) * page_size

        sql += " LIMIT %s OFFSET %s"

        params.append(page_size)
        params.append(offset)

        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        close_db(conn, cur)

def count_movies(
        title=None, 
        director=None, 
        start_year=None, 
        end_year=None,
        movie_search_mode="contains",
        director_search_mode="contains"
):
    conn, cur = open_db()

    try:
        start_year = parse_year(start_year)
        end_year = parse_year(end_year)

        sql = """
            SELECT COUNT(DISTINCT m.movie_id) AS total_count
            FROM movie m
            LEFT JOIN movie_director md ON m.movie_id = md.movie_id
            LEFT JOIN director d ON md.director_id = d.director_id
            WHERE 1=1
        """

        params = []

        if not is_empty(title):
            sql += " AND m.movie_name LIKE %s"
            params.append(make_like_pattern(title, movie_search_mode))

        if not is_empty(director):
            sql += " AND d.director_name LIKE %s"
            params.append(make_like_pattern(director, director_search_mode))

        if start_year is not None:
            sql += " AND m.production_year >= %s"
            params.append(start_year)

        if end_year is not None:
            sql += " AND m.production_year <= %s"
            params.append(end_year)

        cur.execute(sql, params)
        row = cur.fetchone()
        return row["total_count"]
    finally:
        close_db(conn, cur)

# if __name__ == "__main__":
#     result = search_movies(title="워페어")

#     for row in result:
#         print(row)
