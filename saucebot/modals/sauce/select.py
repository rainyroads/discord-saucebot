import typing as t
from urllib.parse import urlparse, unquote

import hikari
import miru

from saucebot.components import log
from saucebot.components.helpers import truncate, make_utf8_safe
from saucebot.lang.lang import lang

__all__ = ['SelectTemplateView']


class SelectTemplateView(miru.View):

    def __init__(self, items: t.List[t.Union[hikari.Attachment, hikari.Embed]]):
        self.items      = items
        self.select     = None  # type: t.Optional[miru.TextSelect]
        self.selected   = None  # type: t.Optional[t.Union[hikari.Attachment, hikari.Embed]]

        super().__init__()

    def build_select(self) -> None:
        """
        Select a warning template to use
        """
        index = 0
        options = []
        for item in self.items:

            parsed_url = urlparse(item.url)
            path = unquote(parsed_url.path)  # Decode URL-encoded characters
            filename = path.split('/')[-1]  # Extract the last part of the path as the filename
            filename = filename.split('?')[0]  # Remove any query string parameters

            filetype = "Video" if filename.endswith((".mp4", ".webm", ".mov")) else "Image"

            options.append(
                miru.SelectOption(
                    label=f"{filetype} #{index + 1}",
                    value=str(index),
                    description=truncate(make_utf8_safe(filename), 50)
                )
            )

            index += 1

        select = miru.TextSelect(
            placeholder=lang('Sauce', 'multiple_placeholder'),
            options=options
        )
        select.callback = self.select_callback

        self.add_item(select)
        self.select = select

    async def select_callback(self, ctx: miru.ViewContext) -> None:
        log.debug(f"Image {self.select.values[0]} selected for searching", ctx.get_guild())
        self.selected = self.items[int(self.select.values[0])]
