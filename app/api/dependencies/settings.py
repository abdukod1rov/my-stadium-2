from pathlib import Path
from os.path import dirname, join
import os

from app.config import Settings, load_config


def get_settings() -> Settings:
    return load_config()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
