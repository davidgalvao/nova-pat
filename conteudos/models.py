from django import forms
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from django.template.loader import select_template
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalManyToManyField
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.images import get_image_model_string
from wagtail.fields import RichTextField
from wagtail.search import index

# Import do core para herdar de RecursoBasePage
from core.models import RecursoBasePage


class Tipo(models.Model):
    """
    Tipo de mídia do conteúdo (vídeo, documento, podcast, etc.).
    Carrega em `options.formatos` a lista de extensões de arquivo permitidas
    para aquele tipo — **é configuração ativa de validação de upload, não só etiqueta**.
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descrição")
    options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Opções",
        help_text="JSON com configurações do tipo. Ex: {'formatos': ['mp4', 'webm', 'ogg']}"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem de exibição")

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("options"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]

    class Meta:
        verbose_name = "Tipo de Conteúdo"
        verbose_name_plural = "Tipos de Conteúdo"
        ordering = ["ordem", "name"]

    def __str__(self):
        return self.name

    def get_formatos_permitidos(self):
        """Retorna lista de extensões permitidas para este tipo."""
        return self.options.get("formatos", [])

    def validar_extensao(self, extensao: str) -> bool:
        """Valida se a extensão é permitida para este tipo."""
        formatos = self.get_formatos_permitidos()
        if not formatos:
            return True  # Se não há restrição, permite
        return extensao.lower().lstrip(".") in [f.lower().lstrip(".") for f in formatos]


class Licenca(models.Model):
    """
    Árvore de licenças (modelo tipo Creative Commons — licença pode ter sublicenças).
    Exclusiva do app `conteudos` — `aplicativos` não tem licença no legado.
    """

    name = models.CharField(max_length=150, verbose_name="Nome")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descrição")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sublicencas",
        verbose_name="Licença pai",
    )
    url = models.URLField(blank=True, verbose_name="URL da licença")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("parent"),
        FieldPanel("url"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]

    class Meta:
        verbose_name = "Licença"
        verbose_name_plural = "Licenças"
        ordering = ["ordem", "name"]

    def __str__(self):
        return self.name


class CategoriaConteudo(models.Model):
    """
    Árvore de categorias escopada por canal.
    Distinta da categoria de aplicativo (AplicativoCategory) — não fundir.
    """

    name = models.CharField(max_length=150, verbose_name="Nome")
    slug = models.SlugField(max_length=150, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descrição")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="subcategorias",
        verbose_name="Categoria pai",
    )
    canal = models.ForeignKey(
        "canais.CanalPage",
        on_delete=models.PROTECT,
        related_name="categorias",
        verbose_name="Canal",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("parent"),
        FieldPanel("canal"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]

    class Meta:
        verbose_name = "Categoria de Conteúdo"
        verbose_name_plural = "Categorias de Conteúdo"
        ordering = ["canal", "ordem", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "canal"],
                name="unique_categoriaconteudo_slug_per_canal",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.canal.name})"


class ConteudoPage(RecursoBasePage):
    """
    Página de conteúdo educacional — entidade central do sistema.
    Herda de RecursoBasePage (canal, autor, tags) e adiciona campos próprios.
    """

    # ------------------------------------------------------------------
    # Mecanismo de Exibição (Formato Técnico)
    # ------------------------------------------------------------------
    # Distinto da taxonomia pedagógica (`tipo`). Enquanto `tipo` é a
    # categoria pedagógica usada em filtros de busca e currículo, o
    # `mecanismo_exibicao` é o formato técnico que determina a view de
    # renderização (player, visualizador, download, link externo, etc.).
    # Decisão fechada em CONTEXT.MD seção 3.
    MECANISMO_VIDEO = "video"
    MECANISMO_AUDIO = "audio"
    MECANISMO_DOCUMENTO_PDF = "documento_pdf"
    MECANISMO_APRESENTACAO = "apresentacao"
    MECANISMO_DOWNLOAD_BINARIO = "download_binario"
    MECANISMO_LINK_EXTERNO = "link_externo"
    MECANISMO_ANIMACAO_EXTERNA = "animacao_externa"

    MECANISMO_CHOICES = [
        (MECANISMO_VIDEO, _("Vídeo — Player responsivo 16:9.")),
        (MECANISMO_AUDIO, _("Áudio — Player de áudio nativo estilizado.")),
        (MECANISMO_DOCUMENTO_PDF, _("Documento PDF — Visualizador embutido ou download seguro de PDF.")),
        (MECANISMO_APRESENTACAO, _("Apresentação — Visualizador/download de apresentação.")),
        (MECANISMO_DOWNLOAD_BINARIO, _("Download binário — Download seguro de pacotes/executáveis (.zip, .rar, .exe).")),
        (MECANISMO_LINK_EXTERNO, _("Link externo — Link externo seguro (noopener noreferrer).")),
        (MECANISMO_ANIMACAO_EXTERNA, _("Animação externa — iframe protegido para animações/sites externos.")),
    ]

    # Campos próprios (além de canal, autor, tags herdados de RecursoBasePage)
    tipo = models.ForeignKey(
        "conteudos.Tipo",
        on_delete=models.PROTECT,
        verbose_name="Tipo de mídia",
        help_text="Categoria pedagógica do conteúdo (usada em filtros de busca e currículo).",
    )

    mecanismo_exibicao = models.CharField(
        max_length=30,
        choices=MECANISMO_CHOICES,
        default=MECANISMO_LINK_EXTERNO,
        verbose_name="Mecanismo de Exibição",
        help_text=(
            "Formato técnico de renderização (distinto da categoria pedagógica 'tipo'). "
            "Determina o player/visualizador usado na exibição do conteúdo."
        ),
    )

    category = models.ForeignKey(
        "conteudos.CategoriaConteudo",
        on_delete=models.PROTECT,
        verbose_name="Categoria",
        help_text="Categoria do conteúdo (árvore escopada por canal).",
    )

    license = models.ForeignKey(
        "conteudos.Licenca",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Licença",
        help_text="Licença de uso (estrutura em árvore tipo Creative Commons).",
    )

    # Tags via django-taggit (herdado de RecursoBasePage, mas reforçando aqui para painel)
    # tags = TaggableManager(blank=True, verbose_name="Tags")  # Já vem de RecursoBasePage

    componentes_curriculares = ParentalManyToManyField(
        "curriculo.CurricularComponent",
        blank=True,
        verbose_name="Componentes Curriculares",
        help_text="Mínimo 1 obrigatório (regra pedagógica RN-L5).",
    )

    # Arquivo/mídia associado
    arquivo = models.FileField(
        upload_to="conteudos/arquivos/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Arquivo",
        help_text="Arquivo de mídia/documento. Extensão validada conforme o Tipo (RN-L3).",
    )

    # Metadados adicionais
    authors = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Autores do conteúdo",
        help_text="Nomes dos autores/criadores do recurso (diferente do autor publicador).",
    )

    source = models.URLField(
        blank=True,
        verbose_name="Fonte original",
        help_text="URL da fonte original do conteúdo, se aplicável.",
    )

    options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Opções extras",
        help_text="JSON para dados flexíveis (acessibilidade, site associado, etc.).",
    )

    # Workflow de aprovação (RN-L1)
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Aprovado",
        help_text="Conteúdo aprovado para publicação. Só coordenador+ pode aprovar.",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Em destaque",
        help_text="Exibir em destaque na home/listagens.",
    )

    is_site = models.BooleanField(
        default=False,
        verbose_name="É site",
        help_text="Marca se o conteúdo é um site associado (legado: is_site).",
    )

    # Contadores (RN-L6)
    qt_downloads = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade de downloads",
        editable=False,
    )

    qt_access = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade de acessos",
        editable=False,
    )

    # Suporte a episódios de série (RF008)
    numero_episodio = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Número do episódio",
        help_text="Preenchido apenas quando o conteúdo é filho de uma Temporada (app series).",
    )

    # Campos desnormalizados para exibição (atualizados via signal do app interacoes)
    media_avaliacao = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name="Média de avaliação",
        editable=False,
        help_text="Atualizado automaticamente via signal. Não usar em filtros/ordenação (RF011).",
    )

    total_avaliacoes = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de avaliações",
        editable=False,
        help_text="Atualizado automaticamente via signal.",
    )

    # Configuração de árvore de páginas
    parent_page_types = ["canais.CanalPage", "series.Temporada"]
    subpage_types = []  # Conteúdo não tem filhos

    # Painéis de conteúdo (herda de RecursoBasePage que já tem canal, autor, tags)
    content_panels = RecursoBasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel("tipo"),
            FieldPanel("category"),
            FieldPanel("license"),
            FieldPanel("componentes_curriculares", widget=forms.CheckboxSelectMultiple),
            FieldPanel("arquivo"),
        ], heading="Informações do Conteúdo"),
        MultiFieldPanel([
            FieldPanel("mecanismo_exibicao"),
        ], heading="Mecanismo de Exibição"),
        MultiFieldPanel([
            FieldPanel("authors"),
            FieldPanel("source"),
            FieldPanel("options"),
        ], heading="Metadados Adicionais"),
        MultiFieldPanel([
            FieldPanel("is_approved"),
            FieldPanel("is_featured"),
            FieldPanel("is_site"),
        ], heading="Status e Destaque"),
        MultiFieldPanel([
            FieldPanel("numero_episodio"),
        ], heading="Episódio de Série (RF008)", classname="collapsible collapsed"),
    ]

    # Painéis de promoção (herda de RecursoBasePage -> BasePage que já tem Open Graph)
    promote_panels = RecursoBasePage.promote_panels

    # Configurações de busca
    search_fields = Page.search_fields + [
        # Campos para filtro na busca avançada (RF001)
        index.FilterField("canal_id"),
        index.FilterField("tipo_id"),
        index.FilterField("category_id"),
        index.FilterField("license_id"),
        index.FilterField("componentes_curriculares"),
        index.FilterField("mecanismo_exibicao"),
        index.FilterField("is_approved"),
        index.FilterField("is_featured"),
        index.FilterField("is_site"),
        index.FilterField("first_published_at"),
        # Campos de busca textual
        index.SearchField("title", partial_match=True, boost=2.0),
        index.SearchField("search_description", partial_match=True),
        index.SearchField("authors", partial_match=True),
        index.SearchField("source", partial_match=True),
        index.RelatedFields("tipo", [
            index.SearchField("name", partial_match=True, boost=1.5),
            index.SearchField("description", partial_match=True),
        ]),
        index.RelatedFields("category", [
            index.SearchField("name", partial_match=True, boost=1.5),
        ]),
        index.RelatedFields("license", [
            index.SearchField("name", partial_match=True),
        ]),
        index.RelatedFields("canal", [
            index.SearchField("title", partial_match=True, boost=1.5),
            index.FilterField("id"),
        ]),
        index.RelatedFields("componentes_curriculares", [
            index.SearchField("name", partial_match=True),
            index.FilterField("id"),
            index.RelatedFields("nivel", [
                index.SearchField("name", partial_match=True),
                index.FilterField("id"),
            ]),
            index.RelatedFields("category", [
                index.SearchField("name", partial_match=True),
                index.FilterField("id"),
            ]),
        ]),
    ]

    class Meta:
        verbose_name = "Conteúdo Educacional"
        verbose_name_plural = "Conteúdos Educacionais"

    def get_template(self, request, *args, **kwargs):
        """
        Escolhe o template pelo mecanismo de exibição (decisão fechada).

        O mecanismo de exibição (formato técnico) é distinto da taxonomia
        pedagógica (`tipo`). O template específico é
        ``conteudos/conteudo_page_<mecanismo>.html``. Se o arquivo não existir
        (mecanismo sem template dedicado ainda, ex: `documento_pdf` e
        `download_binario` — criados na Fase 3), cai num template genérico
        ``conteudos/conteudo_page.html`` para nunca disparar
        ``TemplateDoesNotExist`` durante a renderização.
        """
        fallback = "conteudos/conteudo_page.html"
        if self.mecanismo_exibicao:
            especifico = f"conteudos/conteudo_page_{self.mecanismo_exibicao}.html"
            return select_template([especifico, fallback]).template.name
        return fallback

    def clean(self):
        """Validações de nível de model (RN-L3, RN-L5)."""
        super().clean()

        # RN-L3: Validar extensão do arquivo contra o tipo
        if self.arquivo and self.tipo:
            import os
            extensao = os.path.splitext(self.arquivo.name)[1]
            if not self.tipo.validar_extensao(extensao):
                from django.core.exceptions import ValidationError
                formatos = self.tipo.get_formatos_permitidos()
                raise ValidationError({
                    "arquivo": _(
                        f"Extensão '{extensao}' não permitida para o tipo '{self.tipo.name}'. "
                        f"Formatos aceitos: {', '.join(formatos) if formatos else 'nenhum configurado'}."
                    )
                })

        # RN-L5: Validações de campos obrigatórios com regra pedagógica
        # Nota: validação de M2M (componentes_curriculares, tags) deve ser feita no form/serializer
        # pois clean() do model não tem acesso aos dados M2M não salvos

    def save(self, *args, **kwargs):
        """Sobrescreve save para garantir contadores iniciam em zero (RN-L6)."""
        if not self.pk:  # Criação
            self.qt_downloads = 0
            self.qt_access = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# Import forms no final para evitar import circular
from django import forms