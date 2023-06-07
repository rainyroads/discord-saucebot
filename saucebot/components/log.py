import inspect
import logging
import typing as t

import hikari

from saucebot.components.helpers import make_utf8_safe

__all__ = ['debug', 'info', 'warning', 'error', 'exception']


def debug(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None, **kwargs):
    return logging.getLogger(get_module().__name__).debug(render_message(message, guild), **kwargs)


def info(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None, **kwargs):
    return logging.getLogger(get_module().__name__).info(render_message(message, guild), **kwargs)


def warning(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None, **kwargs):
    return logging.getLogger(get_module().__name__).warning(render_message(message, guild), **kwargs)


def error(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None, **kwargs):
    return logging.getLogger(get_module().__name__).error(render_message(message, guild), **kwargs)


def exception(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None, **kwargs):
    return logging.getLogger(get_module().__name__).exception(render_message(message, guild), **kwargs)


def get_module():
    stack = inspect.stack()[1]
    return inspect.getmodule(stack[0])


def render_message(message: str, guild: t.Optional[t.Union[hikari.Guild, int]] = None):
    if isinstance(guild, hikari.Guild):
        message = f"[{guild.name} ({guild.id})] {message}"
    elif isinstance(guild, int):
        message = f"[{guild}] {message}"
        
    return make_utf8_safe(message)
