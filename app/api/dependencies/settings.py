from app.config import Settings, load_config


def get_settings() -> Settings:
    return load_config()

