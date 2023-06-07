import hashlib
import re
import typing as t
from datetime import date

import anilist
import cachetools as cachetools
import hikari
import lightbulb
import pysaucenao
from pysaucenao import SauceNao

from saucebot.components import log, embeds
from saucebot.components.config import config
from saucebot.components.helpers import escape_markdown, truncate, codewrap
from saucebot.lang.lang import lang
from saucebot.modals.sauce.results import SauceResultsView
from saucebot.modals.sauce.select import SelectTemplateView
from saucebot.models.servers import Servers

sauce_plugin = lightbulb.Plugin("SauceNao")
user_cooldowns = lightbulb.CooldownManager(lambda ctx: lightbulb.UserBucket(300.0, 6))  # 6/5 minutes
guild_cooldowns = lightbulb.CooldownManager(lambda ctx: lightbulb.GuildBucket(86400.0, 100))  # 100/day
dm_cooldowns = lightbulb.CooldownManager(lambda ctx: lightbulb.GuildBucket(86400.0, 20))  # 20/day
sauce_cache = cachetools.TTLCache(maxsize=1024, ttl=3600)


@sauce_plugin.command()
@lightbulb.add_cooldown(300.0, 1, lightbulb.UserBucket)
@lightbulb.add_cooldown(86400.0, 100, lightbulb.GuildBucket)
@lightbulb.command("sauce", "Look up the source of an image using a specified URL or file upload")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def sauce():
    ...


@sauce_plugin.command()
@lightbulb.command("sauce", "Look up the source of an image in the specified message", ephemeral=True)
@lightbulb.implements(lightbulb.MessageCommand)
async def message_sauce(ctx: lightbulb.MessageContext):
    await _command_init(ctx)

    message = ctx.options.target  # type: hikari.Message
    image_attachments = _get_image_attachments(message)
    if not image_attachments:
        await ctx.respond(embeds.error(lang('Sauce', 'no_images')))
        return

    image_url = await _multiple_images_prompt(ctx, image_attachments)
    if not image_url:  # Prompt timeouts will result in this being None
        return

    await _run_sauce_command(ctx, image_url)


