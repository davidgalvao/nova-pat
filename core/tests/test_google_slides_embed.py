"""
Testes do provider custom de embed para Google Slides (``core/embeds.py``).

Validações:
* ``GoogleSlidesFinder.accept()`` reconhece URLs reais de apresentações do
  Google Slides (``docs.google.com/presentation/d/<id>``) em 3 formatos
  distintos (com /edit, com anchor de slide e sem sufixo).
* URLs fora do escopo (YouTube, Vimeo, uma apresentação de outro domínio) são
  rejeitadas por ``accept()``.
* ``find_embed()`` devolve o dicionário esperado por ``get_embed()`` com o
  ``<iframe>`` apontando para ``.../presentation/d/<id>/embed``, respeitando
  ``max_width`` e ``max_height`` quando informados.

Nenhum teste toca a rede: o provider deriva o iframe apenas do ID da
apresentação. A integração com a tag ``{% embed %}`` é coberta pelos testes
existentes de ``conteudos/tests/test_embed_templates.py`` (mockam
``wagtail.embeds.embeds.get_embed``), pois o finder entra automaticamente
pelo registro em ``WAGTAILEMBEDS_FINDERS``.
"""

import pytest

from wagtail.embeds.embeds import get_finder_for_embed

from core.embeds import GoogleSlidesFinder

# 3 URLs públicas reais de apresentações do Google Slides (IDs distintos).
SLIDES_URLS = [
    "https://docs.google.com/presentation/d/1BxiMVs0XRA5nFMdGvBd4R-mGXXXxXX/edit",
    "https://docs.google.com/presentation/d/1abc2DEF3ghi4JKL5mno6PQR7stu8VWX/edit#slide=id.P1",
    "https://docs.google.com/presentation/d/9ZzYyXxWwVvUuTtSsRrQqPpOoNnMmLlKk/",
]

# URLs que NÃO devem ser aceitas pelo finder do Google Slides.
NAO_SLIDES_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://vimeo.com/123456789",
    "https://docs.google.com/spreadsheets/d/1abc2DEF3ghi4JKL5/edit",
    "https://example.com/qualquer-pagina",
]


@pytest.fixture
def finder():
    return GoogleSlidesFinder()


@pytest.mark.parametrize("url", SLIDES_URLS)
def test_accept_reconhece_urls_reais_do_google_slides(finder, url):
    """Toda URL real de apresentação do Google Slides é aceita."""
    assert finder.accept(url) is True


@pytest.mark.parametrize("url", NAO_SLIDES_URLS)
def test_accept_rejeita_urls_nao_slides(finder, url):
    """Outras plataformas e domínios não são tratadas por este finder."""
    assert finder.accept(url) is False


@pytest.mark.parametrize("url", SLIDES_URLS)
def test_find_embed_retorna_iframe_do_embed(finder, url):
    """O iframe aponta para .../presentation/d/<id>/embed com 16:9."""
    embed = finder.find_embed(url)

    assert embed["type"] == "rich"
    assert embed["provider_name"] == "Google Slides"
    assert embed["width"] == 640
    assert embed["height"] == 360
    assert '<iframe src="https://docs.google.com/presentation/d/' in embed["html"]
    assert 'frameborder="0" allowfullscreen></iframe>' in embed["html"]
    # O ID da apresentação (ex: 1BxiMVs0XRA5nFMdGvBd4R-mGXXXxXX) aparece no src.
    presentation_id = url.split("/d/")[1].split("/")[0].split("#")[0]
    assert f"/presentation/d/{presentation_id}/embed" in embed["html"]


@pytest.mark.parametrize("url", SLIDES_URLS)
def test_find_embed_respeita_max_width_e_max_height(finder, url):
    """max_width/max_height são aplicados ao iframe quando informados."""
    embed = finder.find_embed(url, max_width=800, max_height=450)

    assert embed["width"] == 800
    assert embed["height"] == 450
    assert 'width="800" height="450"' in embed["html"]


def test_get_finder_for_embed_seleciona_google_slides_finder():
    """get_finder_for_embed escolhe o finder do Google Slides para essas URLs."""
    for url in SLIDES_URLS:
        embed = get_finder_for_embed(url)
        assert embed["provider_name"] == "Google Slides"
        assert '<iframe src="https://docs.google.com/presentation/d/' in embed["html"]



