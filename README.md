# KOBIS Movie Search DB Project

KOBIS 영화정보 엑셀 데이터를 MySQL에 적재하고, 정규화된 영화 검색 데이터베이스와 Flask 기반 검색 화면을 구현한 데이터베이스 기말 프로젝트입니다.

이 프로젝트는 일반적인 회원/게시판형 백엔드 서비스가 아니라, **영화 데이터 적재 → 정규화 → 검색 기능 구현 → 페이지네이션 최적화 → 인덱스 성능 비교** 흐름을 중심으로 한 DB 설계 및 검색 시스템 프로젝트입니다.

## 프로젝트 목표

- KOBIS 영화정보 엑셀 데이터를 MySQL 데이터베이스에 적재
- 원본 비정규화 테이블을 정규화된 관계형 스키마로 분리
- 영화명, 감독명, 제작연도 기반 검색 기능 구현
- 페이지네이션과 정렬을 적용한 검색 결과 화면 구현
- B+Tree 인덱스와 `EXPLAIN ANALYZE`를 활용한 검색 성능 비교
- Gunicorn, Nginx, systemd 기반의 Ubuntu 서버 배포 설정 구성

## 기술 스택

- Python
- Flask
- MySQL
- PyMySQL
- HTML/CSS
- Gunicorn
- Nginx

## 주요 기능

### 1. KOBIS 영화 데이터 적재

- KOBIS 영화정보 엑셀 파일 사용
- 총 119,104건의 영화 데이터를 `movie_info` 원본 테이블에 적재
- 엑셀의 다중값 속성을 이후 정규화 과정에서 분리

### 2. 데이터베이스 정규화

원본 데이터는 영화, 장르, 제작국가, 감독, 제작사 정보가 하나의 테이블에 포함된 비정규화 구조였습니다.

정규화 후 주요 테이블은 다음과 같습니다.

- `movie`
- `genre`
- `nation`
- `director`
- `company`
- `movie_genre`
- `movie_nation`
- `movie_director`
- `movie_company`

장르, 제작국가, 감독, 제작사는 영화와 N:M 관계를 가질 수 있으므로 관계 테이블을 통해 연결했습니다.

### 3. 영화 검색 화면

Flask와 HTML/CSS를 사용해 영화 검색 화면을 구현했습니다.

검색 조건:

- 영화명
- 감독명
- 제작연도 범위
- 개봉일자 입력 UI

정렬 조건:

- 최신업데이트순
- 제작연도순
- 영화명순

결과 컬럼:

- 영화명
- 영화명(영문)
- 영화코드
- 제작연도
- 제작국가
- 유형
- 장르
- 제작상태
- 감독
- 제작사

### 4. 페이지네이션 성능 개선

초기에는 전체 검색 결과에 대해 `JOIN`과 `GROUP BY`를 수행한 뒤 `LIMIT/OFFSET`을 적용하는 구조였습니다. 이 방식은 첫 화면에서도 119,104건 전체에 가까운 데이터를 조인하고 집계해야 해서 로딩이 느려질 수 있었습니다.

개선 후에는 먼저 페이지에 필요한 `movie_id` 10개만 조회한 뒤, 해당 ID에 대해서만 상세 정보를 `JOIN`하도록 쿼리 구조를 변경했습니다.

이를 통해 불필요한 상세 조인 범위를 줄이고, 검색 결과 페이지의 응답 속도를 개선했습니다.

### 5. 인덱스 설계 및 검색 방식 비교

검색 조건에 맞춰 다음 인덱스를 생성했습니다.

```sql
CREATE INDEX idx_movie_name
ON movie(movie_name);

CREATE INDEX idx_director_name
ON director(director_name);

CREATE INDEX idx_movie_year
ON movie(production_year);
```

영화명과 감독명 검색은 두 가지 방식으로 선택할 수 있습니다.

- 포함 검색: `LIKE '%검색어%'`
- 접두어 검색: `LIKE '검색어%'`

포함 검색은 사용자가 기대하는 일반 검색 방식에 가깝지만, 문자열 앞부분이 와일드카드이기 때문에 B+Tree 인덱스 활용이 어렵습니다.

