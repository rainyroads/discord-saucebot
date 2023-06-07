import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

from saucebot.components.config import config

__all__ = ['async_engine', 'Base']


if config["bot"]["in_dev"]:
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    db_url = config["database"]["dev"]["url"]
else:
    db_url = config["database"]["prod"]["url"]


async_engine = create_async_engine(db_url)
Base = declarative_base()
