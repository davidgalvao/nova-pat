"""
Testes para models do app aplicativos.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

from wagtail.models import Site
from wagtail.images import get_image_model

from canais.models import CanalPage
from aplicativos.models import AplicativoCategory, AplicativoEducacionalPage
from usuarios.models import User, Role


class AplicativosModelsTestCase(TestCase):
    """Testes para os models do app aplicativos."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        # Roles já existem via migration 0003_create_default_roles
        cls.role_editor = Role.objects.get(slug="editor")
        cls.editor = User.objects.create_user(
            username="editor",
            email="editor@test.com",
            password="testpass123",
            role=cls.role_editor,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar canal fixo (Aplicativos Educacionais) com pk=9
        # O save() do AplicativoEducacionalPage busca por pk=9 ou slug='aplicativos-educacionais'
        cls.canal_apps = CanalPage(
            title="Aplicativos Educacionais",
            name="Aplicativos Educacionais",
            slug="aplicativos-educacionais",
            is_active=True,
        )
        # Forçar pk=9 para corresponder ao que o save() espera
        cls.canal_apps.pk = 9
        cls.root_page.add_child(instance=cls.canal_apps)
        cls.canal_apps.save_revision().publish()

        # Criar categoria de aplicativo
        cls.categoria = AplicativoCategory.objects.create(
            name="Ferramentas de Estudo",
            slug="ferramentas-estudo",
            ordem=1,
            is_active=True,
        )

    def test_aplicativo_category_creation(self):
        """Testa criação de AplicativoCategory."""
        cat = AplicativoCategory.objects.create(
            name="Jogos Educativos",
            slug="jogos-educativos",
            description="Jogos para aprendizado",
            ordem=2,
            is_active=True,
        )

        self.assertEqual(cat.name, "Jogos Educativos")
        self.assertEqual(cat.slug, "jogos-educativos")
        self.assertTrue(cat.is_active)

    def test_aplicativo_category_tree(self):
        """Testa estrutura de árvore da categoria."""
        pai = AplicativoCategory.objects.create(
            name="Ciências",
            slug="ciencias",
            ordem=1,
            is_active=True,
        )

        filho = AplicativoCategory.objects.create(
            name="Física",
            slug="fisica",
            parent=pai,
            ordem=1,
            is_active=True,
        )

        self.assertEqual(filho.parent, pai)
        self.assertIn(filho, pai.children.all())

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_educacional_page_creation(self, mock_gethostbyname, mock_head):
        """Testa criação de AplicativoEducacionalPage."""
        # Mock DNS resolution
        mock_gethostbyname.return_value = "192.168.1.1"
        # Mock HTTP HEAD success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="Calculadora Científica",
            category=self.categoria,
            url="https://calculadora.exemplo.com",
            description="Uma calculadora científica completa para estudantes. "
                        "Permite cálculos avançados, gráficos de funções e "
                        "conversão de unidades. Ideal para ensino médio e superior.",
            is_featured=True,
            autor=self.editor,
        )
        self.canal_apps.add_child(instance=app)
        # Adicionar tags mínimas antes de publicar
        app.tags.add("tag1", "tag2", "tag3")
        app.save_revision().publish()

        # Verificar que canal foi forçado para id=9
        self.assertEqual(app.canal_id, 9)
        self.assertEqual(app.canal, self.canal_apps)

        # Verificar campos
        self.assertEqual(app.category, self.categoria)
        self.assertEqual(app.url, "https://calculadora.exemplo.com")
        self.assertTrue(app.is_featured)
        self.assertEqual(app.qt_access, 0)  # Contador inicia em 0

    def test_aplicativo_educacional_page_parent_page_types(self):
        """Testa configuração de parent_page_types."""
        self.assertEqual(AplicativoEducacionalPage.parent_page_types, ["canais.CanalPage"])
        self.assertEqual(AplicativoEducacionalPage.subpage_types, [])

    def test_aplicativo_clean_validates_description_min_length(self):
        """Testa validação de descrição mínima 140 caracteres."""
        app = AplicativoEducacionalPage(
            title="App Descrição Curta",
            category=self.categoria,
            url="https://exemplo.com",
            description="Curta",  # Menos de 140 chars
        )

        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("description", cm.exception.message_dict)
        self.assertIn("140 caracteres", str(cm.exception))

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_allows_valid_description(self, mock_gethostbyname, mock_head):
        """Testa que descrição válida passa."""
        # Mock DNS resolution
        mock_gethostbyname.return_value = "192.168.1.1"
        # Mock HTTP HEAD success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        descricao_valida = "A" * 140  # Exatamente 140 chars
        app = AplicativoEducacionalPage(
            title="App Válido",
            category=self.categoria,
            url="https://exemplo.com",
            description=descricao_valida,
            autor=self.editor,
        )

        # Não deve levantar exceção
        app.clean()

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_validates_url_active(self, mock_gethostbyname, mock_head):
        """Testa validação de URL ativa (DNS + HTTP)."""
        # Mock DNS resolution
        mock_gethostbyname.return_value = "192.168.1.1"

        # Mock HTTP HEAD success
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="App URL Válida",
            category=self.categoria,
            url="https://valido.exemplo.com",
            description="A" * 140,
            autor=self.editor,
        )

        # Não deve levantar exceção
        app.clean()

        mock_gethostbyname.assert_called_once_with("valido.exemplo.com")
        mock_head.assert_called_once()

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_rejects_invalid_dns(self, mock_gethostbyname, mock_head):
        """Testa rejeição de URL com DNS inválido."""
        import socket
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")

        app = AplicativoEducacionalPage(
            title="App DNS Inválido",
            category=self.categoria,
            url="https://invalido.naoexiste.xyz",
            description="A" * 140,
            autor=self.editor,
        )

        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("url", cm.exception.message_dict)
        self.assertIn("DNS", str(cm.exception))

    @patch('requests.head')
    @patch('requests.get')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_rejects_http_error(self, mock_gethostbyname, mock_get, mock_head):
        """Testa rejeição de URL com erro HTTP."""
        mock_gethostbyname.return_value = "192.168.1.1"

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        # Mock GET também falha
        mock_get_response = MagicMock()
        mock_get_response.status_code = 404
        mock_get.return_value = mock_get_response

        app = AplicativoEducacionalPage(
            title="App HTTP Error",
            category=self.categoria,
            url="https://erro.exemplo.com",
            description="A" * 140,
            autor=self.editor,
        )

        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("url", cm.exception.message_dict)
        self.assertIn("404", str(cm.exception))

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_validates_image_format(self, mock_gethostbyname, mock_head):
        """Testa validação de formato de imagem."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        # Criar imagem fake com formato inválido
        from wagtail.images.models import Image
        from io import BytesIO
        from PIL import Image as PILImage

        # Criar imagem BMP (formato não permitido)
        img = PILImage.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='BMP')
        buffer.seek(0)

        imagem_bmp = SimpleUploadedFile(
            "teste.bmp",
            buffer.read(),
            content_type="image/bmp"
        )

        # Criar objeto Image do Wagtail
        wagtail_image = Image.objects.create(
            title="Teste BMP",
            file=imagem_bmp,
        )

        app = AplicativoEducacionalPage(
            title="App Imagem Inválida",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            image=wagtail_image,
            autor=self.editor,
        )

        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("image", cm.exception.message_dict)
        self.assertIn("não permitido", str(cm.exception))

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_clean_validates_image_size(self, mock_gethostbyname, mock_head):
        """Testa validação de tamanho de imagem (max 1MB)."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        from wagtail.images.models import Image
        from io import BytesIO
        from PIL import Image as PILImage
        from unittest.mock import PropertyMock

        # Criar imagem grande (> 1MB) - usar dimensões muito grandes para garantir > 1MB após processamento
        img = PILImage.new('RGB', (5000, 5000), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        imagem_grande = SimpleUploadedFile(
            "grande.png",
            buffer.read(),
            content_type="image/png"
        )

        wagtail_image = Image.objects.create(
            title="Teste Grande",
            file=imagem_grande,
        )

        # Se o Wagtail comprimir a imagem para < 1MB, mockamos o tamanho do arquivo
        # para testar a validação
        if wagtail_image.file.size <= 1024 * 1024:
            # Mock do tamanho do arquivo para simular > 1MB
            type(wagtail_image.file).size = PropertyMock(return_value=2 * 1024 * 1024)

        app = AplicativoEducacionalPage(
            title="App Imagem Grande",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            image=wagtail_image,
            autor=self.editor,
        )

        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("image", cm.exception.message_dict)
        self.assertIn("1MB", str(cm.exception))

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_save_forces_canal_id_9(self, mock_gethostbyname, mock_head):
        """Testa que save() força canal_id=9."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="App Save Test",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            autor=self.editor,
        )
        self.canal_apps.add_child(instance=app)
        # Adicionar tags mínimas antes de salvar
        app.tags.add("tag1", "tag2", "tag3")
        app.save()

        self.assertEqual(app.canal_id, 9)

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_save_sets_qt_access_zero(self, mock_gethostbyname, mock_head):
        """Testa que save() garante qt_access=0 na criação."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="App Qt Access",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            qt_access=999,  # Valor forçado
            autor=self.editor,
        )
        self.canal_apps.add_child(instance=app)
        # Adicionar tags mínimas antes de salvar
        app.tags.add("tag1", "tag2", "tag3")
        app.save()

        self.assertEqual(app.qt_access, 0)

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_tags_validation_3_to_15(self, mock_gethostbyname, mock_head):
        """Testa validação de tags entre 3 e 15."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="App Tags",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            autor=self.editor,
        )
        self.canal_apps.add_child(instance=app)
        # Adicionar 3 tags mínimas para poder publicar
        app.tags.add("tag1", "tag2", "tag3")
        app.save_revision().publish()

        # Testar com 2 tags - deve falhar
        app.tags.clear()
        app.tags.add("tag1", "tag2")
        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("tags", cm.exception.message_dict)
        self.assertIn("Mínimo 3", str(cm.exception))

        # Adicionar 3ª tag - deve passar
        app.tags.add("tag3")
        app.clean()  # Não deve levantar

        # Adicionar muitas tags - deve falhar
        app.tags.clear()
        for i in range(1, 17):
            app.tags.add(f"tag{i}")
        with self.assertRaises(ValidationError) as cm:
            app.clean()

        self.assertIn("tags", cm.exception.message_dict)
        self.assertIn("Máximo 15", str(cm.exception))

    @patch('requests.head')
    @patch('socket.gethostbyname')
    def test_aplicativo_get_context(self, mock_gethostbyname, mock_head):
        """Testa get_context adiciona aplicativo."""
        # Mock DNS/HTTP para URL
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        app = AplicativoEducacionalPage(
            title="App Context",
            category=self.categoria,
            url="https://exemplo.com",
            description="A" * 140,
            autor=self.editor,
        )
        self.canal_apps.add_child(instance=app)
        # Adicionar tags mínimas antes de publicar
        app.tags.add("tag1", "tag2", "tag3")
        app.save_revision().publish()

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get("/")

        context = app.get_context(request)
        self.assertIn("aplicativo", context)
        self.assertEqual(context["aplicativo"], app)


class AplicativoSearchTestCase(TestCase):
    """Testes para configuração de busca do AplicativoEducacionalPage."""

    def test_search_fields_include_filter_fields(self):
        """Testa que search_fields inclui FilterField."""
        search_fields = AplicativoEducacionalPage.search_fields
        filter_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'FilterField'
        ]

        expected_filters = ["canal_id", "category_id", "is_featured", "first_published_at"]
        for expected in expected_filters:
            self.assertIn(expected, filter_field_names,
                f"FilterField '{expected}' não encontrado")

    def test_search_fields_include_search_fields(self):
        """Testa que search_fields inclui SearchField."""
        search_fields = AplicativoEducacionalPage.search_fields
        search_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'SearchField'
        ]

        expected_searches = ["title", "search_description", "description"]
        for expected in expected_searches:
            self.assertIn(expected, search_field_names,
                f"SearchField '{expected}' não encontrado")

    def test_search_fields_include_related_fields(self):
        """Testa que search_fields inclui RelatedFields."""
        search_fields = AplicativoEducacionalPage.search_fields
        related_field_names = [
            f.field_name for f in search_fields
            if hasattr(f, 'field_name') and f.__class__.__name__ == 'RelatedFields'
        ]

        expected_related = ["category", "canal", "tags"]
        for expected in expected_related:
            self.assertIn(expected, related_field_names,
                f"RelatedFields '{expected}' não encontrado")