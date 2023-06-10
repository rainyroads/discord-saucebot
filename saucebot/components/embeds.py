import typing as t
from enum import Enum

import hikari

from saucebot.lang.lang import lang

__all__ = ['Colors', 'base_embed', 'default', 'timeout', 'success', 'error']


class Colors(Enum):
    DEFAULT = hikari.Color(0x3F497F)
    SUCCESS = hikari.Color(0xBFDB38)
    DANGER = hikari.Color(0xF94A29)
    WARNING = hikari.Color(0xFCE22A)
    ERROR = hikari.Color(0xD61355)


def base_embed():
    return hikari.Embed()


def default(*, message: t.Optional[str] = None, footer: bool = False, color: Colors = Colors.DEFAULT) -> hikari.Embed:
    """
    Gets a speech bubble formatted embed
    """
    embed = hikari.Embed()

    if message:
        if footer:
            embed.set_footer(text=message)
        else:
            embed.description = message

    if color:
        embed.color = color.value

    return embed


def timeout() -> hikari.Embed:
    """
    Generates a generic response for interaction timeouts
    """
    return default(
        message=lang('Errors', 'interaction_timeout'),
        color=Colors.ERROR
    )


def error(message: str, face: str = None) -> hikari.Embed:
    """
    Returns a generic error template
    """
    return default(
        message=str(message),
        color=Colors.ERROR
    )


def success(message: str, face: str = None) -> hikari.Embed:
    """
    Returns a generic success template
    """
    return default(
        message=str(message),
        color=Colors.SUCCESS
    )

