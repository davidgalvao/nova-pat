"""
Testes para models do app canais.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from wagtail.models import Site

from canais.models import CanalPage
from curriculo.models import CurricularComponentCategory
from usuarios.models import User, Role


class CanaisModelsTestCase(TestCase):
    """Testes para os models do app canais."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        # Usar roles existentes (criados pela migration 0003_create_default_roles)
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.super_admin = User.objects.create_user(
            username="superadmin_canais",
            email="superadmin_canais@test.com",
            password="testpass123",
            role=cls.role_super_admin,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar categorias de componente para M2M
        cls.cat_componente = CurricularComponentCategory.objects.create(
            name="Ciências",
            slug="ciencias-canais",
            ordem=1,
            is_active=True,
        )

    def test_canal_page_creation(self):
        """Testa criação de CanalPage."""
        canal = CanalPage(
            title="TV Anísio Teixeira",
            name="TV Anísio Teixeira",
            slug="tv-anisio-teixeira",
            description="Canal de vídeos educacionais",
            is_active=True,
            options={"cor": "#FF5733"},
        )
        self.root_page.add_child(instance=canal)
        canal.save_revision().publish()

        self.assertEqual(canal.name, "TV Anísio Teixeira")
        self.assertEqual(canal.slug, "tv-anisio-teixeira")
        self.assertTrue(canal.is_active)
        self.assertEqual(canal.options, {"cor": "#FF5733"})

    def test_canal_page_parent_page_types(self):
        """Testa configuração de parent_page_types."""
        self.assertEqual(CanalPage.parent_page_types, ["wagtailcore.Page"])
        self.assertIn("conteudos.ConteudoPage", CanalPage.subpage_types)
        self.assertIn("aplicativos.AplicativoEducacionalPage", CanalPage.subpage_types)

    def test_canal_page_categorias_componente_permitidas_m2m(self):
        """Testa M2M categorias_componente_permitidas."""
        canal = CanalPage(
            title="Canal com Componentes",
            name="Canal com Componentes",
            slug="canal-com-componentes",
            is_active=True,
        )
        self.root_page.add_child(instance=canal)
        canal.save_revision().publish()

        canal.categorias_componente_permitidas.add(self.cat_componente)
        self.assertEqual(canal.categorias_componente_permitidas.count(), 1)
        self.assertIn(self.cat_componente, canal.categorias_componente_permitidas.all())

        # Testar related_name
        self.assertIn(canal, self.cat_componente.canais_permitidos.all())

    def test_canal_page_get_context(self):
        """Testa get_context adiciona conteudos e aplicativos."""
        canal = CanalPage(
            title="Canal Contexto",
            name="Canal Contexto",
            slug="canal-contexto",
            is_active=True,
        )
        self.root_page.add_child(instance=canal)
        canal.save_revision().publish()

        # Simular request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get("/")

        context = canal.get_context(request)
        self.assertIn("conteudos", context)
        self.assertIn("aplicativos", context)

    def test_canal_name_unique(self):
        """Testa que name é único."""
        canal1 = CanalPage(
            title="Canal 1",
            name="Canal Único",
            slug="canal-1",
            is_active=True,
        )
        self.root_page.add_child(instance=canal1)
        canal1.save_revision().publish()

        # Tentar criar outro com mesmo name deve falhar no add_child (que chama save)
        canal2 = CanalPage(
            title="Canal 2",
            name="Canal Único",
            slug="canal-2",
            is_active=True,
        )
        with self.assertRaises(Exception):
            self.root_page.add_child(instance=canal2)

    def test_canal_token_hidden_warning(self):
        """Testa que token tem help_text de aviso."""
        canal = CanalPage(
            title="Canal Token",
            name="Canal Token",
            slug="canal-token",
            token="secret-token-123",
            is_active=True,
        )
        self.root_page.add_child(instance=canal)
        canal.save_revision().publish()

        # Verificar que o campo existe e tem help_text
        field = canal._meta.get_field("token")
        self.assertIn("NUNCA expor", field.help_text)

    def test_canal_is_active_default_true(self):
        """Testa que is_active default é True."""
        canal = CanalPage(
            title="Canal Default",
            name="Canal Default",
            slug="canal-default",
        )
        self.root_page.add_child(instance=canal)
        canal.save_revision().publish()

        self.assertTrue(canal.is_active)

    def test_canal_ordering_by_name(self):
        """Testa ordenação por name no Meta."""
        # Limpar canais existentes criados por outros testes
        CanalPage.objects.all().delete()
        
        canal_z = CanalPage(
            title="Canal Z",
            name="Canal Z",
            slug="canal-z-order",
            is_active=True,
        )
        self.root_page.add_child(instance=canal_z)
        canal_z.save_revision().publish()

        canal_a = CanalPage(
            title="Canal A",
            name="Canal A",
            slug="canal-a-order",
            is_active=True,
        )
        self.root_page.add_child(instance=canal_a)
        canal_a.save_revision().publish()

        canais = list(CanalPage.objects.all().order_by("name"))
        self.assertEqual(canais[0].name, "Canal A")
        self.assertEqual(canais[1].name, "Canal Z")


class CanalPageSearchTestCase(TestCase):
    """Testes para configuração de busca do CanalPage."""

    @classmethod
    def setUpTestData(cls):
        # Usar role existente (criada pela migration 0003_create_default_roles)
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.super_admin = User.objects.create_user(
            username="superadmin_canais_search",
            email="superadmin_canais_search@test.com",
            password="testpass123",
            role=cls.role_super_admin,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

    def test_canal_search_fields_exist(self):
        """Testa que CanalPage tem search_fields configurados."""
        # CanalPage herda de BasePage que herda de Page
        # Verificar se tem search_fields
        self.assertTrue(hasattr(CanalPage, 'search_fields'))
        self.assertGreater(len(CanalPage.search_fields), 0)