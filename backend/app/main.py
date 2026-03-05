import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import sys
import uvicorn


# 최상단에서 Windows 루프 정책 강제 설정
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router
from app.middleware.logging import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up chai-na backend...")
    yield
    print("Shutting down...")

app = FastAPI(title="chai-na API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health(): return {"status": "ok"}

if __name__ == "__main__":
    # 실행 시에도 루프 정책 재설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
