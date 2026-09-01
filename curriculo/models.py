from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.search import index


class NivelEnsino(models.Model):
    """
    Nível de ensino (ex: "1º ano do Ensino Médio", "5º ano do Ensino Fundamental").
    Snippet consumido por CurricularComponent (FK obrigatória).
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome",
        help_text="Ex: '1º ano do Ensino Médio', '5º ano do Ensino Fundamental I'.",
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug",
        help_text="Identificador único para URLs e APIs.",
    )

    ordem = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição em listas/selects.",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = "Nível de Ensino"
        verbose_name_plural = "Níveis de Ensino"
        ordering = ["ordem", "name"]

    def __str__(self):
        return self.name

    # Wagtail search fields for snippets
    search_fields = [
        index.SearchField("name"),
        index.FilterField("is_active"),
        index.FilterField("ordem"),
    ]


class CurricularComponentCategory(models.Model):
    """
    Categoria de componente curricular — agrupador de disciplinas
    (ex: "Ciências da Natureza", "Linguagens", "Matemática").
    Snippet consumido por CurricularComponent (FK obrigatória) e
    por CanalPage via M2M (categorias_componente_permitidas).
    """

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nome",
        help_text="Agrupador de disciplinas (ex: 'Ciências da Natureza', 'Linguagens').",
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
        verbose_name="Slug",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    ordem = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ordem",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
    )

    # Tree structure (parent_id) — schema legado: categories é árvore
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Categoria Pai",
        help_text="Categoria pai para estrutura hierárquica.",
    )

    # M2M com CanalPage — filtro de categorias de componente por canal
    # Legado: pivot 'canal_cc_categories'
    # Direção inversa definida em canais.CanalPage.categorias_componente_permitidas
    # related_name="canais_permitidos" já definido lá

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
        FieldPanel("parent"),
    ]

    class Meta:
        verbose_name = "Categoria de Componente Curricular"
        verbose_name_plural = "Categorias de Componentes Curriculares"
        ordering = ["ordem", "name"]

    def __str__(self):
        return self.name

    # Wagtail search fields for snippets
    search_fields = [
        index.SearchField("name"),
        index.SearchField("description"),
        index.FilterField("is_active"),
        index.FilterField("ordem"),
    ]


class CurricularComponent(models.Model):
    """
    Componente curricular (disciplina) — combinação fixa de disciplina + nível.
    Cada componente pertence a EXATAMENTE UM nível e UMA categoria.
    Não é reaproveitável entre níveis: "Matemática — 1º ano" e "Matemática — 2º ano"
    são registros DIFERENTES (rigidez do schema legado, não corrigir para M2M).

    Consumido por ConteudoPage via ParentalManyToManyField (componentes_curriculares).
    """

    name = models.CharField(
        max_length=150,
        verbose_name="Nome",
        help_text="Nome do componente (ex: 'Matemática — 1º ano', 'Língua Portuguesa — 5º ano').",
    )

    slug = models.SlugField(
        max_length=150,
        verbose_name="Slug",
    )

    # FK obrigatória para categoria (agrupador)
    category = models.ForeignKey(
        "curriculo.CurricularComponentCategory",
        on_delete=models.PROTECT,
        related_name="componentes",
        verbose_name="Categoria",
        help_text="Agrupador disciplinar (ex: 'Matemática', 'Ciências da Natureza').",
    )

    # FK obrigatória para nível de ensino
    nivel = models.ForeignKey(
        "curriculo.NivelEnsino",
        on_delete=models.PROTECT,
        related_name="componentes",
        verbose_name="Nível de Ensino",
        help_text="Nível ao qual este componente pertence (ex: '1º ano do Ensino Médio').",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição pedagógica do componente (opcional).",
    )

    ordem = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ordem",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("category"),
        FieldPanel("nivel"),
        FieldPanel("description"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = "Componente Curricular"
        verbose_name_plural = "Componentes Curriculares"
        ordering = ["nivel__ordem", "category__ordem", "ordem", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "nivel", "category"],
                name="unique_componente_per_nivel_categoria",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.nivel.name})"

    # Wagtail search fields for snippets
    search_fields = [
        index.SearchField("name"),
        index.SearchField("description"),
        index.FilterField("is_active"),
        index.FilterField("ordem"),
        index.RelatedFields("nivel", [
            index.SearchField("name"),
            index.FilterField("is_active"),
        ]),
        index.RelatedFields("category", [
            index.SearchField("name"),
            index.FilterField("is_active"),
        ]),
    ]