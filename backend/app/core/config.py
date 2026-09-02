from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CH_HOST: str = "localhost"
    CH_PORT: int = 8123
    CH_USER: str = "default"
    CH_PASSWORD: str = "secret_password"
    CH_DATABASE: str = "tgmetrics"

    JWT_SECRET: str = "super_secret_jwt_key_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    TELEGRAM_BOT_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()