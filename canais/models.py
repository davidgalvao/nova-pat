from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string

# Import do core para herdar de BasePage
from core.models import BasePage
from core.blocks import HomeStreamBlock


class CanalPage(BasePage):
    """
    Página de Canal — agrupador de topo do site (TV Anísio Teixeira, Rádio Anísio Teixeira,
    EMITEC, Recursos Educacionais Abertos, Projetos Artísticos, etc.).
    É Page hierárquica no Wagtail, pai de ConteudoPage e AplicativoEducacionalPage.
    """

    # Campos básicos (além dos herdados de BasePage: og_title, og_description, og_image)
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nome",
        help_text="Nome do canal (ex: 'TV Anísio Teixeira', 'Recursos Educacionais').",
    )

    description = RichTextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição rica do canal para exibição na página do canal.",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Canal ativo e visível na navegação. Desativar para tirar de circulação sem apagar conteúdo histórico.",
    )

    # Token para integração com API externa (oculto na API/serialização)
    # Legado: protected $hidden = ['token'] — nunca expor em endpoint público
    token = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Token de API",
        help_text="Credencial de conexão com API externa (YouTube, Spotify, WordPress, Colaborativus, etc.). NUNCA expor em API pública. Usar campo criptografado em produção.",
    )

    # Opções flexíveis (JSON) — substitui o jsonb 'options' do legado
    # Carrega: cor do canal
    options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Opções extras",
        help_text="JSON para configurações flexíveis (ex: {'cor': '#FF5733'}).",
    )

    # Composição editorial via StreamField (reutiliza blocos da HomePage)
    body = StreamField(
        HomeStreamBlock(),
        blank=True,
        verbose_name="Composição editorial",
        help_text="Blocos que compõem a página do canal. O gestor escolhe os blocos e a ordem. Reutiliza os blocos da HomePage.",
    )

    # Configuração de árvore de páginas Wagtail
    parent_page_types = [
        "wagtailcore.Page"
    ]  # Canais ficam no nível superior (filhos de root)
    subpage_types = [
        "conteudos.ConteudoPage",
        "aplicativos.AplicativoEducacionalPage",
    ]

    # Painéis de conteúdo
    content_panels = BasePage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("slug"),
                FieldPanel("description"),
                FieldPanel("is_active"),
            ],
            heading="Informações Básicas",
        ),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("token"),
                FieldPanel("options"),
            ],
            heading="Integração Externa",
            classname="collapsible collapsed",
            help_text="⚠️ Token NUNCA deve ser exposto em API pública. Em produção, usar campo criptografado.",
        ),
    ]

    # Painéis de promoção (herda de BasePage: Open Graph)
    promote_panels = BasePage.promote_panels

    class Meta:
        verbose_name = "Canal"
        verbose_name_plural = "Canais"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_context(self, request, *args, **kwargs):
        """
        Adiciona ao contexto os conteúdos e aplicativos deste canal para templates.
        Filtra por is_active e ordenação apropriada.
        """
        context = super().get_context(request, *args, **kwargs)

        # Conteúdos deste canal (filhos diretos do tipo ConteudoPage)
        from conteudos.models import ConteudoPage

        context["conteudos"] = (
            ConteudoPage.objects.live().child_of(self).order_by("-first_published_at")
        )

        # Aplicativos deste canal
        try:
            from aplicativos.models import AplicativoEducacionalPage

            context["aplicativos"] = (
                AplicativoEducacionalPage.objects.live()
                .child_of(self)
                .order_by("-first_published_at")
            )
        except ImportError:
            context["aplicativos"] = []

        return context
