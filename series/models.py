from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model_string

# Import do core para herdar de RecursoBasePage
from core.models import RecursoBasePage


class Serie(RecursoBasePage):
    """
    Série de vídeos estilo streaming (RF008).
    Page independente de Canal — decisão fechada: uma série não pertence
    nem é restrita a um canal específico.
    
    Herda de RecursoBasePage (autor, tags) mas SOBRESCREVE canal para ser opcional
    (serie não pertence a canal). O campo canal herdado fica disponível mas não é obrigatório.
    """

    # Sobrescreve canal para tornar opcional (Serie é independente de Canal)
    canal = models.ForeignKey(
        'canais.CanalPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Canal (não usado para Séries)",
        help_text="Séries são independentes de canal. Este campo não deve ser preenchido.",
    )

    sinopse = models.TextField(
        blank=True,
        verbose_name="Sinopse",
        help_text="Descrição/sinopse da série para exibição na página da série.",
    )

    capa = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Capa da Série",
        help_text="Imagem de capa/banner da série (recomendado: 16:9).",
    )

    # Configuração de árvore de páginas Wagtail
    parent_page_types = ["wagtailcore.Page"]  # Séries ficam no nível superior (filhos de root)
    subpage_types = ["series.Temporada"]

    # Painéis de conteúdo (herda canal, autor, tags de RecursoBasePage)
    # Mas canal não é relevante para Serie — ocultamos no painel
    content_panels = [
        # Painel básico da página (título, slug)
        *Page.content_panels,
        MultiFieldPanel([
            FieldPanel("sinopse"),
            FieldPanel("capa"),
        ], heading="Informações da Série"),
        # Canal, autor, tags herdados mas canal não faz sentido para Serie
        # Mantemos autor/tags para metadados, mas canal pode ser ocultado via JS no admin se necessário
    ]

    # Painéis de promoção (herda de RecursoBasePage -> BasePage: Open Graph)
    promote_panels = RecursoBasePage.promote_panels

    class Meta:
        verbose_name = "Série"
        verbose_name_plural = "Séries"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_context(self, request, *args, **kwargs):
        """
        Adiciona ao contexto as temporadas desta série para templates.
        """
        context = super().get_context(request, *args, **kwargs)
        # Get specific Temporada instances and order by numero
        # We need to get the specific pages first, then order by the specific field
        from django.db.models import Prefetch
        temporadas = list(self.get_children().live().type(Temporada).specific())
        temporadas.sort(key=lambda t: t.numero)
        context["temporadas"] = temporadas
        return context


class Temporada(Page):
    """
    Temporada de uma Série.
    Filha de Serie (parent_page_types = ['series.Serie']).
    Pai de ConteudoPage (episódios).
    """

    numero = models.PositiveSmallIntegerField(
        verbose_name="Número da Temporada",
        help_text="Número ordinal da temporada (1, 2, 3...).",
    )

    sinopse = models.TextField(
        blank=True,
        verbose_name="Sinopse da Temporada",
        help_text="Descrição opcional da temporada.",
    )

    capa = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Capa da Temporada",
        help_text="Imagem de capa da temporada (opcional).",
    )

    # Configuração de árvore de páginas Wagtail
    parent_page_types = ["series.Serie"]
    subpage_types = ["conteudos.ConteudoPage"]  # Episódios são ConteudoPage

    # Painéis de conteúdo
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("numero"),
            FieldPanel("sinopse"),
            FieldPanel("capa"),
        ], heading="Informações da Temporada"),
    ]

    # Painéis de promoção (herda de Page, sem Open Graph extra)
    promote_panels = Page.promote_panels

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"
        ordering = ["numero"]
        # UniqueConstraint com 'path' não funciona com multi-table inheritance (Page)
        # A validação de unicidade por série é feita no clean()

    def __str__(self):
        parent = self.get_parent()
        serie_title = parent.title if parent else "Série desconhecida"
        return f"{serie_title} — Temporada {self.numero}"

    def get_context(self, request, *args, **kwargs):
        """
        Adiciona ao contexto os episódios (ConteudoPage filhos) desta temporada.
        Ordenados por numero_episodio (manual do curador), não por data.
        """
        context = super().get_context(request, *args, **kwargs)
        
        # Episódios são ConteudoPage filhos desta Temporada
        from conteudos.models import ConteudoPage
        context["episodios"] = ConteudoPage.objects.live().child_of(self).order_by("numero_episodio")
        context["serie"] = self.get_parent()  # Serie pai
        
        return context

    def clean(self):
        """Validação: numero deve ser único dentro da mesma Serie."""
        super().clean()
        if self.numero and self.get_parent():
            # Verifica se já existe outra temporada com mesmo numero na mesma serie
            from django.core.exceptions import ValidationError
            irmas = Temporada.objects.sibling_of(self, inclusive=False).filter(numero=self.numero)
            if irmas.exists():
                raise ValidationError({
                    "numero": _("Já existe uma temporada com este número nesta série.")
                })