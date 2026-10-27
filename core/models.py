from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.conf import settings
from wagtail.admin.widgets.chooser import AdminPageChooser
from wagtail.models import Page
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from taggit.managers import TaggableManager


def validar_url_relativa_ou_absoluta(valor):
    """
    Valida que o valor seja um caminho relativo (ex.: /acessibilidade) ou uma
    URL absoluta (http:// ou https://). Rejeita strings vazias só quando o
    campo não permite blank.
    """
    if not valor:
        return
    # Caminho relativo do próprio site é aceito.
    if valor.startswith("/"):
        return
    # URL absoluta com esquema http/https também é aceita.
    try:
        URLValidator(schemes=["http", "https"])(valor)
    except ValidationError:
        raise ValidationError(
            "Informe um caminho relativo (ex.: /acessibilidade) "
            "ou uma URL absoluta (http:// ou https://)."
        )


class FlexLayoutMixin(models.Model):
    """
    Mixin abstrato para páginas que precisam de controle sobre header, footer
    e classe CSS personalizada no body. Útil para landing pages e páginas
    avulsas que fogem do layout padrão do site.

    **Decisão (D5, fechada)**: mantido intencionalmente mesmo sem uso atual.
    É abstrato (não gera tabela) e documenta a intenção de arquitetura de
    suportar landing pages com layout flexível. **Não aplicar em conteúdo**
    (`ConteudoPage`/`AplicativoEducacionalPage`) — esconder header/footer não
    faz sentido de negócio para recurso educacional. Ver `core/ARCHITECTURE.md` e
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


class NavigationItem(models.Model):
    """
    Snippet para itens de navegação editáveis no admin (header e footer).

    Cada item pode apontar para uma página do Wagtail (`page`) ou para uma
    URL externa/arbitrária (`link_url`). Se `page` estiver preenchida, ela tem
    prioridade sobre `link_url`. A ordenação é controlada por `sort_order`.

    **Decisão de desambiguação**: o campo `position` (choices `header`/`footer`)
    é o discriminador explícito de onde o item deve aparecer — nunca inferimos
    isso a partir de IDs ou de outros campos (ver "Models e dados" em `AGENTS.md`).
    """

    POSITION_HEADER = "header"
    POSITION_FOOTER = "footer"

    POSITION_CHOICES = [
        (POSITION_HEADER, "Header (menu superior)"),
        (POSITION_FOOTER, "Footer (menu institucional)"),
    ]

    title = models.CharField(
        max_length=100,
        verbose_name="Título",
        help_text="Texto exibido no link de navegação."
    )
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        default=POSITION_HEADER,
        verbose_name="Posição",
        help_text="Onde este item deve aparecer: menu superior (header) ou rodapé (footer)."
    )
    page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Página",
        help_text="Página interna do site. Se preenchida, tem prioridade sobre a URL externa."
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="URL externa",
        help_text="URL externa ou caminho arbitrário. Usada apenas se 'Página' estiver vazia."
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição (menor aparece primeiro)."
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="Item Pai (Submenu de)",
        help_text="Se preenchido, este item vira um submenu do item pai, permitindo hierarquia multinível."
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("position"),
        FieldPanel("parent"),
        FieldPanel("page"),
        FieldPanel("link_url"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["position", "sort_order", "title"]
        verbose_name = "Item de Navegação"
        verbose_name_plural = "Itens de Navegação"

    def __str__(self) -> str:
        return self.title

    @property
    def url(self) -> str:
        """
        Retorna a URL de destino do item.

        Prioriza a página do Wagtail (`page.url`); caso contrário, usa
        `link_url`. Nunca retorna string vazia se ambos estiverem preenchidos.
        """
        if self.page_id:
            return self.page.url
        return self.link_url

    @property
    def get_children(self):
        """
        Retorna os subitens (filhos) deste item, ordenados.

        Usa o reverse manager `children` (related_name da FK auto-referencial
        `parent`). A hierarquia é derivada exclusivamente do campo explícito
        `parent` (ver "Models e dados" em `AGENTS.md`). Nome sem underscore
        para ser acessível no template Django (que bloqueia atributos com `_`).
        """
        return self.children.all().order_by("sort_order", "title")


@register_setting
class SiteSettings(BaseSiteSetting):
    """
    Configurações editáveis do site (nome e logotipo) acessíveis no admin do
    Wagtail, em "Configurações" → "Configurações do site".

    Permite que gestores alterem o nome do site e façam upload de um logotipo,
    sem editar código nem depender do `WAGTAIL_SITE_NAME` estático em
    `mysite/settings/base.py`. O nome salvo aqui também é gravado em
    `Site.site_name` do site padrão, mantendo paridade com o comportamento
    legado e com o título do navegador/SEO.
    """

    site_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome do site",
        help_text="Nome exibido no cabeçalho e no título do navegador.",
    )

    logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Logotipo",
        help_text="Imagem de logotipo exibida no cabeçalho do site.",
    )

    link_acessibilidade_url = models.CharField(
        max_length=500,
        default="/acessibilidade",
        blank=True,
        verbose_name="URL do link 'Acessibilidade'",
        help_text="Caminho relativo (ex.: /acessibilidade) ou URL absoluta (http:// ou https://).",
        validators=[validar_url_relativa_ou_absoluta],
    )
    link_acessibilidade_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Página (Acessibilidade)",
        help_text="Se preenchida, tem prioridade sobre o campo URL acima.",
    )
    link_acessibilidade_texto = models.CharField(
        max_length=100,
        default="Acessibilidade",
        blank=True,
        verbose_name="Texto do link 'Acessibilidade'",
        help_text="Texto exibido no link 'Acessibilidade' da toolbar do site.",
    )
    link_privacidade_url = models.CharField(
        max_length=500,
        default="/politica-privacidade",
        blank=True,
        verbose_name="URL do link 'Política de privacidade'",
        help_text="Caminho relativo (ex.: /politica-privacidade) ou URL absoluta (http:// ou https://).",
        validators=[validar_url_relativa_ou_absoluta],
    )
    link_privacidade_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Página (Política de privacidade)",
        help_text="Se preenchida, tem prioridade sobre o campo URL acima.",
    )
    link_privacidade_texto = models.CharField(
        max_length=100,
        default="Política de privacidade",
        blank=True,
        verbose_name="Texto do link 'Política de privacidade'",
        help_text="Texto exibido no link 'Política de privacidade' da toolbar do site.",
    )
    link_acesso_informacao_url = models.CharField(
        max_length=500,
        default="https://www.ba.gov.br/comunicacao/lei-de-acesso-a-informacao",
        blank=True,
        verbose_name="URL do link 'Acesso à Informação'",
        help_text="Caminho relativo (ex.: /acesso-informacao) ou URL absoluta (http:// ou https://).",
        validators=[validar_url_relativa_ou_absoluta],
    )
    link_acesso_informacao_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Página (Acesso à Informação)",
        help_text="Se preenchida, tem prioridade sobre o campo URL acima.",
    )
    link_acesso_informacao_texto = models.CharField(
        max_length=100,
        default="Acesso à Informação",
        blank=True,
        verbose_name="Texto do link 'Acesso à Informação'",
        help_text="Texto exibido no link 'Acesso à Informação' da toolbar do site.",
    )

    def url_acessibilidade(self) -> str:
        """
        Retorna a URL efetiva do link 'Acessibilidade'.

        Prioriza a página selecionada (link_acessibilidade_page.url);
        caso contrário, usa o campo URL direto (link_acessibilidade_url).
        """
        if self.link_acessibilidade_page_id:
            return self.link_acessibilidade_page.url
        return self.link_acessibilidade_url or "/acessibilidade"

    def url_privacidade(self) -> str:
        """
        Retorna a URL efetiva do link 'Política de privacidade'.

        Prioriza a página selecionada (link_privacidade_page.url);
        caso contrário, usa o campo URL direto (link_privacidade_url).
        """
        if self.link_privacidade_page_id:
            return self.link_privacidade_page.url
        return self.link_privacidade_url or "/politica-privacidade"

    def url_acesso_informacao(self) -> str:
        """
        Retorna a URL efetiva do link 'Acesso à Informação'.

        Prioriza a página selecionada (link_acesso_informacao_page.url);
        caso contrário, usa o campo URL direto (link_acesso_informacao_url).
        """
        if self.link_acesso_informacao_page_id:
            return self.link_acesso_informacao_page.url
        return self.link_acesso_informacao_url or (
            "https://www.ba.gov.br/comunicacao/lei-de-acesso-a-informacao"
        )

    panels = [
        FieldPanel("site_name"),
        FieldPanel("logo"),
        MultiFieldPanel(
            [
                FieldPanel("link_acessibilidade_page", widget=AdminPageChooser),
                FieldPanel("link_acessibilidade_url"),
                FieldPanel("link_acessibilidade_texto"),
                FieldPanel("link_privacidade_page", widget=AdminPageChooser),
                FieldPanel("link_privacidade_url"),
                FieldPanel("link_privacidade_texto"),
                FieldPanel("link_acesso_informacao_page", widget=AdminPageChooser),
                FieldPanel("link_acesso_informacao_url"),
                FieldPanel("link_acesso_informacao_texto"),
            ],
            heading="Links da toolbar",
            classname="collapsible collapsed links-da-toolbar-separators",
        ),
    ]

    class Meta:
        verbose_name = "Configurações do site"
        verbose_name_plural = "Configurações do site"

    def save(self, *args, **kwargs):
        """
        Persiste as configurações e sincroniza o nome com `Site.site_name`
        do site padrão do Wagtail, para que o nome editado reflita no título
        do navegador e em `<meta property="og:site_name">`.
        """
        super().save(*args, **kwargs)
        from wagtail.models import Site

        default_site = Site.objects.filter(is_default_site=True).first()
        if default_site and self.site_name:
            default_site.site_name = self.site_name
            default_site.save(update_fields=["site_name"])

    def __str__(self) -> str:
        return self.site_name or "Configurações do site"


class RedeSocial(models.Model):
    """
    Rede social configurável na toolbar do site, gerenciada via
    SiteSettings → seção "Redes sociais da toolbar".

    Cada registro representa um link com ícone branco que aparece na toolbar,
    com contraste sobre o fundo azul da barra (NOVAPAT-68).

    A rede social é identificada automaticamente pelo endereço (URL): ao salvar,
    o sistema detecta se é Instagram, YouTube, Facebook ou Flickr e preenche
    automaticamente o tipo, o nome e o ícone correspondente (classe Font Awesome
    em branco, mesma abordagem leve usada pelos demais ícones do site).
    """

    # Redes sociais suportadas com detecção automática de ícone.
    TIPO_REDE_INSTAGRAM = "instagram"
    TIPO_REDE_YOUTUBE = "youtube"
    TIPO_REDE_FACEBOOK = "facebook"
    TIPO_REDE_FLICKR = "flickr"

    TIPO_REDE_CHOICES = [
        (TIPO_REDE_INSTAGRAM, "Instagram"),
        (TIPO_REDE_YOUTUBE, "YouTube"),
        (TIPO_REDE_FACEBOOK, "Facebook"),
        (TIPO_REDE_FLICKR, "Flickr"),
    ]

    # Nome exibido automaticamente para cada tipo detectado.
    NOME_POR_TIPO = {
        TIPO_REDE_INSTAGRAM: "Instagram",
        TIPO_REDE_YOUTUBE: "YouTube",
        TIPO_REDE_FACEBOOK: "Facebook",
        TIPO_REDE_FLICKR: "Flickr",
    }

    # Classe Font Awesome por tipo (ícones brancos via ``text-white`` no template).
    ICONE_POR_TIPO = {
        TIPO_REDE_INSTAGRAM: "fa-instagram",
        TIPO_REDE_YOUTUBE: "fa-youtube",
        TIPO_REDE_FACEBOOK: "fa-facebook",
        TIPO_REDE_FLICKR: "fa-flickr",
    }

    # Padrões de detecção automática por URL.
    DETECAO_POR_URL = [
        (TIPO_REDE_INSTAGRAM, ("instagram.com",)),
        (TIPO_REDE_YOUTUBE, ("youtube.com", "youtu.be")),
        (TIPO_REDE_FACEBOOK, ("facebook.com",)),
        (TIPO_REDE_FLICKR, ("flickr.com",)),
    ]

    site_settings = models.ForeignKey(
        SiteSettings,
        on_delete=models.CASCADE,
        related_name="redes_sociais",
        verbose_name="Configurações do site",
    )

    tipo_rede = models.CharField(
        max_length=20,
        choices=TIPO_REDE_CHOICES,
        verbose_name="Selecione a rede social",
        help_text="Escolha a rede social. O ícone e o nome são preenchidos automaticamente.",
    )

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da rede social",
        help_text="Preenchido automaticamente com base na rede social selecionada.",
    )

    url = models.URLField(
        verbose_name="Endereço da rede social",
        help_text="Link do perfil da rede social "
        "(ex.: https://www.instagram.com/novapat).",
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Desmarque para ocultar esta rede social da toolbar sem excluí-la.",
    )

    sort_order = models.IntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição na toolbar (menor aparece primeiro).",
    )

    panels = [
        FieldPanel("tipo_rede"),
        FieldPanel("url"),
        FieldPanel("ativo"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Rede social"
        verbose_name_plural = "Redes sociais"
        ordering = ["sort_order", "nome"]

    def detectar_tipo_por_url(self, url: str) -> str | None:
        """
        Identifica a rede social pelo endereço (URL).

        Retorna o código do tipo (ex.: ``instagram``) quando o domínio da URL
        corresponde a uma rede suportada; senão, retorna ``None``.
        """
        if not url:
            return None
        url_lower = url.lower()
        for tipo, dominios in self.DETECAO_POR_URL:
            if any(dominio in url_lower for dominio in dominios):
                return tipo
        return None

    @property
    def icone_classe_efetiva(self) -> str | None:
        """
        Retorna a classe Font Awesome do ícone a ser renderizada na toolbar.

        O ícone é inferido da rede social selecionada e renderizado em branco
        (``text-white``) no template.
        """
        return self.ICONE_POR_TIPO.get(self.tipo_rede)

    @property
    def icone_url(self) -> str | None:
        """Sempre None, pois não há upload de ícone; o ícone é automático."""
        return None

    def save(self, *args, **kwargs):
        """
        Persiste a rede social, preenchendo automaticamente tipo, nome e
        associando às configurações do site do site default.

        - Detecta o tipo pela URL; se não corresponder a nenhuma rede suportada,
          levanta ``ValidationError``.
        - Preenche o nome automaticamente com base no tipo detectado.
        - Associa ao ``SiteSettings`` do site default quando não informado.
        """
        from django.core.exceptions import ValidationError
        from wagtail.models import Site

        tipo_detectado = self.detectar_tipo_por_url(self.url)
        if tipo_detectado is None:
            raise ValidationError(
                {
                    "url": "Endereço não reconhecido. "
                    "Aceita Instagram, YouTube, Facebook ou Flickr."
                }
            )
        self.tipo_rede = tipo_detectado
        self.nome = self.NOME_POR_TIPO[tipo_detectado]

        if self.site_settings_id is None:
            default_site = Site.objects.filter(is_default_site=True).first()
            if default_site:
                from core.models import SiteSettings

                site_settings, _ = SiteSettings.objects.get_or_create(
                    site=default_site,
                )
                self.site_settings = site_settings

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nome
