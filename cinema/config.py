from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite://./data/micro-cinema.db"

    class Config:
        case_sensitive = False
