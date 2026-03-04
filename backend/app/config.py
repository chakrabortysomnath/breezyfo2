from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Breeze API credentials
    breeze_api_key: str = ""
    breeze_api_secret: str = ""
    breeze_session_token: str = ""

    # QuotaGuard proxy (for static IP on Render)
    quotaguard_url: str = ""

    # App settings
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
