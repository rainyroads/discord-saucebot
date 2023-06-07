import typing as t
from urllib.parse import quote_plus

import miru
import pysaucenao

from saucebot.lang.lang import lang

__all__ = ['SauceResultsView']


class SauceResultsView(miru.View):
    """
    A view that adds button links to a sauce result response message
    """

    def __init__(self, image_url: str):
        self.image_url = image_url
        super().__init__()

    def build_links(self, sauce: t.Optional[pysaucenao.GenericSource]):
        if not sauce:
            google_url = f"https://lens.google.com/uploadbyurl?url={quote_plus(self.image_url)}&safe=off"
            ascii_url = f"https://ascii2d.net/search/url/{quote_plus(self.image_url)}"
            yandex_url = f"https://yandex.com/images/search?url={quote_plus(self.image_url)}&rpt=imageview"

            urls = [
                (lang('Sauce', 'google'), google_url),
                (lang('Sauce', 'ascii2d'), ascii_url),
                (lang('Sauce', 'yandex'), yandex_url)
            ]

            for label, url in urls:
                self.add_item(miru.Button(label=label, url=url))
            return

        if isinstance(sauce, pysaucenao.AnimeSource):
            urls = []

            if sauce.anilist_url:
                urls.append((lang('Sauce', 'anilist'), sauce.anilist_url))

            if sauce.mal_url:
                urls.append((lang('Sauce', 'mal'), sauce.mal_url))

            if sauce.anidb_url:
                urls.append((lang('Sauce', 'anidb'), sauce.anidb_url))

            for label, url in urls:
                self.add_item(miru.Button(label=label, url=url))
        else:
            self.add_item(miru.Button(label=sauce.index or "Unknown Source", url=sauce.url))
