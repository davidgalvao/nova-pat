from django.db import models
from django.conf import settings
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from taggit.managers import TaggableManager


class FlexLayoutMixin(models.Model):
    """
    Mixin abstrato para páginas que precisam de controle sobre header, footer
    e classe CSS personalizada no body. Útil para landing pages e páginas
    avulsas que fogem do layout padrão do site.

    **Decisão (D5, fechada)**: mantido intencionalmente mesmo sem uso atual.
    É abstrato (não gera tabela) e documenta a intenção de arquitetura de
    suportar landing pages com layout flexível. **Não aplicar em conteúdo**
    (`ConteudoPage`/`AplicativoEducacionalPage`) — esconder header/footer não
    faz sentido de negócio para recurso educacional. Ver `core/CLAUDE.md` e
    `docs/adr/README.md` (seção D5). Se nenhuma landing page existir em ~6
    meses, reavaliar a remoção.
    """

    custom_body_class = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Classe CSS do Body",
        help_text="Classe CSS opcional aplicada à tag <body>."
    )

    hide_header = models.BooleanField(default=False, verbose_name="Esconder Header")
    hide_footer = models.BooleanField(default=False, verbose_name="Esconder Footer")

    content_panels = [
        MultiFieldPanel([
            FieldPanel("hide_header"),
            FieldPanel("hide_footer"),
            FieldPanel("custom_body_class"),
        ], heading="Configurações de Layout", classname="collapsible collapsed"),
    ]

    class Meta:
        abstract = True


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

    @property
    def canonical_url(self):
        """Retorna a URL absoluta para a tag canonical."""
        return self.get_full_url()

    class Meta:
        abstract = True


class RecursoBasePage(BasePage):
    """
    Classe abstrata base para recursos educacionais compartilhados entre
    `ConteudoPage` (app `conteudos`) e `AplicativoEducacionalPage` (app `aplicativos`).

    Campos confirmados no schema legado como compartilhados:
    - `canal` (FK para `CanalPage`, app `canais`) — comportamento difere:
      * Em `conteudos`: escolha real do autor/curador
      * Em `aplicativos`: fixo por constante (CANAL_ID = 9, "Aplicativos Educacionais")
    - `autor` (FK para usuário publicador, `user_id` no legado)
    - `tags` — mesma taxonomia global (`django-taggit`), pivots diferentes
      (`conteudo_tag` vs `aplicativo_tag` no legado)
    """

    canal = models.ForeignKey(
        'canais.CanalPage',
        on_delete=models.PROTECT,
        verbose_name="Canal",
        help_text="Canal ao qual este recurso pertence."
    )

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Autor",
        related_name='%(class)s_autor',
        help_text="Usuário que publicou este recurso."
    )

    tags = TaggableManager(
        blank=True,
        verbose_name="Tags",
        help_text="Tags para categorização e busca."
    )

    content_panels = BasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel("canal"),
            FieldPanel("autor"),
            FieldPanel("tags"),
        ], heading="Informações do Recurso"),
    ]

    class Meta:
        abstract = True
