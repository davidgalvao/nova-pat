"""
Provider custom de embed para apresentações do Google Slides.

``docs.google.com/presentation/...`` não está entre os 80 providers oEmbed
nativos do Wagtail 8, então ``get_embed()`` levanta
``EmbedUnsupportedProviderException`` e a tag ``{% embed %}`` devolve string
vazia (caindo no fallback de link externo seguro).

Este finder reconhece URLs do navegador do tipo
    https://docs.google.com/presentation/d/<ID>/edit
    https://docs.google.com/presentation/d/<ID>/edit#slide=id.P1
    https://docs.google.com/presentation/d/<ID>/
e mapeia para a URL de incorporação
    https://docs.google.com/presentation/d/<ID>/embed

Não faz requisições de rede: a incorporação do Google Slides é um iframe
público cuja URL se deriva apenas do ID da apresentação.

Registrar em ``mysite/settings/base.py``::

    WAGTAILEMBEDS_FINDERS = [
        {"class": "core.embeds.GoogleSlidesFinder"},
        {"class": "wagtail.embeds.finders.oembed"},
    ]

O finder custom fica primeiro para capturar as URLs do Google Slides antes
de o finder oEmbed ser consultado; qualquer outra URL segue o fluxo nativo.
"""

import re

from django.utils.html import format_html

from wagtail.embeds.finders.base import EmbedFinder

# ID da apresentação no Google Slides: alfanumérico, hífen e sublinhado.
# Aparece no caminho da URL como /presentation/d/<ID>/...
_PRESENTATION_ID_RE = re.compile(r"/presentation/d/([a-zA-Z0-9_-]+)")

# Dimensões padrão do iframe quando o gestor não informa max_width/max_height.
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = int(DEFAULT_WIDTH * 9 / 16)  # 360, proporção 16:9


class GoogleSlidesFinder(EmbedFinder):
    """
    Finder de embed para o Google Slides.

    ``accept()`` reconhece apenas URLs de apresentação do Google Slides
    (``docs.google.com/presentation/d/<id>``). ``find_embed()`` devolve o
    dicionário de embed esperado por ``wagtail.embeds.embeds.get_embed``,
    com um ``<iframe>`` cujo ``src`` aponta para
    ``https://docs.google.com/presentation/d/<id>/embed``.

    Respeita ``max_width`` e ``max_height`` quando informados (ex.:
    ``{% embed url max_width=800 %}``), mantendo proporção 16:9 por padrão.
    """

    def accept(self, url):
        """Retorna True apenas para URLs de apresentação do Google Slides."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return bool(
            parsed.netloc.endswith("docs.google.com")
            and _PRESENTATION_ID_RE.search(parsed.path) is not None
        )

    def find_embed(self, url, max_width=None, max_height=None):
        """Retorna o dict de embed do Google Slides para a URL informada."""
        match = _PRESENTATION_ID_RE.search(url)
        if not match:
            # accept() já garante a presença do ID; este ramo é puramente
            # defensivo para nunca quebrar a renderização da página.
            return {
                "title": "",
                "author_name": "",
                "provider_name": "Google Slides",
                "type": "rich",
                "thumbnail_url": "",
                "width": 0,
                "height": 0,
                "html": "",
            }

        presentation_id = match.group(1)
        embed_url = f"https://docs.google.com/presentation/d/{presentation_id}/embed"

        width = int(max_width) if max_width else DEFAULT_WIDTH
        height = int(max_height) if max_height else int(width * 9 / 16)

        html = format_html(
            '<iframe src="{}" width="{width}" height="{height}" '
            'frameborder="0" allowfullscreen></iframe>',
            embed_url,
            width=width,
            height=height,
        )

        return {
            "title": "Apresentação Google Slides",
            "author_name": "",
            "provider_name": "Google Slides",
            "type": "rich",
            "thumbnail_url": "",
            "width": width,
            "height": height,
            "html": html,
        }