접두어 검색은 인덱스 효과를 확인하기 위한 비교 실험용 검색 방식이며, `EXPLAIN ANALYZE`를 통해 Index Range Scan 여부를 확인할 수 있도록 구현했습니다.

## 프로젝트 구조

```text
.
├── app.py                         # Flask 애플리케이션 진입점
├── db_connect.py                  # MySQL 연결 및 .env 설정 로드
├── search_movies.py               # 영화 검색, 필터링, 정렬, 페이지네이션 쿼리
├── 1_create_table.py              # movie_info 원본 테이블 생성
├── 2_insert_movie_info.py         # 엑셀 데이터 적재
├── 3_create_normalized_tables.py  # 정규화 테이블 생성
├── 4_normalize_movie_data.py      # 원본 데이터 정규화 및 관계 테이블 적재
├── 5_create_index.py              # 검색 성능 비교용 인덱스 생성
├── templates/
│   └── search.html                # 영화 검색 화면 템플릿
├── deploy/
│   ├── gunicorn_command.txt
│   ├── kobis-movie-db.service
│   └── nginx_kobis_movie_db.conf
├── requirements.txt
├── .env.example
└── DEPLOY_README.md
```

## 실행 방법

### 1. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell에서는 다음과 같이 실행합니다.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 참고해 `.env` 파일을 생성합니다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=db_user
DB_PASSWORD=your_password_here
DB_NAME=movie_db
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=0
```

실제 DB 비밀번호가 포함된 `.env` 파일은 Git에 올리지 않습니다.

### 3. 데이터베이스 생성

MySQL에서 프로젝트용 데이터베이스를 생성합니다.

```sql
CREATE DATABASE movie_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 4. 테이블 생성 및 데이터 적재

아래 순서대로 스크립트를 실행합니다.

```bash
python 1_create_table.py
python 2_insert_movie_info.py
python 3_create_normalized_tables.py
python 4_normalize_movie_data.py
python 5_create_index.py
```

### 5. Flask 앱 실행

```bash
python app.py
```

기본 실행 주소:

```text
http://127.0.0.1:5000
```

## 배포

Ubuntu EC2 서버 배포를 위해 다음 구성을 준비했습니다.

- Gunicorn: Flask 앱 실행
- Nginx: 80번 포트에서 외부 요청 수신 후 Gunicorn으로 프록시
- systemd: 서버 재부팅 후 자동 실행
- `.env`: DB 접속 정보 분리

자세한 배포 절차는 [DEPLOY_README.md](./DEPLOY_README.md)를 참고하면 됩니다.

## 보안 및 설정

- DB 접속 정보는 `.env`로 분리
- 사용자 입력값은 SQL 문자열에 직접 결합하지 않고 파라미터 바인딩 사용
- 정렬 옵션과 검색 모드는 허용된 값만 사용
- 배포 환경에서 Flask `debug` 모드 비활성화
- Gunicorn은 `127.0.0.1:5000`에서만 실행하고, 외부 접속은 Nginx 80번 포트를 통해 처리

## 한계 및 개선 방향

현재 프로젝트는 데이터베이스 수업 목적의 검색 시스템이므로 일반적인 백엔드 서비스 기능은 포함되어 있지 않습니다.

개선 가능한 부분:

- REST API 형태로 검색 기능 분리
- Controller / Service / Repository 계층 분리
- 자동화 테스트 추가
- CI/CD 파이프라인 구축
- 데이터 적재 및 정규화 스크립트의 마이그레이션 관리 개선
- 검색 성능 측정 결과를 문서화하여 수치 기반 비교 추가

## 프로젝트에서 배운 점

- 다중값 속성을 가진 원본 데이터를 관계형 모델로 정규화하는 과정
- N:M 관계를 관계 테이블로 표현하는 방식
- 검색 조건에 맞는 인덱스 설계
- `LIKE '%검색어%'`와 `LIKE '검색어%'`의 인덱스 활용 차이
- 대용량 조회에서 페이지네이션 쿼리 구조가 성능에 미치는 영향
- Flask 앱을 Gunicorn/Nginx/systemd 기반으로 배포하기 위한 기본 구성
