import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.secret_key = os.getenv("SECRET_KEY", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
