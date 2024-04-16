import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import controllers, dependencies
from app.infrastructure.database.factory import create_pool, make_connection_string
from app import load_config

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    settings = load_config()
    app = FastAPI(
        docs_url='/docs',
        version='1.0.0',
    )
    pool = create_pool(url=make_connection_string(settings=settings.db))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    controllers.setup(app)
    dependencies.setup(app, pool, settings)
    return app

