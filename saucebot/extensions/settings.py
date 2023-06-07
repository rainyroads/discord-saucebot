import hikari
import lightbulb

from saucebot.components import embeds
from saucebot.lang.lang import lang
from saucebot.models.servers import Servers

settings = lightbulb.Plugin("Settings")
settings.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
settings.add_checks(lightbulb.guild_only)


@settings.command()
@lightbulb.command("config", "Configure guild specific settings", ephemeral=True, auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def config(ctx: lightbulb.SlashContext):
    pass


@config.child()
@settings.command()
@lightbulb.option("api_key", "Your SauceNAO API key", str)
@lightbulb.command("api_key", "Provide a SauceNAO API key for this guild to increase search limits")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def api_key(ctx: lightbulb.SlashContext):
    try:
        await Servers.register(ctx.get_guild(), ctx.options.api_key)
    except ValueError as e:
        return await ctx.respond(embed=embeds.error(str(e)))

    await ctx.respond(embed=embeds.success(message=lang('Sauce', 'registered_api_key')))


# Extension methods
def load(_bot: lightbulb.BotApp):
    _bot.add_plugin(settings)


def unload(_bot: lightbulb.BotApp):
    _bot.remove_plugin(settings)