@sauce.child()
@lightbulb.option("image_url", "The URL of the image you wish to find the source of", str)
@lightbulb.command("url", "Look up the source of an image using a specified URL", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def sauce_url(ctx: lightbulb.SlashContext):
    await _command_init(ctx)

    await _run_sauce_command(ctx, ctx.options.image_url)


@sauce.child()
@lightbulb.option("image", "The image you wish to find the source of", hikari.Attachment)
@lightbulb.command("file", "Look up the source of an uploaded image", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def sauce_file(ctx: lightbulb.SlashContext):
    await _command_init(ctx)

    image_url = _get_attachment_image(ctx.options.image)
    await _run_sauce_command(ctx, image_url)


async def _command_init(ctx: lightbulb.Context):
    """
    Sends a defer response and checks for any active cooldowns
    """
    flags = hikari.MessageFlag.EPHEMERAL if ctx.get_guild() else hikari.MessageFlag.NONE
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=flags)
    await user_cooldowns.add_cooldown(ctx)
    if ctx.get_guild():
        await guild_cooldowns.add_cooldown(ctx)
    else:
        await dm_cooldowns.add_cooldown(ctx)


async def _run_sauce_command(ctx: lightbulb.Context, image_url: str):
    """
    Used to run both message commands and slash commands
    """
    log.info(f"Looking up image source/sauce: {image_url}", ctx.get_guild())

    # Attempt to find the source of this image
    try:
        sauce_result = await _get_sauce(ctx, image_url)
    except (pysaucenao.ShortLimitReachedException, pysaucenao.DailyLimitReachedException):
        return await ctx.respond(embeds.error(lang('Sauce', 'api_limit_exceeded')))

    except pysaucenao.InvalidOrWrongApiKeyException:
        log.warning(f"API key was rejected by SauceNao", ctx.get_guild())
        return await ctx.respond(embeds.error(lang('Sauce', 'rejected_api_key')))

    except pysaucenao.InvalidImageException:
        log.debug(f"An invalid image / image link was provided", ctx.get_guild())
        return await ctx.respond(embeds.error(lang('Sauce', 'no_images')))

    except pysaucenao.SauceNaoException:
        log.exception(f"An unknown error occurred while looking up this image", ctx.get_guild())
        return await ctx.respond(embeds.error(lang('Sauce', 'api_offline')))

    # If it's an anime, see if we can find a preview clip
    # TODO: Consider re-implementing support for video previews in the future
    # if isinstance(sauce, pysaucenao.AnimeSource):
    #     preview_file, nsfw = await self._video_preview(sauce, url, True)
    #     if preview_file:
    #         if nsfw and not ctx.channel.is_nsfw():
    #             log.info(f"Channel #{ctx.channel.name} is not NSFW; not uploading an NSFW video here")
    #         else:
    #             preview = discord.File(
    #                 BytesIO(preview_file),
    #                 filename=f"{sauce.title}_preview.mp4".lower().replace(' ', '_')
    #             )

    # We didn't find anything, provide some suggestions for manual investigation
    if not sauce_result:
        log.debug(f"No image sources found", ctx.get_guild())
        embed = embeds.error(lang('Sauce', 'not_found_advice'))
        embed.title = lang('Sauce', 'not_found', member=ctx.author)

        view = SauceResultsView(image_url)
        view.build_links(sauce_result)

        await ctx.respond(embed=embed, components=view)
        return

    if isinstance(sauce_result, pysaucenao.AnimeSource):
        await sauce_result.load_ids()

    view = SauceResultsView(image_url)
    view.build_links(sauce_result)

    await ctx.respond(
        embed=(await _build_sauce_embed(ctx, sauce_result)),
        components=view,
        flags=hikari.MessageFlag.NONE
    )


async def _multiple_images_prompt(ctx: lightbulb.MessageContext, image_attachments: t.List[hikari.Attachment]):
    """
    When there's multiple images available, prompt the user to pick one
    """
    if len(image_attachments) > 1:
        view = SelectTemplateView(image_attachments)
        view.build_select()
        embed = embeds.default(
            message=lang('Sauce', 'multiple_images'),
        )
        response = await ctx.respond(embed=embed, components=view)
        await view.start(response)
        await view.wait_for_input(60)
        view.select.disabled = True
        await response.edit(components=view)
        if not view.selected:
            return log.debug(f"No image selected, canceling", ctx.get_guild())

        attachment = view.selected
    else:
        attachment = image_attachments[0]

    image_url = _get_attachment_image(attachment)
    log.debug(f"Attachment selected: {image_url}", ctx.get_guild())
    return image_url


def _get_image_attachments(message: hikari.Message) -> t.Optional[t.List[t.Union[hikari.Attachment, hikari.Embed]]]:
    """
    Gets all image attachments associated with an image.
    """
    image_attachments = []
    for attachment in message.attachments:  # type: hikari.Attachment
        # Native images
        if _get_attachment_image(attachment):
            image_attachments.append(attachment)

    if message.embeds:
        for embed in message.embeds:
            if embed.url:
                image_attachments.append(embed)

    log.debug(f"Found {len(image_attachments)} image(s) in message {message.id}", message.guild_id)
    return image_attachments


def _get_attachment_image(attachment: t.Union[hikari.Attachment, hikari.Embed]) -> t.Optional[str]:
    """
    Gets the image associated with an attachment, including support for video attachments
    """
    if not attachment.url:
        return None

    # Discord attachments
    if isinstance(attachment, hikari.Attachment):
        # Extract a still frame from video uploads
        if str(attachment.url).endswith(('.mp4', '.webm', '.mov')):
            return attachment.proxy_url + '?format=jpeg'  # This trick only works with proxy_url, not the original url

        return attachment.url

    # Other image embeds
    if hasattr(attachment, 'image'):
        if attachment.image:
            return attachment.image.url

    if hasattr(attachment, 'thumbnail'):
        if attachment.thumbnail:
            return attachment.thumbnail.url


async def _get_sauce(ctx: lightbulb.Context, url: str) -> t.Optional[pysaucenao.GenericSource]:
    """
    Perform a SauceNao lookup on the supplied URL
    """
    # Increment the query counter for this guild
    await Servers.log_query(ctx.get_guild() or 0)  # "0" indicates DM queries

    # Check and see if we have this result cached first
    url_hash = hashlib.sha1(url.encode('utf-8')).hexdigest()
    if url_hash in sauce_cache:
        log.debug(f"Cache hit: {url}", ctx.get_guild())
        return sauce_cache[url_hash]

    # Get the API key for this server, or fallback to the default public key
    api_key = await Servers.get_api_key(ctx.get_guild()) if ctx.get_guild() else None
    api_key = api_key or config["saucenao"]["token"]

    # Initialize SauceNao and execute a search query
    saucenao = SauceNao(api_key=api_key,
                        min_similarity=float(config["saucenao"]["min_similarity"]),
                        priority=[21, 22, 5, 37, 25])
    search = await saucenao.from_url(url)
    _sauce = search.results[0] if search.results else None

    sauce_cache[url_hash] = _sauce
    return _sauce


async def _build_sauce_embed(ctx: lightbulb.Context, sauce_result: pysaucenao.GenericSource) -> hikari.Embed:
    """
    Builds a Discord embed for the provided SauceNao lookup
    """
    embed = embeds.base_embed()
    embed.title = sauce_result.title or sauce_result.author_name or "Untitled"
    embed.url = sauce_result.url
    embed.set_footer(text=lang('Sauce', 'match_title', {'index': sauce_result.index, 'similarity': sauce_result.similarity}),
                     icon="https://raw.githubusercontent.com/rainyDayDevs/discord-saucebot/master/assets/footer_icon.png")

    if sauce_result.author_name and sauce_result.title:
        embed.set_author(name=sauce_result.author_name, url=sauce_result.author_url)
    embed.set_image(sauce_result.thumbnail)

    if isinstance(sauce_result, pysaucenao.VideoSource):
        embed.add_field(name=lang('Sauce', 'episode'), value=codewrap(sauce_result.episode))
        embed.add_field(name=lang('Sauce', 'timestamp'), value=codewrap(sauce_result.timestamp))

    if isinstance(sauce_result, pysaucenao.AnimeSource):
        await _build_anime_embed(sauce_result, embed)

    if isinstance(sauce_result, pysaucenao.MangaSource):
        embed.add_field(name=lang('Sauce', 'chapter'), value=codewrap(sauce_result.chapter))

    if isinstance(sauce_result, pysaucenao.BooruSource):
        if sauce_result.characters:
            characters = [c.title() for c in sauce_result.characters]
            embed.add_field(name=lang('Sauce', 'characters'), value=codewrap(', '.join(characters)), inline=False)
        if sauce_result.material:
            material = [m.title() for m in sauce_result.material]
            embed.add_field(name=lang('Sauce', 'material'), value=codewrap(', '.join(material)), inline=False)

    return embed


async def _build_anime_embed(sauce_result: pysaucenao.AnimeSource, embed: hikari.Embed) -> hikari.Embed:
    """
    Build custom elements specific to anime embeds by pulling data from AniList
    """
    if sauce_result.anilist_url:
        embed.url = sauce_result.anilist_url

    async with anilist.AsyncClient() as anilist_client:
        anilist_sauce = await anilist_client.get(sauce_result.anilist_id)

    embed.set_image(anilist_sauce.cover.extra_large)

    description = str(anilist_sauce.description).replace("<br>", "\n")  # Replace breaks with newlines
    description = description.replace("<br/>", "\n")
    description = re.sub('<[^<]+?>', '', description)  # Strip HTML tags
    description = re.sub(r'\n{3,}', "\n\n", description)  # Reduce excessive newlines
    description = truncate(escape_markdown(description), 4096)
    embed.description = description

    if anilist_sauce.genres:
        embed.add_field(name=lang('Sauce', 'genres'), value=codewrap(', '.join(anilist_sauce.genres)), inline=False)

    if anilist_sauce.start_date:
        start_date = date(anilist_sauce.start_date.year, anilist_sauce.start_date.month, anilist_sauce.start_date.day)

        # Get the approximate season
        yday = start_date.timetuple().tm_yday
        spring = range(80, 172)
        summer = range(172, 264)
        fall = range(264, 355)

        if yday in spring:
            season = lang('Sauce', 'season_spring')
        elif yday in summer:
            season = lang('Sauce', 'season_summer')
        elif yday in fall:
            season = lang('Sauce', 'season_fall')
        else:
            season = lang('Sauce', 'season_winter')

        embed.add_field(name=lang('Sauce', 'aired'), value=codewrap(f"{season} {anilist_sauce.start_date.year}"), inline=False)

    if anilist_sauce.rankings:
        embed.add_field(name=lang('Sauce', 'rankings'), value=codewrap(anilist_sauce.rankings[0].rank), inline=True)
    if anilist_sauce.score:
        embed.add_field(name=lang('Sauce', 'rating'), value=codewrap(f"{anilist_sauce.score.average}%"), inline=True)

    return embed


def load(_bot: lightbulb.BotApp):
    _bot.add_plugin(sauce_plugin)


def unload(_bot: lightbulb.BotApp):
    _bot.remove_plugin(sauce_plugin)
