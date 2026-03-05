import google.generativeai as genai
from app.core.config import settings
from typing import AsyncGenerator

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    async def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    async def translate(self, text: str, target_lang: str = "ko") -> str:
        prompt = f"Translate the following to {target_lang}:\n{text}"
        return await self.generate(prompt)

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response = self.model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
