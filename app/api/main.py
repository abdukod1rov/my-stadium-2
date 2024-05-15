import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import controllers, dependencies
from app.infrastructure.database.factory import create_pool, make_connection_string
from app import load_config
from .middlewares import ExceptionHandlerMiddleware
import sys


def main() -> FastAPI:
    settings = load_config()
    app = FastAPI(
        docs_url='/docs',
        version='1.0.0',
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

    logger.info('API is starting up')
    pool = create_pool(url=make_connection_string(settings=settings.db))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    #app.add_middleware(ExceptionHandlerMiddleware)
    controllers.setup(app)
    dependencies.setup(app, pool, settings)
    return app
