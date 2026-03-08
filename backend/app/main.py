import asyncio
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. 상단 정책 설정 (안전한getattr 방식 유지)
if sys.platform == 'win32':
    policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if policy:
        asyncio.set_event_loop_policy(policy())

# 기존 임포트 유지
from app.api.v1.router import router
from app.middleware.logging import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up chai-na backend...")
    yield
    print("Shutting down...")

app = FastAPI(title="chai-na API", version="1.0.0", lifespan=lifespan)

# 2. CORS 설정 수정 (발표 및 배포를 위해 모든 origin 허용 또는 Netlify 주소 추가 추천)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://markettinghowa-5.netlify.app"],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)
app.add_middleware(LoggingMiddleware)
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health(): 
    return {"status": "ok"}

if __name__ == "__main__":
    # 3. 하단 실행부 오류 수정: 직접 참조를 제거하고 상단과 동일한 로직 적용
    if sys.platform == 'win32':
        policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
        if policy:
            asyncio.set_event_loop_policy(policy())
            
    # uvicorn 실행 시 'app.main:app' 경로가 실제 Render 설정과 일치하는지 확인 필요
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)