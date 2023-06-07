import datetime

import hikari
import humanize
import lightbulb
import sentry_sdk
from lightbulb.ext import tasks

from bot import bot
from saucebot.components import log, embeds
from saucebot.components.config import config
from saucebot.components.helpers import codewrap
from saucebot.extensions import extensions

__all__ = []


# Load extensions
from saucebot.lang.lang import lang
from saucebot.models.servers import Servers

for ext in extensions:
    bot.load_extensions(ext)


@bot.listen()
async def on_start(event: hikari.StartingEvent):
    """
    Initialize sentry logging on boot
    """
    if config["sentry"]["enabled"]:
        if config["bot"]["in_dev"] and not config["sentry"]["log_in_dev"]:
            log.debug("Sentry logging disabled in dev mode")
            return

        sentry_sdk.init(
            config["sentry"]["dsn"],
            debug=config["bot"]["log_level"] == "DEBUG",
            environment="development" if config["bot"]["in_dev"] else "production"
        )


@bot.listen(hikari.events.StartedEvent)
async def on_ready(event: hikari.StartingEvent):
    """
    Initialize tasks once the bot is ready
    """
    update_presence.start()


@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        log.exception("An unknown error occurred: %s", exc_info=event.exception)
        if not config["bot"]["in_dev"]:
            sentry_sdk.capture_exception(event.exception)

        return

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception
    exceptions = [exception]
    caught = False
    _embeds = []

    if isinstance(exception, lightbulb.errors.CommandNotFound):
        log.debug(str(exception))
        return

    if isinstance(exception, lightbulb.errors.CheckFailure):
        if exception.causes:
            exceptions = exception.causes

    for exc in exceptions:
        if isinstance(exc, lightbulb.NotOwner):
            _embeds.append(embeds.error(
                message=f"Only my owner is allowed to ask me to do that!"
            ))
            caught = True
            continue

        if isinstance(exc, lightbulb.errors.CommandIsOnCooldown):
            # noinspection PyUnresolvedReferences
            retry_after = humanize.naturaldelta(datetime.timedelta(seconds=exception.retry_after))
            _embeds.append(embeds.error(
                message=f"The sauce commands are on cooldown!\n\nPlease try again in `{retry_after}`"
            ))
            caught = True
            continue

        if isinstance(exc, lightbulb.errors.MissingRequiredPermission):
            perms = "\n".join(f"**{mp.name}**" for mp in exc.missing_perms)
            _embeds.append(embeds.error(
                message=f"You are missing the following permissions needed to run this command:\n\n {perms}"
            ))
            caught = True
            continue

        if isinstance(exc, lightbulb.errors.OnlyInGuild):
            _embeds.append(embeds.error(
                message=f"This command can only be executed inside of a guild"
            ))
            caught = True
            continue

        log.warning(f"Uncaught check error: {exc}")

    if not caught:
        raise exception

    await event.context.respond(embeds=_embeds[:10])


@bot.command()
@lightbulb.command("help", "Learn how to find the source of images posted in this server!", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def bot_help(ctx: lightbulb.SlashContext):
    embed = embeds.base_embed()
    embed.title = lang('Misc', 'info_title')
    embed.description = lang('Misc', 'info_desc')

    query_count = await Servers.count_queries()
    embed.url = "https://www.patreon.com/saucebot"
    embed.add_field("Sauce queries processed", codewrap(humanize.intcomma(query_count)))
    await ctx.respond(embed)


@tasks.task(h=1)
async def update_presence():
    """
    Update the bots' presence/query counter
    """
    query_count = await Servers.count_queries()
    await bot.update_presence(
        activity=hikari.Activity(
            name=f"{humanize.intcomma(query_count)} sauce queries",
            type=hikari.ActivityType.PLAYING
        )
    )


bot.run()
