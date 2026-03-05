import json
from typing import List
import openai
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import get_supabase

router = APIRouter()

# ✅ 비동기 클라이언트 하나로 통일 (LangChain 제거)
aclient = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """귀하는 '마케띵호와' 플랫폼의 전문 AI 컨설턴트입니다.
1. 중국 시장 분석, 샤오홍슈/타오바오 크롤링, 가구 및 리빙 수출 전략에 특화되어 있습니다.
2. 사용자가 가구 수출 요소를 물어보면 퀄리티, 친환경 인증(E0 등급), 물류 비용 등을 상세히 답변하세요.
3. 한국어와 중국어 전문 용어를 적절히 섞어 전문성을 보여주며, 정중하고 신뢰감 있는 톤을 유지하세요."""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


# ✅ 비동기 클라이언트로 통일 — 이벤트 루프 블로킹 해소
async def get_relevant_context(user_query: str) -> str:
    try:
        emb_res = await aclient.embeddings.create(
            input=user_query,
            model="text-embedding-3-small"
        )
        query_embedding = emb_res.data[0].embedding

        supabase = get_supabase()
        result = supabase.rpc("match_furniture_knowledge", {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,
            "match_count": 3
        }).execute()

        if not result.data:
            return ""
        return "\n".join([item["content"] for item in result.data])
    except Exception as e:
        print(f"RAG Error: {e}")
        return ""


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    context = await get_relevant_context(request.message)

    # ✅ 시스템 프롬프트에 RAG 컨텍스트 주입
    system_content = SYSTEM_PROMPT
    if context:
        system_content += f"\n\n[참고 지식 베이스]\n{context}"

    # ✅ 멀티턴: history를 messages 배열에 포함
    messages = [{"role": "system", "content": system_content}]
    for msg in request.history[-6:]:  # 최근 6개만 유지
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    async def event_generator():
        try:
            stream = await aclient.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                max_tokens=1000,
                temperature=0.7,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'content': delta.content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = json.dumps({"content": f"오류가 발생했습니다: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    # ✅ SSE 헤더 추가 — nginx 버퍼링 방지
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )