import os
import pathlib
import random
import typing as t
from configparser import ConfigParser

import hikari

from saucebot.components import log
from saucebot.components.config import config
from saucebot.components.helpers import escape_markdown

__all__ = ['lang', 'rand_lang']


# Set up localization for use elsewhere in the application
language = config["bot"]["language"]
language_config = ConfigParser()
language_config.read(os.path.join(pathlib.Path(__file__).parent.resolve(), f'{language}.ini'), 'utf-8')


def lang(category: str, key: str, replacements: t.Optional[dict] = None, default=None,
         member: t.Optional[t.Union[hikari.Member, hikari.User]] = None):
    """
    Provides easy to use application localization in the form of ini configuration files

    Language strings can be added or altered in the lang/{language}.ini file
    """
    string = language_config.get(category, key, fallback=default)  # type: str
    if string:
        if replacements:
            for rkey, rvalue in replacements.items():
                string = string.replace(f"{{{rkey}}}", str(rvalue))

        if member:
            string = member_replacements(string, member)

    else:
        log.warning(f"Missing {language} language string: {key} ({category})")
        return '<Missing language string>'

    return string


def rand_lang(category: str, replacements: t.Optional[dict] = None, default=None,
              member: t.Optional[t.Union[hikari.Member, hikari.User]] = None, return_index: bool = False):
    """
    An alternative to the regular lang() method that pulls a random language string from the specified category
    """
    strings = language_config.items(category)
    if strings:
        key, string = random.choice(strings)
    else:
        if default:
            key, string = None, default
        else:
            log.warning(f"Missing {language} language category: {category}")
            return '<Missing language string>'

    if replacements:
        for rkey, rvalue in replacements.items():
            string = string.replace(f"{{{rkey}}}", rvalue)

    if member:
        string = member_replacements(string, member)

    if return_index:
        return string, key

    return string


def member_replacements(string: str, member: t.Union[hikari.Member, hikari.User]) -> str:
    """
    Perform some standard replacements for language strings
    """
    if isinstance(member, hikari.Member):
        name = member.nickname or member.username
    else:
        name = member.username

    # Escape any formatting tags from the users name
    name = escape_markdown(name)

    string = string.replace('{display_name}', name)
    string = string.replace('{mention}', member.mention)

    return string
