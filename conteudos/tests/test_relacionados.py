"""
Testes de template para o bloco de conteúdos relacionados (NOVAPAT-44).

Cobre os dois casos de aceitação:
- com relacionados: exibe conteúdos da mesma CategoriaConteudo e/ou com tags
  em comum, publicados (live()) e aprovados (is_approved=True), limitados;
- sem relacionados: exibe mensagem de vazio.

Também exercita a inclusion_tag ``conteudos_relacionados`` (ordenação por
mesma categoria e quantidade de tags em comum, nunca por media_avaliacao /
total_avaliacoes).
"""

from django.template.loader import render_to_string
from django.test import TestCase

from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import CategoriaConteudo, ConteudoPage, Tipo
from conteudos.templatetags.conteudos_tags import conteudos_relacionados
from usuarios.models import Role, User


class RelacionadosTemplateTestCase(TestCase):
    """Testes de renderização e lógica do bloco de relacionados."""

    @classmethod
    def setUpTestData(cls):
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.autor = User.objects.create_user(
            username="autor_relacionados",
            email="autor_relacionados@test.com",
            password="testpass123",
            role=Role.objects.get(slug="super-admin"),
        )
        cls.tipo = Tipo.objects.create(
            name="Tipo Relacionados",
            slug="tipo-relacionados",
            options={"formatos": [".mp4"]},
        )
        cls.canal = CanalPage(
            title="Canal Relacionados",
            name="Canal Relacionados",
            slug="canal-relacionados",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Relacionados",
            slug="categoria-relacionados",
            canal=cls.canal,
        )

        cls.outra_categoria = CategoriaConteudo.objects.create(
            name="Outra Categoria",
            slug="outra-categoria",
            canal=cls.canal,
        )

    def _criar_conteudo(
        self,
        titulo,
        categoria=None,
        tags=None,
        mecanismo=ConteudoPage.MECANISMO_LINK_EXTERNO,
        source="https://exemplo.com",
        is_approved=True,
        live=True,
    ):
        conteudo = ConteudoPage(
            title=titulo,
            slug=titulo.lower().replace(" ", "-"),
            canal=self.canal,
            autor=self.autor,
            tipo=self.tipo,
            category=categoria or self.categoria,
            mecanismo_exibicao=mecanismo,
            source=source,
            is_approved=is_approved,
        )
        self.canal.add_child(instance=conteudo)
        conteudo.save_revision()
        if live:
            conteudo.save_revision().publish()
        if tags:
            conteudo.tags.add(*tags)
        return conteudo

    def _tag(self, page=None, limit=5):
        return conteudos_relacionados(None, page=page, limit=limit)

    def _render(self, relacionados, limit=5):
        return render_to_string(
            "conteudos/includes/relacionados.html",
            {"relacionados": relacionados, "limit": limit},
        )

    def test_com_relacionados_exibe_conteudos_reais(self):
        atual = self._criar_conteudo("Conteúdo atual", tags=["a", "b"])
        r1 = self._criar_conteudo("Relacionado 1", tags=["a"])
        r2 = self._criar_conteudo("Relacionado 2", tags=["b"])
        self._criar_conteudo("Não relacionado", tags=["z"])

        contexto = self._tag(page=atual)
        titulos = [c.title for c in contexto["relacionados"]]

        self.assertIn("Relacionado 1", titulos)
        self.assertIn("Relacionado 2", titulos)
        self.assertNotIn("Conteúdo atual", titulos)
        self.assertNotIn("Não relacionado", titulos)
        self.assertEqual(contexto["limit"], 5)

        html = self._render(contexto["relacionados"])
        self.assertIn("Conteúdos relacionados", html)
        self.assertIn("Relacionado 1", html)
        self.assertIn("Relacionado 2", html)

    def test_sem_relacionados_exibe_mensagem_vazio(self):
        atual = self._criar_conteudo("Conteúdo atual", tags=["a"])
        # Apenas conteúdos sem categoria em comum e sem tags em comum.
        self._criar_conteudo("Outro", categoria=self.outra_categoria, tags=["z"])

        contexto = self._tag(page=atual)
        self.assertEqual(list(contexto["relacionados"]), [])

        html = self._render([])
        self.assertIn("Conteúdos relacionados", html)
        self.assertIn("Não há conteúdos relacionados no momento.", html)

    def test_exclui_nao_aprovados_e_nao_publicados(self):
        atual = self._criar_conteudo("Conteúdo atual", tags=["a"])
        self._criar_conteudo("Não aprovado", tags=["a"], is_approved=False)
        nao_publicado = self._criar_conteudo("Não publicado", tags=["a"], live=False)
        # Despublica explicitamente (public() foi chamado em _criar_conteudo)
        nao_publicado.unpublish()

        contexto = self._tag(page=atual)
        titulos = [c.title for c in contexto["relacionados"]]
        self.assertNotIn("Não aprovado", titulos)
        self.assertNotIn("Não publicado", titulos)

    def test_limite_respeitado(self):
        atual = self._criar_conteudo("Conteúdo atual", tags=["a"])
        for i in range(7):
            self._criar_conteudo(f"Relacionado {i}", tags=["a"])

        contexto = self._tag(page=atual, limit=3)
        self.assertEqual(len(contexto["relacionados"]), 3)

    def test_prioriza_mesma_categoria_e_tags_em_comum(self):
        atual = self._criar_conteudo("Conteúdo atual", tags=["comum", "extra"])
        # mesma categoria + 2 tags em comum -> deve vir primeiro
        mais_relevante = self._criar_conteudo("Mais relevante", tags=["comum", "extra", "adicional"])
        # mesma categoria + 1 tag em comum
        menos_relevante = self._criar_conteudo("Menos relevante", tags=["comum"])
        # outra categoria, mesma tag
        outra_cat = self._criar_conteudo(
            "Outra categoria", categoria=self.outra_categoria, tags=["comum"]
        )

        contexto = self._tag(page=atual)
        titulos = [c.title for c in contexto["relacionados"]]

        self.assertEqual(titulos[0], "Mais relevante")
        self.assertEqual(titulos[1], "Menos relevante")
        self.assertEqual(titulos[2], "Outra categoria")
