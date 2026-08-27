"""
Testes para models do app conteudos.
"""
import os
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone

from wagtail.models import Site
from wagtail.images import get_image_model

from canais.models import CanalPage
from curriculo.models import NivelEnsino, CurricularComponentCategory, CurricularComponent
from conteudos.models import Tipo, Licenca, CategoriaConteudo, ConteudoPage
from usuarios.models import User, Role


class ConteudosModelsTestCase(TestCase):
    """Testes para os models do app conteudos."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        # Usar roles existentes (criados pela migration 0003_create_default_roles)
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.role_admin = Role.objects.get(slug="admin")
        cls.role_editor = Role.objects.get(slug="editor")
        cls.role_coordenador = Role.objects.get(slug="coordenador")
        cls.role_convidado = Role.objects.get(slug="convidado")

        # Criar usuário super-admin
        cls.super_admin = User.objects.create_user(
            username="superadmin",
            email="superadmin@test.com",
            password="testpass123",
            role=cls.role_super_admin,
        )

        # Criar usuário editor
        cls.editor = User.objects.create_user(
            username="editor",
            email="editor@test.com",
            password="testpass123",
            role=cls.role_editor,
        )

        # Criar site root
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar canal
        cls.canal = CanalPage(
            title="Canal Teste",
            name="Canal Teste",
            slug="canal-teste",
            description="Descrição do canal de teste",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        # Criar nível de ensino
        cls.nivel = NivelEnsino.objects.create(
            name="Ensino Médio",
            slug="ensino-medio",
            ordem=1,
            is_active=True,
        )

        # Criar categoria de componente curricular
        cls.cat_componente = CurricularComponentCategory.objects.create(
            name="Ciências da Natureza",
            slug="ciencias-natureza",
            ordem=1,
            is_active=True,
        )

        # Criar componente curricular
        cls.componente = CurricularComponent.objects.create(
            name="Biologia",
            slug="biologia",
            category=cls.cat_componente,
            nivel=cls.nivel,
            ordem=1,
            is_active=True,
        )

        # Criar tipo de mídia
        cls.tipo_video = Tipo.objects.create(
            name="Vídeo",
            slug="video",
            description="Conteúdo em vídeo",
            options={"formatos": [".mp4", ".webm", ".ogg"]},
            is_active=True,
            ordem=1,
        )

        cls.tipo_documento = Tipo.objects.create(
            name="Documento",
            slug="documento",
            description="Documento PDF",
            options={"formatos": [".pdf", ".doc", ".docx"]},
            is_active=True,
            ordem=2,
        )

        # Criar licença
        cls.licenca = Licenca.objects.create(
            name="CC BY 4.0",
            slug="cc-by-40",
            description="Creative Commons Attribution 4.0",
            url="https://creativecommons.org/licenses/by/4.0/",
            is_active=True,
            ordem=1,
        )

        # Criar categoria
        cls.categoria = CategoriaConteudo.objects.create(
            name="Videoaulas",
            slug="videoaulas",
            canal=cls.canal,
            ordem=1,
            is_active=True,
        )

    def test_tipo_validar_extensao(self):
        """Testa validação de extensão do Tipo."""
        # Extensões válidas
        self.assertTrue(self.tipo_video.validar_extensao(".mp4"))
        self.assertTrue(self.tipo_video.validar_extensao(".webm"))
        self.assertTrue(self.tipo_video.validar_extensao(".ogg"))

        # Extensões inválidas
        self.assertFalse(self.tipo_video.validar_extensao(".pdf"))
        self.assertFalse(self.tipo_video.validar_extensao(".exe"))

        # Case insensitive
        self.assertTrue(self.tipo_video.validar_extensao(".MP4"))
        self.assertTrue(self.tipo_video.validar_extensao(".WebM"))

    def test_tipo_get_formatos_permitidos(self):
        """Testa retorno de formatos permitidos."""
        formatos = self.tipo_video.get_formatos_permitidos()
        self.assertIn(".mp4", formatos)
        self.assertIn(".webm", formatos)
        self.assertIn(".ogg", formatos)

    def test_licenca_tree_structure(self):
        """Testa estrutura de árvore da Licenca."""
        licenca_pai = Licenca.objects.create(
            name="Creative Commons",
            slug="creative-commons-test",
            description="Licenças Creative Commons",
            is_active=True,
            ordem=1,
        )

        licenca_filha = Licenca.objects.create(
            name="CC BY 4.0",
            slug="cc-by-40-test",
            parent=licenca_pai,
            description="Creative Commons Attribution 4.0",
            is_active=True,
            ordem=1,
        )

        self.assertEqual(licenca_filha.parent, licenca_pai)
        self.assertIn(licenca_filha, licenca_pai.sublicencas.all())

    def test_categoria_scoped_by_canal(self):
        """Testa que CategoriaConteudo é escopada por canal."""
        # Criar outro canal
        canal2 = CanalPage(
            title="Canal 2",
            name="Canal 2",
            slug="canal-2",
            is_active=True,
        )
        self.root_page.add_child(instance=canal2)
        canal2.save_revision().publish()

        # Mesma slug em canais diferentes deve ser permitido
        cat1 = CategoriaConteudo.objects.create(
            name="Categoria Teste",
            slug="categoria-teste",
            canal=self.canal,
            is_active=True,
        )

        cat2 = CategoriaConteudo.objects.create(
            name="Categoria Teste",
            slug="categoria-teste",
            canal=canal2,
            is_active=True,
        )

        self.assertEqual(cat1.slug, cat2.slug)
        self.assertNotEqual(cat1.canal, cat2.canal)

    def test_conteudo_page_creation(self):
        """Testa criação de ConteudoPage."""
        conteudo = ConteudoPage(
            title="Videoaula de Biologia",
            tipo=self.tipo_video,
            category=self.categoria,
            license=self.licenca,
            canal=self.canal,
            autor=self.editor,
            authors="Prof. João Silva",
            source="https://exemplo.com",
            is_approved=True,
            is_featured=False,
            is_site=False,
        )
        self.canal.add_child(instance=conteudo)
        conteudo.save_revision().publish()

        # Verificar campos herdados de RecursoBasePage
        self.assertEqual(conteudo.canal, self.canal)
        self.assertEqual(conteudo.autor, self.editor)
        self.assertEqual(conteudo.tipo, self.tipo_video)
        self.assertEqual(conteudo.category, self.categoria)
        self.assertEqual(conteudo.license, self.licenca)

        # Verificar contadores iniciam em zero (RN-L6)
        self.assertEqual(conteudo.qt_downloads, 0)
        self.assertEqual(conteudo.qt_access, 0)

        # Verificar campos desnormalizados
        self.assertEqual(conteudo.media_avaliacao, 0)
        self.assertEqual(conteudo.total_avaliacoes, 0)

    def test_conteudo_page_clean_validates_file_extension(self):
        """Testa validação de extensão de arquivo no clean (RN-L3)."""
        # Criar arquivo de teste com extensão inválida
        arquivo_invalido = SimpleUploadedFile(
            "teste.exe",
            b"conteudo fake",
            content_type="application/octet-stream"
        )

        conteudo = ConteudoPage(
            title="Conteúdo com arquivo inválido",
            tipo=self.tipo_video,  # Só aceita .mp4, .webm, .ogg
            category=self.categoria,
            canal=self.canal,
            autor=self.editor,
            arquivo=arquivo_invalido,
        )

        with self.assertRaises(ValidationError) as cm:
            conteudo.clean()

        self.assertIn("arquivo", cm.exception.message_dict)
        self.assertIn(".exe", str(cm.exception))

    def test_conteudo_page_clean_allows_valid_extension(self):
        """Testa que extensão válida passa na validação."""
        arquivo_valido = SimpleUploadedFile(
            "video.mp4",
            b"fake video content",
            content_type="video/mp4"
        )

        conteudo = ConteudoPage(
            title="Videoaula válida",
            tipo=self.tipo_video,
            category=self.categoria,
            canal=self.canal,
            autor=self.editor,
            arquivo=arquivo_valido,
        )

        # Não deve levantar exceção
        conteudo.clean()

    def test_conteudo_page_save_sets_counters_to_zero(self):
        """Testa que save() garante contadores em zero na criação (RN-L6)."""
        conteudo = ConteudoPage(
            title="Novo conteúdo",
            tipo=self.tipo_video,
            category=self.categoria,
            canal=self.canal,
            autor=self.editor,
            qt_downloads=999,  # Valor forçado
            qt_access=888,     # Valor forçado
        )
        self.canal.add_child(instance=conteudo)
        conteudo.save()

        # Contadores devem ser resetados para 0 na criação
        self.assertEqual(conteudo.qt_downloads, 0)
        self.assertEqual(conteudo.qt_access, 0)

    def test_conteudo_page_get_template_by_tipo(self):
        """Testa seleção de template pelo tipo (decisão fechada)."""
        conteudo = ConteudoPage(
            title="Teste template",
            tipo=self.tipo_video,
            category=self.categoria,
            canal=self.canal,
            autor=self.editor,
        )
        self.canal.add_child(instance=conteudo)
        conteudo.save()

        template = conteudo.get_template(None)
        self.assertEqual(template, "conteudos/conteudo_page_video.html")

        # Testar com tipo documento
        conteudo.tipo = self.tipo_documento
        conteudo.save()
        template = conteudo.get_template(None)
        self.assertEqual(template, "conteudos/conteudo_page_documento.html")

    def test_conteudo_page_parent_page_types(self):
        """Testa configuração de parent_page_types."""
        self.assertIn("canais.CanalPage", ConteudoPage.parent_page_types)
        self.assertIn("series.Temporada", ConteudoPage.parent_page_types)
        self.assertEqual(ConteudoPage.subpage_types, [])

    def test_categoria_unique_slug_per_canal(self):
        """Testa constraint unique slug por canal."""
        CategoriaConteudo.objects.create(
            name="Categoria 1",
            slug="categoria-unica",
            canal=self.canal,
            is_active=True,
        )

        # Tentar criar com mesma slug no mesmo canal deve falhar
        with self.assertRaises(Exception):
            CategoriaConteudo.objects.create(
                name="Categoria 2",
                slug="categoria-unica",
                canal=self.canal,
                is_active=True,
            )

    def test_tipo_is_active_filter(self):
        """Testa filtro is_active no Tipo."""
        Tipo.objects.create(
            name="Tipo Inativo",
            slug="tipo-inativo",
            is_active=False,
        )

        ativos = Tipo.objects.filter(is_active=True)
        self.assertEqual(ativos.count(), 2)  # video e documento
        self.assertNotIn("tipo-inativo", [t.slug for t in ativos])


class ConteudoPageSearchTestCase(TestCase):
    """Testes para configuração de busca do ConteudoPage."""

    @classmethod
    def setUpTestData(cls):
        # Usar role existente (criada pela migration 0003_create_default_roles)
        cls.role_editor = Role.objects.get(slug="editor")
        cls.editor = User.objects.create_user(
            username="editor_search",
            email="editor_search@test.com",
            password="testpass123",
            role=cls.role_editor,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.canal = CanalPage(
            title="Canal Busca",
            name="Canal Busca",
            slug="canal-busca",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.nivel = NivelEnsino.objects.create(
            name="Fundamental",
            slug="fundamental",
            ordem=1,
            is_active=True,
        )

        cls.cat_componente = CurricularComponentCategory.objects.create(
            name="Matemática",
            slug="matematica",
            ordem=1,
            is_active=True,
        )

        cls.componente = CurricularComponent.objects.create(
            name="Álgebra",
            slug="algebra",
            category=cls.cat_componente,
            nivel=cls.nivel,
            ordem=1,
            is_active=True,
        )

        cls.tipo = Tipo.objects.create(
            name="Vídeo",
            slug="video",
            options={"formatos": [".mp4"]},
            is_active=True,
            ordem=1,
        )

        cls.categoria = CategoriaConteudo.objects.create(
            name="Aulas",
            slug="aulas",
            canal=cls.canal,
            is_active=True,
        )

        cls.licenca = Licenca.objects.create(
            name="CC BY",
            slug="cc-by",
            is_active=True,
        )

        # Criar conteúdos para teste de busca
        cls.conteudo1 = ConteudoPage(
            title="Videoaula de Álgebra Linear",
            search_description="Aula sobre matrizes e determinantes",
            tipo=cls.tipo,
            category=cls.categoria,
            license=cls.licenca,
            canal=cls.canal,
            autor=cls.editor,
            authors="Prof. Matemática",
        )
        cls.canal.add_child(instance=cls.conteudo1)
        cls.conteudo1.save_revision().publish()

        cls.conteudo2 = ConteudoPage(
            title="Geometria Analítica",
            search_description="Estudo de retas e planos",
            tipo=cls.tipo,
            category=cls.categoria,
            license=cls.licenca,
            canal=cls.canal,
            autor=cls.editor,
            authors="Prof. Geometria",
        )
        cls.canal.add_child(instance=cls.conteudo2)
        cls.conteudo2.save_revision().publish()

    def test_search_fields_include_filter_fields(self):
        """Testa que search_fields inclui FilterField para campos de filtro."""
        search_fields = ConteudoPage.search_fields
        filter_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'FilterField'
        ]

        expected_filters = [
            "canal_id", "tipo_id", "category_id", "license_id",
            "componentes_curriculares", "is_approved", "is_featured",
            "is_site", "first_published_at"
        ]

        for expected in expected_filters:
            self.assertIn(expected, filter_field_names,
                f"FilterField '{expected}' não encontrado em search_fields")

    def test_search_fields_include_search_fields(self):
        """Testa que search_fields inclui SearchField para busca textual."""
        search_fields = ConteudoPage.search_fields
        search_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'SearchField'
        ]

        expected_searches = ["title", "search_description", "authors", "source"]
        for expected in expected_searches:
            self.assertIn(expected, search_field_names,
                f"SearchField '{expected}' não encontrado em search_fields")

    def test_search_fields_include_related_fields(self):
        """Testa que search_fields inclui RelatedFields para relações."""
        search_fields = ConteudoPage.search_fields
        related_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'RelatedFields'
        ]

        expected_related = ["tipo", "category", "license", "canal", "componentes_curriculares"]
        for expected in expected_related:
            self.assertIn(expected, related_field_names,
                f"RelatedFields '{expected}' não encontrado em search_fields")