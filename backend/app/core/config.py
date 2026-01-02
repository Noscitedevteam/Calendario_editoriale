from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # AI APIs
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str = ""
    PERPLEXITY_API_KEY: str = ""
    
    # App
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000"
    BASE_URL: str = "https://calendar.noscite.it"
    FRONTEND_URL: str = "https://calendar.noscite.it"
    
    # Meta (Facebook + Instagram)
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    
    # Google Business
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # LinkedIn
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    
    # Encryption (per token OAuth)
    ENCRYPTION_KEY: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
