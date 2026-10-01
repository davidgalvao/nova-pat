"""
Testes de embed oEmbed no hero do canal
(``core/templates/blocks/ultimo_conteudo_player.html``).

Garantia central: a "URL colada pelo gestor" (mecanismos ``link_externo`` e
``animacao_externa``) é resolvida no template pela tag ``{% embed %}`` do
``wagtail.embeds`` — nunca injetada direto em ``<iframe src>``. Quando a
resolução oEmbed funciona, o HTML do provider (contendo ``<iframe>``) aparece;
quando ela falha (``EmbedException``), nada de ``<iframe>`` é renderizado e o
hero segue editorial (texto + CTA).

A tag ``{% embed %}`` chama ``wagtail.embeds.embeds.get_embed`` internamente e
captura ``EmbedException`` devolvendo string vazia. Por isso todos os testes
abaixo substituem ``wagtail.embeds.embeds.get_embed``: nenhum toca a rede.
"""

from types import SimpleNamespace
from unittest.mock import patch

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


class EmbedBlocksFixtureMixin:
    """Fixture reutilizável: canal, tipo, categoria, licença e autor."""

    @classmethod
    def setUpTestData(cls):
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.autor = User.objects.create_user(
            username="autor_embed_player",
            email="autor_embed_player@test.com",
            password="testpass123",
            role=Role.objects.get(slug="super-admin"),
        )
        cls.tipo = Tipo.objects.create(
            name="Tipo Embed Player",
            slug="tipo-embed-player",
            options={"formatos": []},
        )
        cls.licenca = Licenca.objects.create(
            name="Licença Embed Player", slug="licenca-embed-player"
        )

        cls.canal = CanalPage(
            title="Canal Embed Player",
            name="Canal Embed Player",
            slug="canal-embed-player",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Embed Player",
            slug="categoria-embed-player",
            canal=cls.canal,
        )

    def _criar_conteudo(self, mecanismo, source="", titulo="Conteúdo Embed Player"):
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

    def _render_hero(self):
        """Renderiza o bloco do hero exatamente como os testes existentes."""
        from core.blocks import UltimoConteudoPlayerBlock

        block = UltimoConteudoPlayerBlock()
        context = block.get_context({}, parent_context={"page": self.canal})
        return block.render({}, context=context)


class UltimoConteudoPlayerEmbedTestCase(EmbedBlocksFixtureMixin, TestCase):
    def test_link_externo_resolve_url_do_gestor_em_iframe(self):
        """URL do gestor -> oEmbed -> HTML com <iframe> no hero."""
        self._criar_conteudo(
            ConteudoPage.MECANISMO_LINK_EXTERNO, source=YOUTUBE_URL
        )
        with patch(
            GET_EMBED_PATH, return_value=SimpleNamespace(html=EMBED_HTML)
        ) as mocked:
            html = self._render_hero()

        self.assertIn("<iframe", html)
        self.assertIn("youtube.com/embed/", html)
        # A URL resolvida é exatamente a colada pelo gestor (não o iframe cru).
        mocked.assert_called_once_with(YOUTUBE_URL, max_width=None)

    def test_animacao_externa_resolve_url_do_gestor_em_iframe(self):
        """O ramo animacao_externa usa o mesmo caminho oEmbed."""
        self._criar_conteudo(
            ConteudoPage.MECANISMO_ANIMACAO_EXTERNA,
            source=YOUTUBE_URL,
            titulo="Animação Embed Player",
        )
        with patch(
            GET_EMBED_PATH, return_value=SimpleNamespace(html=EMBED_HTML)
        ):
            html = self._render_hero()

        self.assertIn("<iframe", html)
        self.assertIn("youtube.com/embed/", html)

    def test_embed_indisponivel_nao_renderiza_iframe(self):
        """EmbedException (URL não-embeddável) não vaza <iframe> no hero."""
        self._criar_conteudo(
            ConteudoPage.MECANISMO_LINK_EXTERNO, source=YOUTUBE_URL
        )
        with patch(GET_EMBED_PATH, side_effect=EmbedException("não embedável")):
            html = self._render_hero()

        self.assertNotIn("<iframe", html)
        # O hero não some: continua com o bloco editorial e o CTA.
        self.assertIn("Conteúdo Embed Player", html)

    def test_source_vazio_nao_renderiza_iframe_e_nao_levanta(self):
        """source="" não deve gerar iframe nem exceção."""
        self._criar_conteudo(ConteudoPage.MECANISMO_LINK_EXTERNO, source="")
        with patch(GET_EMBED_PATH, side_effect=EmbedException("URL vazia")):
            html = self._render_hero()

        self.assertNotIn("<iframe", html)
        self.assertIn("Conteúdo Embed Player", html)
