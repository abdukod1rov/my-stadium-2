from dataclasses import dataclass
from pydantic_settings import BaseSettings


class DBConfig(BaseSettings):
    host: str
    password: str
    user: str
    name: str
    port: int


class ApiConfig(BaseSettings):
    secret: str


class SettingsExtractor(BaseSettings):
    DB__HOST: str
    DB__PORT: int
    DB__NAME: str
    DB__USER: str
    DB__PASSWORD: str

    API__SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    db: DBConfig
    api: ApiConfig


def load_config():
    settings = SettingsExtractor()

    to_return = Settings(
        db=DBConfig(
            host=settings.DB__HOST,
            port=settings.DB__PORT,
            name=settings.DB__NAME,
            user=settings.DB__USER,
            password=settings.DB__PASSWORD
        ),
        api=ApiConfig(
            secret=settings.API__SECRET
        )
    )
    return to_return


