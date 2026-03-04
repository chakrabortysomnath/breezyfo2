from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Breeze API credentials
    breeze_api_key: str = ""
    breeze_api_secret: str = ""
    breeze_session_token: str = ""

    # QuotaGuard proxy (for static IP on Render)
    quotaguard_url: str = ""

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Admin & email
    admin_email: str = ""
    gmail_sender: str = ""
    gmail_app_password: str = ""
    backend_url: str = "http://localhost:8000"

    # App settings
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
