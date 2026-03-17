# 배포 가이드 (markettinghowa / chai-na)

프로젝트는 **프론트엔드(Next.js)** 와 **백엔드(FastAPI)** 로 구성됩니다. 각각 별도 서비스로 배포합니다.

---

## 사전 준비

- [Node.js](https://nodejs.org/) (v18 이상)
- [Python](https://www.python.org/) (3.10 이상, 백엔드용)
- [Supabase](https://supabase.com/) 프로젝트
- [Google AI (Gemini)](https://ai.google.dev/) API 키
- 배포 플랫폼 계정 (예: Vercel, Render)

---

## 1단계: 환경 변수 정리

배포할 서비스에 아래 환경 변수를 설정합니다.

### 프론트엔드 (Next.js)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon 키 | (Supabase 대시보드에서 복사) |
| `NEXT_PUBLIC_API_URL` | **배포된 백엔드 API URL** | `https://your-backend.onrender.com` |

### 백엔드 (FastAPI)

| 변수명 | 설명 |
|--------|------|
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role 키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| (선택) `PLAYWRIGHT_BROWSERS_PATH` | Playwright 브라우저 경로 (호스팅 사양에 따름) |

`.env.example`을 복사해 `.env`를 만들고, 로컬에서 먼저 값을 채운 뒤 배포 플랫폼에도 동일하게 설정합니다.

---

## 2단계: 로컬 빌드 검증

배포 전에 로컬에서 빌드가 되는지 확인합니다.

```powershell
# 루트에서
cd "c:\Users\user\dev\프로젝트\2차 프로젝트(5조)\markettinghowa"

# 프론트엔드 의존성 설치 및 빌드
cd frontend
npm ci
npm run build
cd ..
```

백엔드는 로컬에서 실행해 API 동작을 확인합니다.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 3단계: 백엔드 배포 (예: Render)

1. [Render](https://render.com/) 로그인 후 **New → Web Service** 선택.
2. 저장소 연결 후 **Root Directory**를 `backend`로 지정.
3. **Build Command**: `pip install -r requirements.txt`  
   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment**에 `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY` 등 추가.
5. 배포 후 **서비스 URL**을 복사 (예: `https://chai-na-api.onrender.com`).

Playwright를 쓰는 API가 있다면, Render에서 별도 네이티브 의존성 또는 Docker 빌드가 필요할 수 있습니다.

---

## 4단계: 프론트엔드 배포 (예: Vercel)

1. [Vercel](https://vercel.com/) 로그인 후 **Add New → Project**.
2. 저장소 선택 후 **Root Directory**를 `frontend`로 지정.
3. **Environment Variables**에 다음 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` = 3단계에서 얻은 백엔드 URL (예: `https://chai-na-api.onrender.com`)
4. **Deploy** 실행.

---

## 5단계: CORS 및 도메인 반영

백엔드가 배포된 프론트 도메인을 허용해야 합니다.

- `backend/app/main.py`의 `allow_origins`에 Vercel(또는 사용 중인 도메인) 추가:
  - 예: `https://your-project.vercel.app`
- Netlify를 쓴다면 기존처럼 `https://markettinghowa-5.netlify.app` 유지.

수정 후 백엔드를 다시 배포합니다.

---

## 6단계: 동작 확인

1. 프론트엔드 URL 접속 후 로그인/회원가입 등 Supabase 연동 확인.
2. 분석/브랜딩 등 API를 쓰는 기능 실행 후, 브라우저 개발자 도구 네트워크 탭에서 `NEXT_PUBLIC_API_URL`로 요청이 가는지 확인.
3. 백엔드 `/health` 호출: `https://your-backend.onrender.com/health` → `{"status":"ok"}` 확인.

---

## 요약 체크리스트

- [ ] `.env` / 플랫폼 환경 변수 설정 (프론트·백)
- [ ] `npm run build` (frontend) 성공
- [ ] 백엔드 먼저 배포 후 URL 확보
- [ ] `NEXT_PUBLIC_API_URL`에 백엔드 URL 설정
- [ ] 프론트엔드 배포
- [ ] 백엔드 CORS에 프론트 도메인 추가
- [ ] 실제 사용 플로우로 테스트
