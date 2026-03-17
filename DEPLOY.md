# 배포 가이드 (markettinghowa / chai-na)

프로젝트는 **프론트엔드(Next.js)** 와 **백엔드(FastAPI)** 로 구성됩니다. 각각 별도 서비스로 배포합니다.

---

## 실제 배포 도메인 (참고)

| 용도 | URL |
|------|-----|
| **GitHub** | https://github.com/seulah52/markettinghowa.git |
| **Vercel (프론트)** | https://markettinghowa-5.vercel.app |
| **Vercel 프리뷰** | https://markettinghowa-5-fa8yhq99a-seulah52s-projects.vercel.app |
| **Render (백엔드)** | https://markettinghowa-5.onrender.com |
| **Supabase** | https://oljekyqhsqawqmxzpkeg.supabase.co |

- Vercel **Environment Variables**에 `NEXT_PUBLIC_API_URL=https://markettinghowa-5.onrender.com` 설정.
- Supabase anon 키는 Vercel/프론트 환경 변수 `NEXT_PUBLIC_SUPABASE_ANON_KEY`에, service role 키는 Render/백엔드에만 설정.
- **환경 변수 이름**: 배포 시에는 `backend/.env`에 쓰는 **변수명과 동일하게** Render / Vercel에 추가. 전체 목록은 **`.env.example`** 참고. 백엔드는 `app/core/config.py`의 Settings에서 읽습니다.

---

## ⚠️ "서버 통신 중 오류가 발생했습니다" 해결 방법

배포된 사이트(markettinghowa-5.vercel.app)는 열리는데 **분석 시작** 등에서 위 오류가 나면, 아래를 순서대로 확인하세요.

1. **Vercel 환경 변수**
   - [Vercel](https://vercel.com) → 프로젝트 선택 → **Settings** → **Environment Variables**
   - `NEXT_PUBLIC_API_URL` = `https://markettinghowa-5.onrender.com` (값 끝에 `/` 없음)
   - 없으면 **Add** 후 **Production**, **Preview**, **Development** 모두 체크하고 저장.

2. **환경 변수 추가/수정 후 반드시 재배포**
   - `NEXT_PUBLIC_*` 변수는 **빌드 시** 번들에 들어갑니다. 저장만 하면 기존 배포에는 적용되지 않습니다.
   - **Deployments** 탭 → 최신 배포 오른쪽 **⋯** → **Redeploy** 실행.

3. **백엔드 동작 확인**
   - 브라우저에서 [https://markettinghowa-5.onrender.com/health](https://markettinghowa-5.onrender.com/health) 열기.
   - `{"status":"ok"}` 가 보이면 백엔드는 정상. (무료 플랜은 15분 비활성 시 슬립되므로, 첫 요청은 30초~1분 걸릴 수 있음.)

4. **CORS**
   - 백엔드 코드에 `https://markettinghowa-5.vercel.app` 이 `allow_origins`에 포함되어 있어야 합니다. 포함 후 Render에서 **재배포**해야 적용됩니다.

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

| 변수명 | 설명 | 배포 시 값 |
|--------|------|------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | `https://oljekyqhsqawqmxzpkeg.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon 키 | (Supabase 대시보드에서 복사) |
| `NEXT_PUBLIC_API_URL` | 배포된 백엔드 API URL | `https://markettinghowa-5.onrender.com` |

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
5. 배포 후 **서비스 URL** 사용: `https://markettinghowa-5.onrender.com`

Playwright를 쓰는 API가 있다면, Render에서 별도 네이티브 의존성 또는 Docker 빌드가 필요할 수 있습니다.

---

## 4단계: 프론트엔드 배포 (예: Vercel)

1. [Vercel](https://vercel.com/) 로그인 후 **Add New → Project**.
2. 저장소 선택 후 **Root Directory**를 `frontend`로 지정.
3. **Environment Variables**에 다음 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` = `https://markettinghowa-5.onrender.com`
4. **Deploy** 실행.

---

## 5단계: CORS 및 도메인 반영

백엔드가 배포된 프론트 도메인을 허용해야 합니다.

- `backend/app/main.py`의 `allow_origins`에 이미 반영됨:
  - `https://markettinghowa-5.vercel.app`, `https://markettinghowa-5-fa8yhq99a-seulah52s-projects.vercel.app`

수정 후 백엔드를 다시 배포합니다.

---

## 6단계: 동작 확인

1. 프론트엔드 URL 접속 후 로그인/회원가입 등 Supabase 연동 확인.
2. 분석/브랜딩 등 API를 쓰는 기능 실행 후, 브라우저 개발자 도구 네트워크 탭에서 `NEXT_PUBLIC_API_URL`로 요청이 가는지 확인.
3. 백엔드 `/health` 호출: `https://markettinghowa-5.onrender.com/health` → `{"status":"ok"}` 확인.

---

## 요약 체크리스트

- [ ] `.env` / 플랫폼 환경 변수 설정 (프론트·백)
- [ ] `npm run build` (frontend) 성공
- [ ] 백엔드 먼저 배포 후 URL 확보
- [ ] `NEXT_PUBLIC_API_URL`에 백엔드 URL 설정
- [ ] 프론트엔드 배포
- [ ] 백엔드 CORS에 프론트 도메인 추가
- [ ] 실제 사용 플로우로 테스트
