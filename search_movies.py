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


def build_filter_sql(
    title=None,
    director=None,
    start_year=None,
    end_year=None,
    movie_search_mode="contains"
):
    joins = []
    where = ["1=1"]
    params = []

    if not is_empty(director):
        joins.append("LEFT JOIN movie_director md ON m.movie_id = md.movie_id")
        joins.append("LEFT JOIN director d ON md.director_id = d.director_id")
        where.append("d.director_name LIKE %s")
        params.append(make_like_pattern(director, "contains"))

    if not is_empty(title):
        where.append(f"{movie_name_sql()} LIKE %s")
        params.append(make_like_pattern(title, movie_search_mode))

    if start_year is not None:
        where.append("m.production_year >= %s")
        params.append(start_year)

    if end_year is not None:
        where.append("m.production_year <= %s")
        params.append(end_year)

    return "\n".join(joins), " AND ".join(where), params


def movie_name_sql():
    return "m.movie_name"


def clean_movie_name_sql():
    return """TRIM(
            REPLACE(
            REPLACE(
            REPLACE(
            REPLACE(
            REPLACE(
            REPLACE(
            REPLACE(m.movie_name,
                CONVERT(UNHEX('EFBBBF') USING utf8mb4), ''),
                CONVERT(UNHEX('E2808B') USING utf8mb4), ''),
                CONVERT(UNHEX('E2808C') USING utf8mb4), ''),
                CONVERT(UNHEX('E2808D') USING utf8mb4), ''),
                CONVERT(UNHEX('E281A0') USING utf8mb4), ''),
                CONVERT(UNHEX('C2A0') USING utf8mb4), ' '),
                CONVERT(UNHEX('E38080') USING utf8mb4), ' ')
        )"""


def sort_sql(sort):
    if sort == "year_desc":
        return "m.production_year DESC, m.movie_id DESC"

    if sort == "name_asc":
        clean_name = clean_movie_name_sql()
        return """CASE
            WHEN HEX(LEFT({clean_name}, 1)) BETWEEN 'EAB080' AND 'ED9EA3' THEN 0
            WHEN HEX(LEFT(UPPER({clean_name}), 1)) BETWEEN '41' AND '5A' THEN 1
            WHEN HEX(LEFT({clean_name}, 1)) BETWEEN '30' AND '39' THEN 2
            ELSE 3
        END,
        {clean_name} ASC,
        m.movie_id DESC""".format(clean_name=clean_name)

    return "m.movie_id DESC"


def search_movies(
    title=None,
    director=None,
    start_year=None,
    end_year=None,
    sort=None,
    page=1,
    page_size=10,
    movie_search_mode="contains"
):
    conn, cur = open_db()

    try:
        start_year = parse_year(start_year)
        end_year = parse_year(end_year)
        offset = (page - 1) * page_size

        joins, where_sql, params = build_filter_sql(
            title=title,
            director=director,
            start_year=start_year,
            end_year=end_year,
            movie_search_mode=movie_search_mode
        )

        # 먼저 현재 페이지에 필요한 movie_id만 가져온다.
        # 이렇게 해야 전체 119,104건을 모두 JOIN/GROUP BY 한 뒤 LIMIT 하는 비용을 피할 수 있다.
        page_sql = f"""
            SELECT
                m.movie_id,
                m.movie_name,
                m.production_year
            FROM movie m
            {joins}
            WHERE {where_sql}
            GROUP BY m.movie_id, m.movie_name, m.production_year
            ORDER BY {sort_sql(sort)}
            LIMIT %s OFFSET %s
        """
        cur.execute(page_sql, params + [page_size, offset])
        page_rows = cur.fetchall()
        movie_ids = [row["movie_id"] for row in page_rows]

        if not movie_ids:
            return []

        id_placeholders = ", ".join(["%s"] * len(movie_ids))

        detail_sql = f"""
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
            WHERE m.movie_id IN ({id_placeholders})
            GROUP BY
                m.movie_id,
                m.movie_name,
                m.movie_name_en,
                m.production_year,
                m.movie_type,
                m.production_status
            ORDER BY FIELD(m.movie_id, {id_placeholders})
        """

        cur.execute(detail_sql, movie_ids + movie_ids)
        return cur.fetchall()
    finally:
        close_db(conn, cur)


def count_movies(
        title=None,
        director=None,
        start_year=None,
        end_year=None,
        movie_search_mode="contains"
):
    conn, cur = open_db()

    try:
        start_year = parse_year(start_year)
        end_year = parse_year(end_year)

        joins, where_sql, params = build_filter_sql(
            title=title,
            director=director,
            start_year=start_year,
            end_year=end_year,
            movie_search_mode=movie_search_mode
        )

        if is_empty(director):
            sql = f"""
                SELECT COUNT(*) AS total_count
                FROM movie m
                WHERE {where_sql}
            """
        else:
            sql = f"""
                SELECT COUNT(DISTINCT m.movie_id) AS total_count
                FROM movie m
                {joins}
                WHERE {where_sql}
            """

        cur.execute(sql, params)
        row = cur.fetchone()
        return row["total_count"]
    finally:
        close_db(conn, cur)
