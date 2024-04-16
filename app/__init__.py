from . import infrastructure
from . import dto
from .api import controllers, dependencies
from app.config import load_config

load_config()
