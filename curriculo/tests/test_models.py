"""
Testes para models do app curriculo.
"""
from django.test import TestCase
from django.db import IntegrityError

from curriculo.models import NivelEnsino, CurricularComponentCategory, CurricularComponent
from canais.models import CanalPage
from wagtail.models import Site


class CurriculoModelsTestCase(TestCase):
    """Testes para os models do app curriculo."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.canal = CanalPage(
            title="Canal Currículo",
            name="Canal Currículo",
            slug="canal-curriculo",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

    def test_nivel_ensino_creation(self):
        """Testa criação de NivelEnsino."""
        nivel = NivelEnsino.objects.create(
            name="Ensino Fundamental",
            slug="ensino-fundamental",
            ordem=1,
            is_active=True,
        )

        self.assertEqual(nivel.name, "Ensino Fundamental")
        self.assertEqual(nivel.slug, "ensino-fundamental")
        self.assertEqual(nivel.ordem, 1)
        self.assertTrue(nivel.is_active)

    def test_nivel_ensino_ordering(self):
        """Testa ordenação por ordem."""
        NivelEnsino.objects.create(name="Médio", slug="medio", ordem=2, is_active=True)
        NivelEnsino.objects.create(name="Fundamental", slug="fundamental", ordem=1, is_active=True)
        NivelEnsino.objects.create(name="Superior", slug="superior", ordem=3, is_active=True)

        niveis = list(NivelEnsino.objects.all())
        self.assertEqual(niveis[0].name, "Fundamental")
        self.assertEqual(niveis[1].name, "Médio")
        self.assertEqual(niveis[2].name, "Superior")

    def test_curricular_component_category_creation(self):
        """Testa criação de CurricularComponentCategory."""
        cat = CurricularComponentCategory.objects.create(
            name="Ciências da Natureza",
            slug="ciencias-natureza",
            description="Componentes de ciências",
            ordem=1,
            is_active=True,
        )

        self.assertEqual(cat.name, "Ciências da Natureza")
        self.assertEqual(cat.slug, "ciencias-natureza")
        self.assertTrue(cat.is_active)

    def test_curricular_component_category_tree(self):
        """Testa estrutura de árvore da categoria."""
        pai = CurricularComponentCategory.objects.create(
            name="Ciências",
            slug="ciencias",
            ordem=1,
            is_active=True,
        )

        filho = CurricularComponentCategory.objects.create(
            name="Biologia",
            slug="biologia",
            parent=pai,
            ordem=1,
            is_active=True,
        )

        self.assertEqual(filho.parent, pai)
        self.assertIn(filho, pai.children.all())

    def test_curricular_component_category_canais_permitidos_m2m(self):
        """Testa M2M canais_permitidos."""
        cat = CurricularComponentCategory.objects.create(
            name="Matemática",
            slug="matematica",
            ordem=1,
            is_active=True,
        )

        cat.canais_permitidos.add(self.canal)
        self.assertEqual(cat.canais_permitidos.count(), 1)
        self.assertIn(self.canal, cat.canais_permitidos.all())

        # Testar related_name reverso
        self.assertIn(cat, self.canal.categorias_componente_permitidas.all())

    def test_curricular_component_creation(self):
        """Testa criação de CurricularComponent."""
        nivel = NivelEnsino.objects.create(
            name="Ensino Médio",
            slug="ensino-medio",
            ordem=1,
            is_active=True,
        )

        cat = CurricularComponentCategory.objects.create(
            name="Matemática",
            slug="matematica",
            ordem=1,
            is_active=True,
        )

        componente = CurricularComponent.objects.create(
            name="Álgebra",
            slug="algebra",
            category=cat,
            nivel=nivel,
            description="Estudo de estruturas algébricas",
            ordem=1,
            is_active=True,
        )

        self.assertEqual(componente.name, "Álgebra")
        self.assertEqual(componente.category, cat)
        self.assertEqual(componente.nivel, nivel)
        self.assertTrue(componente.is_active)

    def test_curricular_component_unique_name_nivel_category(self):
        """Testa constraint unique (name, nivel, category)."""
        nivel = NivelEnsino.objects.create(
            name="Fundamental",
            slug="fundamental",
            ordem=1,
            is_active=True,
        )

        cat = CurricularComponentCategory.objects.create(
            name="Português",
            slug="portugues",
            ordem=1,
            is_active=True,
        )

        CurricularComponent.objects.create(
            name="Gramática",
            slug="gramatica",
            category=cat,
            nivel=nivel,
            ordem=1,
            is_active=True,
        )

        # Tentar criar outro com mesmo name, nivel, category deve falhar
        with self.assertRaises(IntegrityError):
            CurricularComponent.objects.create(
                name="Gramática",
                slug="gramatica-2",  # slug diferente mas name+nivel+category iguais
                category=cat,
                nivel=nivel,
                ordem=2,
                is_active=True,
            )

    def test_curricular_component_ordering(self):
        """Testa ordenação por nivel__ordem, category__ordem, name."""
        nivel1 = NivelEnsino.objects.create(name="Fundamental", slug="fundamental", ordem=1, is_active=True)
        nivel2 = NivelEnsino.objects.create(name="Médio", slug="medio", ordem=2, is_active=True)

        cat1 = CurricularComponentCategory.objects.create(name="Matemática", slug="matematica", ordem=1, is_active=True)
        cat2 = CurricularComponentCategory.objects.create(name="Português", slug="portugues", ordem=2, is_active=True)

        CurricularComponent.objects.create(name="Geometria", slug="geometria", category=cat1, nivel=nivel1, ordem=2, is_active=True)
        CurricularComponent.objects.create(name="Álgebra", slug="algebra", category=cat1, nivel=nivel1, ordem=1, is_active=True)
        CurricularComponent.objects.create(name="Literatura", slug="literatura", category=cat2, nivel=nivel1, ordem=1, is_active=True)
        CurricularComponent.objects.create(name="Cálculo", slug="calculo", category=cat1, nivel=nivel2, ordem=1, is_active=True)

        componentes = list(CurricularComponent.objects.all())

        # Ordem: nivel1/cat1/Álgebra, nivel1/cat1/Geometria, nivel1/cat2/Literatura, nivel2/cat1/Cálculo
        self.assertEqual(componentes[0].name, "Álgebra")
        self.assertEqual(componentes[1].name, "Geometria")
        self.assertEqual(componentes[2].name, "Literatura")
        self.assertEqual(componentes[3].name, "Cálculo")

    def test_curricular_component_str(self):
        """Testa representação string."""
        nivel = NivelEnsino.objects.create(name="Médio", slug="medio", ordem=1, is_active=True)
        cat = CurricularComponentCategory.objects.create(name="Física", slug="fisica", ordem=1, is_active=True)

        componente = CurricularComponent.objects.create(
            name="Mecânica",
            slug="mecanica",
            category=cat,
            nivel=nivel,
            ordem=1,
            is_active=True,
        )

        self.assertEqual(str(componente), "Mecânica (Médio)")


class CurriculoSearchTestCase(TestCase):
    """Testes para configuração de busca do curriculo."""

    def test_nivel_ensino_search_fields(self):
        """Testa que NivelEnsino tem search_fields."""
        self.assertTrue(hasattr(NivelEnsino, 'search_fields'))

    def test_curricular_component_category_search_fields(self):
        """Testa que CurricularComponentCategory tem search_fields."""
        self.assertTrue(hasattr(CurricularComponentCategory, 'search_fields'))

    def test_curricular_component_search_fields(self):
        """Testa que CurricularComponent tem search_fields."""
        self.assertTrue(hasattr(CurricularComponent, 'search_fields'))