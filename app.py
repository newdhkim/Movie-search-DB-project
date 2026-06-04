import os

from flask import Flask, render_template, request
import pymysql

from search_movies import search_movies, count_movies

app = Flask(__name__)


def get_page():
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return 1

    return max(page, 1)


def get_search_mode(name):
    mode = request.args.get(name, "contains")
    if mode not in ("contains", "prefix"):
        return "contains"

    return mode


@app.route("/", methods=["GET"])
def index():
    page = get_page()
    page_size = 10

    title = request.args.get("title")
    director = request.args.get("director")
    start_year = request.args.get("start_year")
    end_year = request.args.get("end_year")
    sort = request.args.get("sort", "update_desc")
    movie_search_mode = get_search_mode("movie_search_mode")

    db_error = None

    try:
        total_count = count_movies(
            title=title,
            director=director,
            start_year=start_year,
            end_year=end_year,
            movie_search_mode=movie_search_mode
        )
        total_pages = (total_count + page_size - 1) // page_size
        total_pages = max(total_pages, 1)
        page = min(page, total_pages)

        results = search_movies(
            title=title,
            director=director,
            start_year=start_year,
            end_year=end_year,
            sort=sort,
            page=page,
            page_size=page_size,
            movie_search_mode=movie_search_mode
        )
    except pymysql.MySQLError as error:
        results = []
        total_count = 0
        total_pages = 1
        page = 1
        db_error = f"데이터베이스 연결 또는 조회 중 오류가 발생했습니다: {error}"

    return render_template(
        "search.html", 
        results=results, 
        result_count=total_count,
        page=page,
        total_pages=total_pages,
        db_error=db_error
    )

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )
