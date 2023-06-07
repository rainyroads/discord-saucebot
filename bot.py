import hikari
import lightbulb
import miru
from lightbulb.ext import tasks

from saucebot.components.config import config

__all__ = ['bot']

_token = config["discord"]["dev"]["token"] if config["bot"]["in_dev"] else config["discord"]["prod"]["token"]
bot = lightbulb.BotApp(_token, intents=hikari.Intents.ALL_UNPRIVILEGED, logs=config['bot']['log_level'])


# Extensions
tasks.load(bot)
miru.install(bot)
