"""
Testes para models do app series.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from wagtail.models import Site

from series.models import Serie, Temporada
from canais.models import CanalPage
from conteudos.models import Tipo, CategoriaConteudo, Licenca
from usuarios.models import User, Role


class SeriesModelsTestCase(TestCase):
    """Testes para os models do app series."""

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

        # Criar canal (para ConteudoPage)
        cls.canal = CanalPage(
            title="Canal Séries",
            name="Canal Séries",
            slug="canal-series",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        # Criar tipo, categoria, licença para ConteudoPage
        cls.tipo = Tipo.objects.create(
            name="Vídeo",
            slug="video",
            options={"formatos": [".mp4"]},
            is_active=True,
            ordem=1,
        )

        cls.categoria = CategoriaConteudo.objects.create(
            name="Séries",
            slug="series",
            canal=cls.canal,
            is_active=True,
        )

        cls.licenca = Licenca.objects.create(
            name="CC BY",
            slug="cc-by",
            is_active=True,
        )

    def test_serie_creation(self):
        """Testa criação de Serie."""
        serie = Serie(
            title="Série de Biologia",
            sinopse="Uma série sobre biologia",
            canal=None,  # Serie é independente de Canal (RF008)
            autor=self.editor,
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        self.assertEqual(serie.title, "Série de Biologia")
        self.assertEqual(serie.sinopse, "Uma série sobre biologia")
        self.assertIsNone(serie.canal)  # Canal é opcional/nulo
        self.assertEqual(serie.autor, self.editor)

    def test_serie_canal_override_nullable(self):
        """Testa que Serie sobrescreve canal para ser nullable (RF008)."""
        # Verificar que o campo canal permite null e blank
        canal_field = Serie._meta.get_field("canal")
        self.assertTrue(canal_field.null)
        self.assertTrue(canal_field.blank)

    def test_serie_parent_page_types(self):
        """Testa configuração de parent_page_types."""
        self.assertEqual(Serie.parent_page_types, ["wagtailcore.Page"])
        self.assertIn("series.Temporada", Serie.subpage_types)

    def test_serie_get_context_includes_temporadas(self):
        """Testa get_context adiciona temporadas."""
        serie = Serie(
            title="Série Contexto",
            autor=self.editor,
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        # Criar temporada
        temporada = Temporada(
            title="Temporada 1",
            numero=1,
            sinopse="Primeira temporada",
        )
        serie.add_child(instance=temporada)
        temporada.save_revision().publish()

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get("/")

        context = serie.get_context(request)
        self.assertIn("temporadas", context)
        self.assertEqual(len(context["temporadas"]), 1)
        # get_context returns specific pages
        self.assertEqual(context["temporadas"][0], temporada)

    def test_temporada_creation(self):
        """Testa criação de Temporada."""
        serie = Serie(
            title="Série para Temporada",
            autor=self.editor,
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        temporada = Temporada(
            title="Temporada 1",
            numero=1,
            sinopse="Primeira temporada",
        )
        serie.add_child(instance=temporada)
        temporada.save_revision().publish()

        self.assertEqual(temporada.title, "Temporada 1")
        self.assertEqual(temporada.numero, 1)
        self.assertEqual(temporada.sinopse, "Primeira temporada")
        self.assertEqual(temporada.get_parent(), serie)

    def test_temporada_parent_page_types(self):
        """Testa configuração de parent_page_types."""
        self.assertEqual(Temporada.parent_page_types, ["series.Serie"])
        self.assertIn("conteudos.ConteudoPage", Temporada.subpage_types)

    def test_temporada_unique_numero_per_serie(self):
        """Testa validação de numero único por série."""
        serie = Serie(
            title="Série Única",
            autor=self.editor,
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        # Criar primeira temporada
        t1 = Temporada(title="Temporada 1", numero=1, sinopse="Primeira")
        serie.add_child(instance=t1)
        t1.save_revision().publish()

        # Tentar criar outra temporada com mesmo numero na mesma serie
        # A validação ocorre no full_clean() durante add_child()
        t2 = Temporada(title="Temporada 1 Duplicada", numero=1, sinopse="Duplicada")
        
        with self.assertRaises(ValidationError):
            serie.add_child(instance=t2)

    def test_temporada_get_context_includes_episodios(self):
        """Testa get_context adiciona episódios ordenados por numero_episodio."""
        serie = Serie(
            title="Série Episódios",
            autor=self.editor,
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        temporada = Temporada(
            title="Temporada 1",
            numero=1,
        )
        serie.add_child(instance=temporada)
        temporada.save_revision().publish()

        # Criar episódios (ConteudoPage filhos da temporada)
        ep1 = ConteudoPage(
            title="Episódio 2",
            numero_episodio=2,
            tipo=self.tipo,
            category=self.categoria,
            license=self.licenca,
            canal=self.canal,
            autor=self.editor,
        )
        temporada.add_child(instance=ep1)
        ep1.save_revision().publish()

        ep2 = ConteudoPage(
            title="Episódio 1",
            numero_episodio=1,
            tipo=self.tipo,
            category=self.categoria,
            license=self.licenca,
            canal=self.canal,
            autor=self.editor,
        )
        temporada.add_child(instance=ep2)
        ep2.save_revision().publish()

        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get("/")

        context = temporada.get_context(request)
        self.assertIn("episodios", context)
        episodios = list(context["episodios"])
        self.assertEqual(len(episodios), 2)
        # Devem estar ordenados por numero_episodio
        self.assertEqual(episodios[0].numero_episodio, 1)
        self.assertEqual(episodios[1].numero_episodio, 2)

    def test_temporada_str(self):
        """Testa representação string."""
        serie = Serie(title="Minha Série", autor=self.editor)
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        temporada = Temporada(title="Temporada 1", numero=1)
        serie.add_child(instance=temporada)
        temporada.save_revision().publish()

        self.assertEqual(str(temporada), "Minha Série — Temporada 1")

    def test_serie_independent_of_canal(self):
        """Testa que Serie não requer canal (RF008 - independente de Canal)."""
        serie = Serie(
            title="Série Independente",
            autor=self.editor,
            # canal não fornecido
        )
        self.root_page.add_child(instance=serie)
        serie.save_revision().publish()

        self.assertIsNone(serie.canal)

        # Mas ConteudoPage filho de Temporada ainda precisa de canal
        temporada = Temporada(title="Temp 1", numero=1)
        serie.add_child(instance=temporada)
        temporada.save_revision().publish()

        ep = ConteudoPage(
            title="Episódio",
            numero_episodio=1,
            tipo=self.tipo,
            category=self.categoria,
            license=self.licenca,
            canal=self.canal,  # Episódio precisa de canal
            autor=self.editor,
        )
        temporada.add_child(instance=ep)
        ep.save_revision().publish()

        self.assertEqual(ep.canal, self.canal)


# Import ConteudoPage here to avoid circular import
from conteudos.models import ConteudoPage