from db_connect import open_db, close_db

conn, cur = open_db()
sql = """
DROP TABLE IF EXISTS movie_info;
CREATE TABLE movie_info (
    movie_info_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    movie_name VARCHAR(255),
    movie_name_en VARCHAR(255),
    production_year INT,
    production_country VARCHAR(500),
    movie_type VARCHAR(100),
    genre VARCHAR(500),
    production_status VARCHAR(100),
    director VARCHAR(500),
    production_company VARCHAR(500),
    source_sheet VARCHAR(50)
);
"""

cur.execute(sql)
conn.commit()

print("movie_info 테이블 생성 완료")

close_db(conn, cur)