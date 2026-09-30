"""
Testes da composição editorial de fallback da página de canal:
`CanalPage.get_effective_body()` e os blocos contextuais
`UltimoConteudoPlayerBlock` / `UltimosConteudosCarrosselBlock`.
"""

from django.test import TestCase

from wagtail.blocks.stream_block import StreamValue
from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import CategoriaConteudo, ConteudoPage, Licenca, Tipo
from curriculo.models import CurricularComponent
from usuarios.models import User, Role


class FallbackBlocksTestMixin:
    """Fixture reutilizável: canal, tipo, categoria, licença e autor."""

    @classmethod
    def setUpTestData(cls):
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.autor = User.objects.create_user(
            username="autor_fallback",
            email="autor_fallback@test.com",
            password="testpass123",
            role=Role.objects.get(slug="super-admin"),
        )
        cls.tipo = Tipo.objects.create(
            name="Tipo Fallback",
            slug="tipo-fallback",
            options={"formatos": []},
        )
        cls.licenca = Licenca.objects.create(
            name="Licença Fallback", slug="licenca-fallback"
        )
        cls.componente = CurricularComponent.objects.first()

        cls.canal = CanalPage(
            title="Canal Fallback",
            name="Canal Fallback",
            slug="canal-fallback",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Fallback",
            slug="categoria-fallback",
            canal=cls.canal,
        )

    def _criar_conteudo(self, canal, titulo, mecanismo, approved=True, live=True):
        content = ConteudoPage(
            title=titulo,
            slug=titulo.lower().replace(" ", "-"),
            canal=canal,
            autor=self.autor,
            tipo=self.tipo,
            category=self.categoria,
            license=self.licenca,
            mecanismo_exibicao=mecanismo,
            is_approved=approved,
        )
        canal.add_child(instance=content)
        revision = content.save_revision()
        if live:
            revision.publish()
        return content


class GetEffectiveBodyTestCase(FallbackBlocksTestMixin, TestCase):
    def test_retorna_body_quando_preenchido(self):
        """body preenchido pelo gestor tem precedência sobre o fallback."""
        body_json = [
            {"type": "hero", "value": {"titulo": "Hero manual"}},
        ]
        self.canal.body = body_json
        self.canal.save_revision().publish()

        effective = self.canal.get_effective_body()
        self.assertEqual(len(effective), 1)

    def test_retorna_fallback_quando_body_vazio(self):
        """body vazio gera StreamValue sintético com os 2 blocos padrão."""
        effective = self.canal.get_effective_body()
        self.assertIsInstance(effective, StreamValue)
        tipos = [b.block_type for b in effective]
        self.assertEqual(
            tipos, ["ultimo_conteudo_player", "ultimos_conteudos_carrossel"]
        )

    def test_fallback_e_streamvalue_valido_e_renderizavel(self):
        """O StreamValue sintético renderiza sem erro num canal sem conteúdo."""
        effective = self.canal.get_effective_body()
        html = ""
        for block in effective:
            html += block.render(context={"page": self.canal})
        self.assertIsInstance(html, str)


