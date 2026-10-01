"""
Testes de embed oEmbed nos templates de página de conteúdo:
``conteudo_page_animacao_externa.html`` e ``conteudo_page_link_externo.html``.

A "URL colada pelo gestor" é resolvida pela tag ``{% embed %}`` (oEmbed),
nunca por ``<iframe src="{{ page.source }}">``. Quando a resolução funciona, o
HTML do provider (com ``<iframe>``) aparece; quando falha (``EmbedException``),
o template cai no link de fallback seguro (``rel="noopener noreferrer"``).

A tag chama ``wagtail.embeds.embeds.get_embed`` e captura ``EmbedException``.
Todos os testes mockam essa função — nenhum toca a rede.
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import TestCase

from wagtail.embeds.exceptions import EmbedException
from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import CategoriaConteudo, ConteudoPage, Licenca, Tipo
from usuarios.models import Role, User


YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
EMBED_HTML = (
    '<iframe width="480" height="270" '
    'src="https://www.youtube.com/embed/dQw4w9WgXcQ" '
    'frameborder="0" allowfullscreen></iframe>'
)

# Ponto exato usado pela tag {% embed %}: wagtail.embeds.embeds.get_embed
GET_EMBED_PATH = "wagtail.embeds.embeds.get_embed"


class EmbedTemplatesFixtureMixin:
    """Fixture reutilizável: canal, tipo, categoria, licença e autor."""

    @classmethod
    def setUpTestData(cls):
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.autor = User.objects.create_user(
            username="autor_embed_page",
            email="autor_embed_page@test.com",
            password="testpass123",
            role=Role.objects.get(slug="super-admin"),
        )
        cls.tipo = Tipo.objects.create(
            name="Tipo Embed Page",
            slug="tipo-embed-page",
            options={"formatos": []},
        )
        cls.licenca = Licenca.objects.create(
            name="Licença Embed Page", slug="licenca-embed-page"
        )

        cls.canal = CanalPage(
            title="Canal Embed Page",
            name="Canal Embed Page",
            slug="canal-embed-page",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Embed Page",
            slug="categoria-embed-page",
            canal=cls.canal,
        )

    def _criar_conteudo(self, mecanismo, source="", titulo="Conteúdo Embed Page"):
        conteudo = ConteudoPage(
            title=titulo,
            slug=titulo.lower().replace(" ", "-"),
            canal=self.canal,
            autor=self.autor,
            tipo=self.tipo,
            category=self.categoria,
            license=self.licenca,
            mecanismo_exibicao=mecanismo,
            source=source,
            is_approved=True,
        )
        self.canal.add_child(instance=conteudo)
        conteudo.save_revision().publish()
        return conteudo

    def _render_template(self, mecanismo, source, titulo=None):
        conteudo = self._criar_conteudo(
            mecanismo,
            source=source,
            titulo=titulo or f"Conteúdo Embed {mecanismo}",
        )
        template = f"conteudos/conteudo_page_{mecanismo}.html"
        return render_to_string(template, {"page": conteudo})


class AnimacaoExternaTemplateEmbedTestCase(EmbedTemplatesFixtureMixin, TestCase):
    def test_com_embed_renderiza_iframe(self):
        with patch(
            GET_EMBED_PATH, return_value=SimpleNamespace(html=EMBED_HTML)
        ) as mocked:
            html = self._render_template(
                ConteudoPage.MECANISMO_ANIMACAO_EXTERNA, YOUTUBE_URL
            )

        self.assertIn("<iframe", html)
        self.assertIn("youtube.com/embed/", html)
        mocked.assert_called_once_with(YOUTUBE_URL, max_width=None)

    def test_sem_embed_renderiza_fallback_com_link_seguro(self):
        with patch(GET_EMBED_PATH, side_effect=EmbedException("não embedável")):
            html = self._render_template(
                ConteudoPage.MECANISMO_ANIMACAO_EXTERNA, YOUTUBE_URL
            )

        self.assertNotIn("<iframe", html)
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn(YOUTUBE_URL, html)
        self.assertIn("não oferece incorporação direta", html)


class LinkExternoTemplateEmbedTestCase(EmbedTemplatesFixtureMixin, TestCase):
    def test_com_embed_renderiza_iframe(self):
        with patch(
            GET_EMBED_PATH, return_value=SimpleNamespace(html=EMBED_HTML)
        ) as mocked:
            html = self._render_template(
                ConteudoPage.MECANISMO_LINK_EXTERNO, YOUTUBE_URL
            )

        self.assertIn("<iframe", html)
        self.assertIn("youtube.com/embed/", html)
        mocked.assert_called_once_with(YOUTUBE_URL, max_width=None)

    def test_sem_embed_renderiza_fallback_com_link_seguro(self):
        with patch(GET_EMBED_PATH, side_effect=EmbedException("não embedável")):
            html = self._render_template(
                ConteudoPage.MECANISMO_LINK_EXTERNO, YOUTUBE_URL
            )

        self.assertNotIn("<iframe", html)
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn(YOUTUBE_URL, html)


class SourceVazioTemplateEmbedTestCase(EmbedTemplatesFixtureMixin, TestCase):
    def test_source_vazio_nao_renderiza_iframe_e_nao_levanta(self):
        """source="": o guard ``{% if page.source %}`` evita até a chamada oEmbed."""
        with patch(
            GET_EMBED_PATH, side_effect=EmbedException("URL vazia")
        ) as mocked:
            for mecanismo in (
                ConteudoPage.MECANISMO_ANIMACAO_EXTERNA,
                ConteudoPage.MECANISMO_LINK_EXTERNO,
            ):
                with self.subTest(mecanismo=mecanismo):
                    html = self._render_template(mecanismo, "")
                    self.assertNotIn("<iframe", html)

        mocked.assert_not_called()
