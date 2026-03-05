# Backend - 기술팀

## 구현 기능
- 사용자가 한국어로 입력한 자연어 검색어를 AI 기반 nlp 기술을 사용하여 중국어로 번역 후 시스템에 저장
- 저장된 검색어를 小红书, 淘宝 내에 검색 엔진에 입력하여 결과 크롤링 + 百度 Index에도 동일하게 적용
- 추출한 결과를 AI가 분석하고, AI에게 프롬프트로 학습시킨 양식에 대입하여 화면에 출력
- 추출한 결과들을 이후 모든 기능마다 적용할 수 있도록 마스터 데이터로 저장

## 🛠️ 기술 스택 (Tech Stack)

| 분류 | 기술 |
|------|------|
| Language | Java 17 |
| Framework | Spring Boot 3.x |
| Database | MySQL 8.0 |
| ORM | JPA / Hibernate |
| Infra | AWS EC2, S3 |
| 기타 | Docker, Redis |

## 📁 프로젝트 구조 (Project Structure)
```
backend/                              ── Python 3.11 + FastAPI
    ├── app/
    │   ├── main.py                       # CORS + Lifespan + 미들웨어 + 헬스체크
    │   ├── api/v1/
    │   │   ├── router.py                 # 모든 라우터 집약
    │   │   └── endpoints/
    │   │       ├── analysis.py           # 분석 시작/정보 수집/시장 분석/레포트
    │   │       ├── branding.py           # 브랜드 스토리 생성
    │   │       ├── marketing.py          # 홍보 이미지/홍보 영상/마케팅 문구 생성
    │   │       ├── wanghong.py           # 왕홍 리스트/광고 제안서
    │   │       └── chatbot.py            # 챗봇
	  └── README.md
```

## ⚙️ 설치 및 실행 (Getting Started)

### 사전 요구사항 (Prerequisites)
- Java 17+
- Docker & Docker Compose

### 환경 변수 설정
루트 디렉토리에 `.env` 파일을 생성하고 아래 값을 설정하세요.
```
DB_URL=jdbc:mysql://localhost:3306/dbname
DB_USERNAME=root
DB_PASSWORD=your_password
JWT_SECRET=your_secret_key
```

### 실행 방법

**로컬 실행**
```bash
git clone https://github.com/username/project-backend.git
cd project-backend
./gradlew clean build
./gradlew bootRun
```

**Docker 실행**
```bash
docker-compose up --build
```

## 📡 API 문서 (API Docs)

> 서버 실행 후 Swagger UI에서 전체 문서를 확인할 수 있습니다.  
> `http://localhost:8080/swagger-ui/index.html`

### 주요 API 목록

#### 👤 User
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/users/signup | 회원가입 | ✗ |
| POST | /api/users/login | 로그인 | ✗ |
| GET | /api/users/me | 내 정보 조회 | ✓ |

#### 📝 Post (예시)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/posts | 게시글 목록 조회 | ✗ |
| POST | /api/posts | 게시글 작성 | ✓ |
| PATCH | /api/posts/{id} | 게시글 수정 | ✓ |
| DELETE | /api/posts/{id} | 게시글 삭제 | ✓ |

### 공통 응답 형식
```json
{
  "success": true,
  "data": { },
  "message": "요청이 성공적으로 처리되었습니다."
}
```

### 에러 코드
| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| USER_NOT_FOUND | 404 | 유저를 찾을 수 없음 |
| UNAUTHORIZED | 401 | 인증 실패 |
| INVALID_INPUT | 400 | 입력값 오류 |