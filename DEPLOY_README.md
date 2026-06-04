# AWS EC2 Ubuntu 배포 가이드

이 프로젝트는 Flask 앱을 Gunicorn으로 `127.0.0.1:5000`에서 실행하고, 외부 접속은 Nginx 80번 포트로만 받는 구성을 사용합니다. MySQL은 같은 EC2 내부의 `localhost`를 사용합니다.

## 1. EC2 보안 그룹

인바운드 규칙은 다음처럼 설정합니다.

- SSH: 22번, 본인 IP만 허용
- HTTP: 80번, 필요한 대역 허용
- 5000번 포트: 열지 않음
- MySQL 3306번 포트: 외부에 열지 않음

## 2. 패키지 설치

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx mysql-server
```

## 3. 프로젝트 배치

예시는 프로젝트를 `/home/ubuntu/kobis-movie-db`에 둔다고 가정합니다.

```bash
cd /home/ubuntu
git clone <your-repository-url> kobis-movie-db
cd kobis-movie-db
```

Git을 쓰지 않는 경우에는 프로젝트 폴더 전체를 같은 경로로 업로드하면 됩니다.

## 4. Python 가상환경 및 의존성 설치

```bash
cd /home/ubuntu/kobis-movie-db
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. 환경변수 설정

실제 DB 비밀번호는 코드에 넣지 않고 `.env`에만 작성합니다.

```bash
cp .env.example .env
nano .env
```

예시:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=db_user
DB_PASSWORD=your_real_password
DB_NAME=movie_db
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=0
```

## 6. MySQL 설정

```bash
sudo mysql
```

```sql
CREATE DATABASE movie_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'db_user'@'localhost' IDENTIFIED BY 'your_real_password';
GRANT ALL PRIVILEGES ON movie_db.* TO 'db_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

테이블 생성 및 데이터 적재:

```bash
source venv/bin/activate
python 1_create_table.py
python 2_insert_movie_info.py
python 3_create_normalized_tables.py
python 4_normalize_movie_data.py
python 5_create_index.py
```

## 7. Gunicorn 단독 실행 테스트

Gunicorn은 외부 IP가 아니라 `127.0.0.1:5000`에만 바인딩합니다.

```bash
source venv/bin/activate
gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
```

다른 터미널에서 확인:

```bash
curl http://127.0.0.1:5000/
```

## 8. systemd 서비스 등록

```bash
sudo cp deploy/kobis-movie-db.service /etc/systemd/system/kobis-movie-db.service
sudo systemctl daemon-reload
sudo systemctl enable kobis-movie-db
sudo systemctl start kobis-movie-db
sudo systemctl status kobis-movie-db
```

로그 확인:

```bash
journalctl -u kobis-movie-db -f
```

## 9. Nginx 설정

```bash
sudo cp deploy/nginx_kobis_movie_db.conf /etc/nginx/sites-available/kobis-movie-db
sudo ln -s /etc/nginx/sites-available/kobis-movie-db /etc/nginx/sites-enabled/kobis-movie-db
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

브라우저에서 EC2 퍼블릭 IP로 접속합니다.

```text
http://<EC2_PUBLIC_IP>/
```

## 10. 배포 구조 요약

```text
Internet
  -> EC2 Security Group: 80 only
  -> Nginx :80
  -> Gunicorn 127.0.0.1:5000
  -> Flask app
  -> MySQL localhost:3306
```

## 11. 운영 명령어

```bash
sudo systemctl restart kobis-movie-db
sudo systemctl restart nginx
sudo systemctl status kobis-movie-db
sudo systemctl status nginx
```

## 12. GitHub Actions CI/CD

`.github/workflows/deploy.yml`은 `main` 또는 `master` 브랜치에 push될 때 다음 순서로 실행됩니다.

GitHub Actions를 이용해 push 시 Python 문법 검사를 수행하고,
검사 통과 후 EC2 서버에 SSH 접속하여 최신 코드를 pull한 뒤
`requirements.txt` 재설치 및 systemd 서비스 재시작을 자동화하였습니다.

1. Python 파일 문법 검사
2. EC2 서버에 SSH 접속
3. 서버의 프로젝트 폴더에서 최신 코드 반영
4. `requirements.txt` 기반 의존성 설치
5. `kobis-movie-db` systemd 서비스 재시작

GitHub 저장소의 `Settings > Secrets and variables > Actions`에 다음 Secrets를 등록합니다.

```text
EC2_HOST=EC2 퍼블릭 IP 또는 도메인
EC2_USER=ubuntu
EC2_SSH_KEY=EC2 접속용 private key 전체 내용
EC2_APP_DIR=/home/ubuntu/kobis-movie-db
EC2_SERVICE_NAME=kobis-movie-db
```

`EC2_APP_DIR`와 `EC2_SERVICE_NAME`은 선택값입니다. 등록하지 않으면 각각 `/home/ubuntu/kobis-movie-db`, `kobis-movie-db`를 기본값으로 사용합니다.

서버에서는 최초 1회 배포 준비가 되어 있어야 합니다.

```bash
cd /home/ubuntu
git clone <your-repository-url> kobis-movie-db
cd kobis-movie-db
cp .env.example .env
nano .env
sudo cp deploy/kobis-movie-db.service /etc/systemd/system/kobis-movie-db.service
sudo systemctl daemon-reload
sudo systemctl enable kobis-movie-db
```

## 주의사항

- `app.py`의 직접 실행 모드는 기본적으로 `debug=False`입니다.
- 운영 환경에서는 `.env`를 Git에 올리지 않습니다.
- EC2 보안 그룹에서 5000번 포트를 열지 않습니다.
- MySQL은 `localhost` 접속만 사용합니다.
- GitHub Actions는 `.env`와 DB 데이터 적재를 자동으로 수행하지 않습니다. 운영 DB 설정과 초기 데이터 적재는 서버에서 최초 1회 직접 수행합니다.
