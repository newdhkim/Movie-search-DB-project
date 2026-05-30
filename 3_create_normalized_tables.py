from db_connect import open_db, close_db

conn, cur = open_db()

sql = """
DROP TABLE IF EXISTS movie_company;
DROP TABLE IF EXISTS movie_director;
DROP TABLE IF EXISTS movie_nation;
DROP TABLE IF EXISTS movie_genre;

DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS director;
DROP TABLE IF EXISTS nation;
DROP TABLE IF EXISTS genre;
DROP TABLE IF EXISTS movie;

CREATE TABLE movie (
    movie_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    movie_name VARCHAR(255),
    movie_name_en VARCHAR(255),
    production_year INT,
    movie_type VARCHAR(100),
    production_status VARCHAR(100),
    raw_movie_info_id BIGINT,
    FOREIGN KEY (raw_movie_info_id)
        REFERENCES movie_info(movie_info_id)
);

CREATE TABLE genre (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE nation (
    nation_id INT AUTO_INCREMENT PRIMARY KEY,
    nation_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE director (
    director_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    director_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE company (
    company_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE movie_genre (
    movie_id BIGINT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id),
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id)
);

CREATE TABLE movie_nation (
    movie_id BIGINT NOT NULL,
    nation_id INT NOT NULL,
    PRIMARY KEY (movie_id, nation_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id),
    FOREIGN KEY (nation_id) REFERENCES nation(nation_id)
);

CREATE TABLE movie_director (
    movie_id BIGINT NOT NULL,
    director_id BIGINT NOT NULL,
    PRIMARY KEY (movie_id, director_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id),
    FOREIGN KEY (director_id) REFERENCES director(director_id)
);

CREATE TABLE movie_company (
    movie_id BIGINT NOT NULL,
    company_id BIGINT NOT NULL,
    PRIMARY KEY (movie_id, company_id),
    FOREIGN KEY (movie_id) REFERENCES movie(movie_id),
    FOREIGN KEY (company_id) REFERENCES company(company_id)
);
"""

cur.execute(sql)
conn.commit()

print("정규화 테이블 생성 완료")

close_db(conn, cur)