class UltimoConteudoPlayerBlockTestCase(FallbackBlocksTestMixin, TestCase):
    def _block(self):
        from core.blocks import UltimoConteudoPlayerBlock

        return UltimoConteudoPlayerBlock()

    def test_retorna_ultimo_conteudo_do_canal(self):
        """get_context retorna o conteúdo mais recente aprovado e publicado."""
        self._criar_conteudo(self.canal, "Antigo", ConteudoPage.MECANISMO_AUDIO)
        recente = self._criar_conteudo(
            self.canal, "Recente", ConteudoPage.MECANISMO_VIDEO
        )
        context = self._block().get_context({}, parent_context={"page": self.canal})
        self.assertEqual(context["conteudo"].pk, recente.pk)

    def test_retorna_none_fora_de_canal(self):
        """Sem parent_context (fora de CanalPage), conteudo é None e não quebra."""
        self._criar_conteudo(self.canal, "Existente", ConteudoPage.MECANISMO_VIDEO)
        context = self._block().get_context({}, parent_context=None)
        self.assertIsNone(context["conteudo"])

    def test_canal_sem_conteudo_retorna_none(self):
        context = self._block().get_context({}, parent_context={"page": self.canal})
        self.assertIsNone(context["conteudo"])

    def test_ignora_conteudo_nao_aprovado(self):
        self._criar_conteudo(
            self.canal, "Pendente", ConteudoPage.MECANISMO_VIDEO, approved=False
        )
        context = self._block().get_context({}, parent_context={"page": self.canal})
        self.assertIsNone(context["conteudo"])

    def test_render_com_conteudo_sem_og_image_nao_quebra(self):
        """Edge case: conteúdo sem og_image renderiza hero sem imagem de fundo."""
        self._criar_conteudo(self.canal, "Sem Capa", ConteudoPage.MECANISMO_VIDEO)
        block = self._block()
        context = block.get_context({}, parent_context={"page": self.canal})
        html = block.render({}, context=context)
        self.assertIn("Sem Capa", html)
        self.assertNotIn("hero_img", html)

    def test_render_mecanismo_desconhecido_nao_quebra(self):
        """Edge case: mecanismo sem player (apresentacao) renderiza só o CTA."""
        self._criar_conteudo(
            self.canal, "Apresentação X", ConteudoPage.MECANISMO_APRESENTACAO
        )
        block = self._block()
        context = block.get_context({}, parent_context={"page": self.canal})
        html = block.render({}, context=context)
        self.assertIn("Apresentação X", html)
        self.assertNotIn("<video", html)
        self.assertNotIn("<audio", html)

    def test_render_sem_dados_nao_quebra(self):
        """Bloco vazio (sem conteúdo no canal) renderiza string vazia."""
        block = self._block()
        html = block.render({}, context={"page": self.canal})
        self.assertEqual(html.strip(), "")


class UltimosConteudosCarrosselBlockTestCase(FallbackBlocksTestMixin, TestCase):
    def _block(self):
        from core.blocks import UltimosConteudosCarrosselBlock

        return UltimosConteudosCarrosselBlock()

    def test_busca_ultimos_9_e_agrupa_em_paginas_de_3(self):
        """12 conteúdos → carrossel limita a 9 e agrupa em 3 páginas de 3."""
        for i in range(12):
            self._criar_conteudo(
                self.canal, f"Conteudo {i:02}", ConteudoPage.MECANISMO_VIDEO
            )
        context = self._block().get_context({}, parent_context={"page": self.canal})
        paginas = context["paginas"]
        self.assertEqual(len(paginas), 3)
        self.assertTrue(all(len(pagina) == 3 for pagina in paginas))

    def test_pagina_parcial_quando_menos_de_multiplo_de_3(self):
        """4 conteúdos → 2 páginas (3 + 1)."""
        for i in range(4):
            self._criar_conteudo(
                self.canal, f"Conteudo {i}", ConteudoPage.MECANISMO_LINK_EXTERNO
            )
        context = self._block().get_context({}, parent_context={"page": self.canal})
        paginas = context["paginas"]
        self.assertEqual(len(paginas), 2)
        self.assertEqual([len(p) for p in paginas], [3, 1])

    def test_canal_sem_conteudos_retorna_lista_vazia(self):
        context = self._block().get_context({}, parent_context={"page": self.canal})
        self.assertEqual(context["paginas"], [])

    def test_retorna_vazio_fora_de_canal(self):
        self._criar_conteudo(self.canal, "Existente", ConteudoPage.MECANISMO_VIDEO)
        context = self._block().get_context({}, parent_context=None)
        self.assertEqual(context["paginas"], [])

    def test_render_com_dados_nao_quebra(self):
        self._criar_conteudo(self.canal, "Visível", ConteudoPage.MECANISMO_AUDIO)
        block = self._block()
        context = block.get_context({}, parent_context={"page": self.canal})
        html = block.render({}, context=context)
        self.assertIn("Visível", html)

    def test_render_sem_dados_nao_quebra(self):
        """Carrossel vazio não renderiza a section (guarda {% if paginas %})."""
        block = self._block()
        html = block.render({}, context={"page": self.canal})
        self.assertNotIn("<section", html)
