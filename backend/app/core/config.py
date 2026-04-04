from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPORTLINK_CLIENT_ID: str
    
    CLUB_NAME: str | None = None
    CLUB_CODE: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()


