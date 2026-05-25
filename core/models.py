from django.db import models
from wagtail.models import Page, Site
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model_string

class BasePage(Page):
    """
    Classe abstrata de onde todas as outras páginas devem herdar.
    Contém campos comuns que todas as páginas do site devem possuir.
    """
    
    og_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Título Redes Sociais",
        help_text="Título personalizado para Facebook, Instagram e WhatsApp. Se vazio, usa o título da página."
    )

    og_description = models.TextField(
        blank=True,
        verbose_name="Descrição Redes Sociais",
        help_text="Descrição curta para compartilhamento. Se vazio, usa a descrição de busca (SEO)."
    )

    og_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Imagem Redes Sociais",
        help_text="Imagem que aparecerá no card de compartilhamento (Recomendado: 1200x630px)."
    )
    
    custom_body_class = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Classe CSS do Body",
        help_text="Classe CSS opcional aplicada à tag <body>."
    )

    hide_header = models.BooleanField(default=False, verbose_name="Esconder Header")
    hide_footer = models.BooleanField(default=False, verbose_name="Esconder Footer")

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("hide_header"),
            FieldPanel("hide_footer"),
            FieldPanel("custom_body_class"),
        ], heading="Configurações de Layout", classname="collapsible collapsed"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([
            FieldPanel("og_title"),
            FieldPanel("og_description"),
            FieldPanel("og_image"),
        ], heading="Redes Sociais (Open Graph)"),
    ]

    @property
    def social_title(self):
        """Retorna o título para redes sociais com fallback para o título SEO ou título da página."""
        return self.og_title or self.seo_title or self.title

    @property
    def social_description(self):
        """Retorna a descrição para redes sociais com fallback para a descrição de busca."""
        return self.og_description or self.search_description

    def get_context(self, request):
        context = super().get_context(request)
        # Exemplo: Adicionar configurações globais ao contexto se necessário
        # context['site_settings'] = MySettings.for_request(request)
        return context

    @property
    def canonical_url(self):
        """Retorna a URL absoluta para a tag canonical."""
        return self.get_full_url()

    class Meta:
        abstract = True