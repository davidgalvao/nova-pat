"""
Testes para views do app search.
"""
from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock

from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import ConteudoPage, Tipo, CategoriaConteudo, Licenca
from aplicativos.models import AplicativoCategory, AplicativoEducacionalPage
from usuarios.models import User, Role
from curriculo.models import CurricularComponent, CurricularComponentCategory, NivelEnsino


class SearchViewTestCase(TestCase):
    """Testes para a view de busca."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        cls.factory = RequestFactory()

        # Roles já existem via migration 0003_create_default_roles
        cls.role_editor = Role.objects.get(slug="editor")
        cls.role_convidado = Role.objects.get(slug="convidado")

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar canal para conteúdos
        cls.canal = CanalPage(
            title="Canal Teste",
            name="Canal Teste",
            slug="canal-teste-search",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        # Criar tipo de conteúdo
        cls.tipo = Tipo.objects.create(
            name="Vídeo",
            slug="video-search",
            options={"formatos": ["mp4", "webm"]},
            is_active=True,
            ordem=1,
        )

        # Criar categoria para o canal
        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Teste",
            slug="categoria-teste-search",
            canal=cls.canal,
            ordem=1,
            is_active=True,
        )

        # Criar licença
        cls.licenca = Licenca.objects.create(
            name="CC BY",
            slug="cc-by-search",
            description="Creative Commons Attribution",
            is_active=True,
            ordem=1,
        )

        # Criar nível de ensino
        cls.nivel = NivelEnsino.objects.create(
            name="Ensino Médio",
            slug="ensino-medio-search",
            ordem=1,
            is_active=True,
        )

        # Criar categoria de componente curricular
        cls.comp_category = CurricularComponentCategory.objects.create(
            name="Ciências da Natureza",
            slug="ciencias-natureza-search",
            ordem=1,
            is_active=True,
        )

        # Criar componente curricular
        cls.componente = CurricularComponent.objects.create(
            name="Biologia",
            slug="biologia-search",
            nivel=cls.nivel,
            category=cls.comp_category,
            ordem=1,
            is_active=True,
        )

        # Criar usuário editor
        cls.editor = User.objects.create_user(
            username="editor_search",
            email="editor_search@test.com",
            password="testpass123",
            role=cls.role_editor,
        )

        # Criar ConteudoPage
        cls.conteudo = ConteudoPage(
            title="Conteúdo Teste Busca",
            tipo=cls.tipo,
            category=cls.categoria,
            license=cls.licenca,
            arquivo="conteudos/teste.mp4",
            autor=cls.editor,
            canal=cls.canal,
        )
        cls.canal.add_child(instance=cls.conteudo)
        cls.conteudo.componentes_curriculares.add(cls.componente)
        cls.conteudo.save_revision().publish()

        # Criar canal fixo para aplicativos
        cls.canal_apps = CanalPage(
            title="Aplicativos Educacionais",
            name="Aplicativos Educacionais",
            slug="aplicativos-educacionais",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal_apps)
        cls.canal_apps.save_revision().publish()

        # Criar categoria de aplicativo
        cls.categoria_app = AplicativoCategory.objects.create(
            name="Ferramentas",
            slug="ferramentas-search",
            ordem=1,
            is_active=True,
        )

        # Criar AplicativoEducacionalPage
        with patch('requests.head') as mock_head, patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "192.168.1.1"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            cls.aplicativo = AplicativoEducacionalPage(
                title="App Teste Busca",
                category=cls.categoria_app,
                url="https://app.exemplo.com",
                description="A" * 140,
                autor=cls.editor,
            )
            cls.canal_apps.add_child(instance=cls.aplicativo)
            cls.aplicativo.tags.add("tag1", "tag2", "tag3")
            cls.aplicativo.save_revision().publish()

    def test_search_view_accessible(self):
        """Testa que a view de busca é acessível."""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search/search.html")

    def test_search_view_with_query(self):
        """Testa busca com query textual."""
        response = self.client.get(reverse("search"), {"query": "Teste"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("search_results", response.context)
        self.assertEqual(response.context["search_query"], "Teste")

    def test_search_view_filter_by_canal(self):
        """Testa filtro por canal (RF001)."""
        response = self.client.get(reverse("search"), {"canal": self.canal.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        # Com apenas canal, deve buscar em ambos os tipos (filterset é None)
        self.assertIsNone(response.context.get("filterset"))

    def test_search_view_filter_by_tipo_infers_conteudo(self):
        """Testa que preencher 'tipo' infere busca apenas em ConteudoPage."""
        response = self.client.get(reverse("search"), {"tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        # Deve usar ConteudoSearchFilterSet
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)
        # Deve encontrar o conteúdo
        self.assertContains(response, "Conteúdo Teste Busca")
        # Não deve encontrar o aplicativo
        self.assertNotContains(response, "App Teste Busca")

    def test_search_view_filter_by_licenca_infers_conteudo(self):
        """Testa que preencher 'licenca' infere busca apenas em ConteudoPage."""
        response = self.client.get(reverse("search"), {"licenca": self.licenca.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)
        self.assertContains(response, "Conteúdo Teste Busca")
        self.assertNotContains(response, "App Teste Busca")

    def test_search_view_filter_by_componente_infers_conteudo(self):
        """Testa que preencher 'componente' infere busca apenas em ConteudoPage."""
        response = self.client.get(reverse("search"), {"componente": self.componente.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)
        self.assertContains(response, "Conteúdo Teste Busca")
        self.assertNotContains(response, "App Teste Busca")

    def test_search_view_filter_by_categoria_conteudo_infers_conteudo(self):
        """Testa que selecionar categoria de conteúdo infere ConteudoPage."""
        response = self.client.get(reverse("search"), {"categoria_conteudo": self.categoria.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)
        self.assertContains(response, "Conteúdo Teste Busca")
        self.assertNotContains(response, "App Teste Busca")

    def test_search_view_filter_by_categoria_aplicativo_infers_aplicativo(self):
        """Testa que selecionar categoria de aplicativo infere AplicativoEducacionalPage."""
        response = self.client.get(reverse("search"), {"categoria_aplicativo": self.categoria_app.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import AplicativoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], AplicativoSearchFilterSet)
        self.assertContains(response, "App Teste Busca")
        self.assertNotContains(response, "Conteúdo Teste Busca")

    def test_search_view_query_and_canal_only_searches_both(self):
        """Testa que apenas query e/ou canal busca nos dois tipos (sem filterset)."""
        response = self.client.get(reverse("search"), {"query": "Teste", "canal": self.canal.id})
        self.assertEqual(response.status_code, 200)
        # Para 'ambos', não há filterset (usa busca unificada)
        self.assertIsNone(response.context.get("filterset"))
        # Deve encontrar o conteúdo (que está no canal)
        self.assertContains(response, "Conteúdo Teste Busca")

    def test_search_view_pagination(self):
        """Testa paginação dos resultados."""
        response = self.client.get(reverse("search"), {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("search_results", response.context)
        self.assertTrue(response.context["search_results"].has_next() or
                       response.context["search_results"].has_previous() or
                       response.context["search_results"].number == 1)

    def test_search_view_context_includes_filters(self):
        """Testa que contexto inclui todos os filtros disponíveis."""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)

        # Verificar que todos os filtros estão no contexto
        self.assertIn("canais", response.context)
        self.assertIn("tipos", response.context)
        self.assertIn("categorias_conteudo", response.context)
        self.assertIn("categorias_aplicativo", response.context)
        self.assertIn("licencas", response.context)
        self.assertIn("componentes", response.context)

    def test_search_view_current_filters_preserved(self):
        """Testa que current_filters mantém parâmetros na paginação."""
        response = self.client.get(reverse("search"), {"query": "teste", "canal": self.canal.id, "tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("current_filters", response.context)
        self.assertIn("query=teste", response.context["current_filters"])
        self.assertIn(f"canal={self.canal.id}", response.context["current_filters"])
        self.assertIn(f"tipo={self.tipo.id}", response.context["current_filters"])

    def test_search_results_include_conteudo(self):
        """Testa que resultados incluem ConteudoPage."""
        response = self.client.get(reverse("search"), {"query": "Busca", "tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conteúdo Teste Busca")

    def test_search_results_include_aplicativo(self):
        """Testa que resultados incluem AplicativoEducacionalPage."""
        response = self.client.get(reverse("search"), {"query": "Busca", "categoria_aplicativo": self.categoria_app.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "App Teste Busca")

    def test_search_empty_query_returns_all(self):
        """Testa que query vazia retorna todos (com paginação)."""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "")

    def test_search_invalid_canal_id_ignored(self):
        """Testa que canal_id inválido é ignorado."""
        response = self.client.get(reverse("search"), {"canal": "invalid"})
        self.assertEqual(response.status_code, 200)
        # FilterSet deve ignorar valor inválido

    def test_search_invalid_tipo_id_ignored(self):
        """Testa que tipo_id inválido é ignorado."""
        response = self.client.get(reverse("search"), {"tipo": "invalid"})
        self.assertEqual(response.status_code, 200)
        # FilterSet deve ignorar valor inválido

    def test_search_combined_filters_conteudo(self):
        """Testa combinação de múltiplos filtros para conteúdo."""
        response = self.client.get(reverse("search"), {
            "query": "teste",
            "canal": self.canal.id,
            "tipo": self.tipo.id,
            "licenca": self.licenca.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "teste")
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)

    def test_search_combined_filters_aplicativo(self):
        """Testa combinação de múltiplos filtros para aplicativo."""
        response = self.client.get(reverse("search"), {
            "query": "teste",
            "categoria_aplicativo": self.categoria_app.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "teste")
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        from search.filters import AplicativoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], AplicativoSearchFilterSet)

    def test_search_filterset_form_in_context_conteudo(self):
        """Testa que filterset.form está no contexto quando tipo inferido é conteúdo."""
        response = self.client.get(reverse("search"), {"tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("filterset", response.context)
        self.assertIsNotNone(response.context["filterset"])
        self.assertTrue(hasattr(response.context["filterset"], "form"))

    def test_search_filterset_form_fields_conteudo(self):
        """Testa que filterset.form de conteúdo tem os campos esperados."""
        response = self.client.get(reverse("search"), {"tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        filterset = response.context["filterset"]
        form = filterset.form
        # Verificar campos do ConteudoSearchFilterSet
        self.assertIn("query", form.fields)
        self.assertIn("canal", form.fields)
        self.assertIn("tipo", form.fields)
        self.assertIn("categoria_conteudo", form.fields)
        self.assertIn("licenca", form.fields)
        self.assertIn("componente", form.fields)
        # Não deve ter content_type
        self.assertNotIn("content_type", form.fields)

    def test_search_filterset_form_fields_aplicativo(self):
        """Testa que filterset.form de aplicativo tem campos esperados."""
        response = self.client.get(reverse("search"), {"categoria_aplicativo": self.categoria_app.id})
        self.assertEqual(response.status_code, 200)
        filterset = response.context["filterset"]
        form = filterset.form
        # Verificar campos do AplicativoSearchFilterSet
        self.assertIn("query", form.fields)
        self.assertIn("canal", form.fields)
        self.assertIn("categoria_aplicativo", form.fields)
        # Não deve ter tipo, licenca, componente, content_type
        self.assertNotIn("tipo", form.fields)
        self.assertNotIn("licenca", form.fields)
        self.assertNotIn("componente", form.fields)
        self.assertNotIn("content_type", form.fields)

    def test_search_selected_filters_in_context(self):
        """Testa que filtros selecionados são passados para o template."""
        response = self.client.get(reverse("search"), {
            "canal": self.canal.id,
            "tipo": self.tipo.id,
            "categoria_conteudo": self.categoria.id,
            "licenca": self.licenca.id,
            "componente": self.componente.id,
        })
        self.assertEqual(response.status_code, 200)
        # Verificar que objetos selecionados estão no contexto
        self.assertEqual(response.context["canal"], self.canal)
        self.assertEqual(response.context["tipo"], self.tipo)
        self.assertEqual(response.context["categoria_conteudo"], self.categoria)
        self.assertEqual(response.context["licenca"], self.licenca)
        self.assertEqual(response.context["componente"], self.componente)

    def test_search_selected_categoria_aplicativo_in_context(self):
        """Testa que categoria de aplicativo selecionada é passada para o template."""
        response = self.client.get(reverse("search"), {"categoria_aplicativo": self.categoria_app.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["categoria_aplicativo"], self.categoria_app)


class SearchTemplateTestCase(TestCase):
    """Testes para o template de busca."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.role_editor = Role.objects.get(slug="editor")
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.canal = CanalPage(
            title="Canal Template",
            name="Canal Template",
            slug="canal-template",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

    def test_search_template_has_form(self):
        """Testa que template tem formulário de busca."""
        response = self.client.get(reverse("search"))
        self.assertContains(response, 'form action="')
        self.assertContains(response, 'name="query"')
        self.assertContains(response, 'type="submit"')

    def test_search_template_has_filter_accordion(self):
        """Testa que template tem accordion de filtros."""
        response = self.client.get(reverse("search"))
        self.assertContains(response, "search-filters-accordion")
        self.assertContains(response, "search-filters-toggle")

    def test_search_template_has_filter_groups(self):
        """Testa que template tem grupos de filtros."""
        response = self.client.get(reverse("search"))
        self.assertContains(response, "filter-group")
        # Verificar labels dos filtros
        self.assertContains(response, "Canal")
        self.assertContains(response, "Tipo de Mídia")
        self.assertContains(response, "Categoria")
        self.assertContains(response, "Licença")
        self.assertContains(response, "Componente Curricular")
        # NÃO deve ter "Tipo de Conteúdo" (radio removido)
        self.assertNotContains(response, "Tipo de Conteúdo")
        self.assertNotContains(response, "Conteúdos Educacionais")
        self.assertNotContains(response, "Aplicativos Educacionais")

    def test_search_template_has_results_section(self):
        """Testa que template tem seção de resultados."""
        response = self.client.get(reverse("search"))
        self.assertContains(response, "search-results")
        self.assertContains(response, "results-header")
        self.assertContains(response, "results-grid")

    def test_search_template_has_pagination(self):
        """Testa que template tem paginação."""
        response = self.client.get(reverse("search"))
        self.assertContains(response, "pagination")
        self.assertContains(response, "page-link")

    def test_search_template_has_no_results_state(self):
        """Testa estado sem resultados."""
        response = self.client.get(reverse("search"), {"query": "xyznenhumresultadoxyz"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no-results")

    def test_search_template_has_initial_state(self):
        """Testa estado inicial (sem query)."""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "search-initial-state")

    def test_search_template_renders_filter_fields_when_tipo_selected(self):
        """Testa que template renderiza campos de filtro quando tipo é selecionado."""
        response = self.client.get(reverse("search"), {"tipo": "1"})
        self.assertEqual(response.status_code, 200)
        # Deve conter campos do filterset de conteúdo
        self.assertContains(response, 'name="canal"')
        self.assertContains(response, 'name="tipo"')
        self.assertContains(response, 'name="categoria_conteudo"')
        self.assertContains(response, 'name="categoria_aplicativo"')
        self.assertContains(response, 'name="licenca"')
        self.assertContains(response, 'name="componente"')

    def test_search_template_active_filters_tags(self):
        """Testa que template renderiza tags de filtros ativos."""
        from conteudos.models import Tipo
        tipo = Tipo.objects.create(name="Teste Tipo", slug="teste-tipo", is_active=True, ordem=1)
        response = self.client.get(reverse("search"), {"tipo": tipo.id, "query": "teste"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "search-filters-summary")
        self.assertContains(response, "filter-tag")
        self.assertContains(response, "Teste Tipo")
        self.assertContains(response, "teste")


class SearchIntegrationTestCase(TestCase):
    """Testes de integração da busca com models."""

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.role_editor = Role.objects.get(slug="editor")
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.canal = CanalPage(
            title="Canal Integração",
            name="Canal Integração",
            slug="canal-integracao",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        # Criar canal fixo para aplicativos (necessário para test_search_inference_tipo_overrides_categoria)
        cls.canal_apps = CanalPage(
            title="Aplicativos Educacionais",
            name="Aplicativos Educacionais",
            slug="aplicativos-educacionais",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal_apps)
        cls.canal_apps.save_revision().publish()

        cls.tipo = Tipo.objects.create(
            name="Documento",
            slug="documento-integracao",
            options={"formatos": ["pdf"]},
            is_active=True,
            ordem=2,
        )

        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Integração",
            slug="categoria-integracao",
            canal=cls.canal,
            ordem=1,
            is_active=True,
        )

        cls.editor = User.objects.create_user(
            username="editor_int",
            email="editor_int@test.com",
            password="testpass123",
            role=cls.role_editor,
        )

        # Criar múltiplos conteúdos para testar busca
        for i in range(3):
            conteudo = ConteudoPage(
                title=f"Conteúdo Integração {i}",
                tipo=cls.tipo,
                category=cls.categoria,
                arquivo=f"conteudos/integracao{i}.pdf",
                autor=cls.editor,
                canal=cls.canal,
            )
            cls.canal.add_child(instance=conteudo)
            conteudo.save_revision().publish()

    def test_search_finds_by_title(self):
        """Testa busca encontra por título."""
        response = self.client.get(reverse("search"), {"query": "Integração 1", "tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conteúdo Integração 1")

    def test_search_finds_partial_match(self):
        """Testa busca encontra correspondência parcial."""
        response = self.client.get(reverse("search"), {"query": "Integração", "tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        # Deve encontrar os 3 conteúdos
        self.assertContains(response, "Conteúdo Integração 0")
        self.assertContains(response, "Conteúdo Integração 1")
        self.assertContains(response, "Conteúdo Integração 2")

    def test_search_filter_by_canal_works(self):
        """Testa filtro por canal funciona na prática."""
        # Criar segundo canal
        canal2 = CanalPage(
            title="Canal 2",
            name="Canal 2",
            slug="canal-2-integracao",
            is_active=True,
        )
        self.root_page.add_child(instance=canal2)
        canal2.save_revision().publish()

        # Criar categoria no canal2
        from conteudos.models import CategoriaConteudo
        cat2 = CategoriaConteudo.objects.create(
            name="Cat Canal 2",
            slug="cat-canal-2",
            canal=canal2,
            ordem=1,
            is_active=True,
        )

        # Criar conteúdo no canal 2
        conteudo2 = ConteudoPage(
            title="Conteúdo Canal 2",
            tipo=self.tipo,
            category=cat2,
            arquivo="conteudos/canal2.pdf",
            autor=self.editor,
            canal=canal2,
        )
        canal2.add_child(instance=conteudo2)
        conteudo2.save_revision().publish()

        # Buscar filtrando por canal 1
        response = self.client.get(reverse("search"), {"canal": self.canal.id, "tipo": self.tipo.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conteúdo Integração")
        self.assertNotContains(response, "Conteúdo Canal 2")

    def test_search_inference_tipo_overrides_categoria(self):
        """Testa que preencher 'tipo' força busca em conteúdo mesmo com categoria de app."""
        # Criar categoria de app
        cat_app = AplicativoCategory.objects.create(
            name="Teste App",
            slug="teste-app-int",
            ordem=1,
            is_active=True,
        )
        with patch('requests.head') as mock_head, patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "192.168.1.1"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            canal_apps = CanalPage.objects.get(slug="aplicativos-educacionais")
            app = AplicativoEducacionalPage(
                title="App Integração",
                category=cat_app,
                url="https://app.int.com",
                description="B" * 140,
                autor=self.editor,
            )
            canal_apps.add_child(instance=app)
            app.tags.add("tag1", "tag2", "tag3")
            app.save_revision().publish()

        # Preencher tipo (conteúdo) E categoria de app
        # A regra: tipo/licenca/componente têm prioridade sobre categoria
        response = self.client.get(reverse("search"), {
            "tipo": self.tipo.id,
            "categoria_aplicativo": cat_app.id,
            "query": "Integração"
        })
        self.assertEqual(response.status_code, 200)
        # Deve buscar apenas conteúdo (tipo tem prioridade)
        from search.filters import ConteudoSearchFilterSet
        self.assertIsInstance(response.context["filterset"], ConteudoSearchFilterSet)
        self.assertContains(response, "Conteúdo Integração")
        self.assertNotContains(response, "App Integração")

    def test_search_pagination_preserves_filters(self):
        """Testa que paginação preserva parâmetros de filtro."""
        response = self.client.get(reverse("search"), {"query": "teste", "canal": self.canal.id, "tipo": self.tipo.id, "page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("current_filters", response.context)
        # Verificar que os links de paginação incluem os filtros
        self.assertIn("query=teste", response.context["current_filters"])
        self.assertIn(f"canal={self.canal.id}", response.context["current_filters"])
        self.assertIn(f"tipo={self.tipo.id}", response.context["current_filters"])