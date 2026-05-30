import pandas as pd
from db_connect import open_db, close_db

EXCEL_PATH = "영화정보 리스트_2026-05-28.xls"

COLUMNS = [
    "movie_name",
    "movie_name_en",
    "production_year",
    "production_country",
    "movie_type",
    "genre",
    "production_status",
    "director",
    "production_company"
]

def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()
    return value if value else None


def clean_year(value):
    if pd.isna(value):
        return None

    try:
        return int(float(value))
    except:
        return None


def read_sheet(sheet_name):
    if sheet_name == "영화정보 리스트":
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=4)

        df = df.rename(columns={
            "영화명": "movie_name",
            "영화명(영문)": "movie_name_en",
            "제작연도": "production_year",
            "제작국가": "production_country",
            "유형": "movie_type",
            "장르": "genre",
            "제작상태": "production_status",
            "감독": "director",
            "제작사": "production_company"
        })

        df = df[COLUMNS]

    elif sheet_name == "영화정보 리스트_2":
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=None)

        # 앞 9개 컬럼만 사용
        df = df.iloc[:, :9]
        df.columns = COLUMNS

        # 혹시 첫 행에 헤더가 들어간 경우 제거
        df = df[df["movie_name"] != "영화명"]

    else:
        raise ValueError(f"알 수 없는 시트명: {sheet_name}")

    return df


def main():
    conn, cur = open_db()

    insert_sql = """
    INSERT INTO movie_info (
        movie_name,
        movie_name_en,
        production_year,
        production_country,
        movie_type,
        genre,
        production_status,
        director,
        production_company,
        source_sheet
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    total = 0

    for sheet_name in ["영화정보 리스트", "영화정보 리스트_2"]:
        print(f"{sheet_name} 읽는 중...")

        df = read_sheet(sheet_name)

        rows = []

        for _, row in df.iterrows():
            if pd.isna(row["movie_name"]):
                continue

            rows.append((
                clean_value(row["movie_name"]),
                clean_value(row["movie_name_en"]),
                clean_year(row["production_year"]),
                clean_value(row["production_country"]),
                clean_value(row["movie_type"]),
                clean_value(row["genre"]),
                clean_value(row["production_status"]),
                clean_value(row["director"]),
                clean_value(row["production_company"]),
                sheet_name
            ))

        cur.executemany(insert_sql, rows)
        conn.commit()

        print(f"{sheet_name}: {len(rows)}개 삽입 완료")
        total += len(rows)

    print(f"총 {total}개 삽입 완료")

    close_db(conn, cur)


if __name__ == "__main__":
    main()