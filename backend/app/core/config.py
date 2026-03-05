import os
from pydantic_settings import BaseSettings

# backend 폴더의 절대 경로 계산
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, "..", ".env")

class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    gemini_api_key: str = ""
    baidu_index_api_key: str = ""
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    hs_code_api_key: str = ""
    uncomtrade_api_key: str = ""
    hs_percentage_api_key: str = ""
    kotra_news_api_key: str = ""
    breaking_news_api_key: str = ""
    OPENAI_API_MODEL: str = "gpt-5.2"

    class Config:
        env_file = ENV_PATH
        extra = "ignore"

settings = Settings()
