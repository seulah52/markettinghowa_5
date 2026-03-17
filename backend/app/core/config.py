import os
from pydantic_settings import BaseSettings

# backend 폴더 기준 .env 로드 (로컬: backend/.env, 배포: Render Environment Variables)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    # AI / API
    gemini_api_key: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_API_MODEL: str = "gpt-4o"
    DEEPSEEK_API_KEY: str = ""
    baidu_index_api_key: str = ""
    hs_code_api_key: str = ""
    uncomtrade_api_key: str = ""
    hs_percentage_api_key: str = ""
    kotra_news_api_key: str = ""
    breaking_news_api_key: str = ""
    REMOVE_BG_API_KEY: str = ""
    PORTER_GROK_API_KEY: str = ""
    PORTER_API_URL: str = ""
    TEXT_MODEL: str = "gpt-4o"
    IMAGE_MODEL: str = "gpt-image-1"

    class Config:
        env_file = ENV_PATH
        extra = "ignore"


settings = Settings()
