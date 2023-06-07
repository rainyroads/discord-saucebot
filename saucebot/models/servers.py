import re
import typing as t

import hikari
import pysaucenao.containers
from pysaucenao import SauceNao
from sqlalchemy import Column, BigInteger, String, select, insert, update, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from saucebot.components import log
from saucebot.lang.lang import lang
from saucebot.models import async_engine

Base = declarative_base()
Session = sessionmaker()


api_re = re.compile(r"[a-z\d]{32}")


class Servers(Base):
    __tablename__ = 'servers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    server_id = Column(BigInteger, unique=True)
    api_key = Column(String(40), nullable=True)
    queries = Column(BigInteger)

    @classmethod
    async def get_api_key(cls, guild) -> t.Optional[str]:
        """
        Gets the SauceNao API key for the specified guild
        Args:
            guild (discord.Guild):

        Returns:
            t.Optional[str]
        """
        async with async_engine.connect() as conn:
            result = await conn.execute(
                select(Servers)
                .where(Servers.server_id == guild.id)
                .limit(1)
            )

            server = result.fetchone()
            if server:
                return server.api_key

    @classmethod
    async def register(cls, guild: hikari.Guild, api_key: t.Optional[str]):
        # Make sure the key is valid
        if not api_re.match(api_key):
            raise ValueError(lang("Sauce", "bad_api_key"))

        # Test the API key
        if api_key:
            saucenao = SauceNao(api_key=api_key)
            test = await saucenao.test()

            # Make sure the API key is valid
            if test.error:
                raise ValueError(lang("Sauce", "rejected_api_key"))

            # Free API keys cannot be used as they are IP restricted
            if test.account_type == pysaucenao.containers.ACCOUNT_FREE:
                raise ValueError(lang("Sauce", "api_free"))

            log.info("Registering API key for server", guild)

        # Update or create a new server entry
        async with async_engine.connect() as conn:
            # Check for an existing entry
            result = await conn.execute(
                select(Servers)
                .where(Servers.server_id == guild.id)
                .limit(1)
            )

            # Update
            if result.fetchone():
                await conn.execute(
                    update(Servers)
                    .where(Servers.server_id == guild.id)
                    .values(api_key=api_key)
                )
                await conn.commit()
                return

            # Insert
            await conn.execute(
                insert(Servers)
                .values(server_id=guild.id, api_key=api_key)
            )
            await conn.commit()
            return

    @classmethod
    async def log_query(cls, guild: t.Optional[hikari.Guild]):
        guild_id = guild.id if guild else 0

        # Update or create a new server entry
        async with async_engine.connect() as conn:
            # Check for an existing entry
            result = await conn.execute(
                select(Servers)
                .where(Servers.server_id == guild_id)
                .limit(1)
            )

            # Update
            if result.fetchone():
                await conn.execute(
                    update(Servers)
                    .where(Servers.server_id == guild_id)
                    .values(queries=Servers.queries + 1)
                )
                await conn.commit()
                return

            # Insert
            await conn.execute(
                insert(Servers)
                .values(server_id=guild_id, queries=1)
            )
            await conn.commit()
            return

    @classmethod
    async def count_queries(cls) -> int:
        async with async_engine.connect() as conn:
            result = await conn.execute(
                select(func.sum(Servers.queries))
            )

            return result.scalar()
