from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page
from wagtail.search import index

from typing import Any, Dict

from django.http import HttpRequest
from core.models import RecursoBasePage

# Constante do canal fixo para aplicativos (ADR-002).
# No legado (Laravel), `Aplicativo::CANAL_ID = 9` fixa o canal de todo
# aplicativo educacional por constante no código — não é escolha do usuário
# no formulário. Mantemos o mesmo comportamento, centralizando o valor em uma
# única constante nomeada para eliminar o número mágico inline no save().
# Pendência: confirmar no admin de produção que o canal id=9 é de fato
# "Aplicativos Educacionais" antes de fechar como definitivo.
CANAL_ID = 9

# Fallback por slug mantido como contingência de ambiente (se o canal id=9 não
# existir no banco). Documentado como segunda fonte de verdade — ver ADR-002.
CANAL_SLUG_FALLBACK = "aplicativos-educacionais"


class AplicativoCategory(models.Model):
    """
    Categoria de aplicativo educacional — árvore própria, separada de conteudos.CategoriaConteudo.
    Legado: tabela `aplicativo_categories` com parent_id para hierarquia.
    """

    name = models.CharField(_("nome"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=110, unique=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("categoria pai"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    description = models.TextField(_("descrição"), blank=True)
    ordem = models.PositiveIntegerField(_("ordem"), default=0)
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("categoria de aplicativo")
        verbose_name_plural = _("categorias de aplicativos")
        ordering = ["ordem", "name"]

    def __str__(self) -> str:
        return self.name


class AplicativoEducacionalPage(RecursoBasePage):
    """
    Página de aplicativo educacional — link externo, não arquivo de mídia com player.
    Herda de RecursoBasePage (canal, autor, tags) mas:
    - canal é fixo no id=9 (Aplicativos Educacionais), não editável
    - sem license, sem workflow de aprovação
    - tags: mínimo 3, máximo 15 (diferente de conteudos: 3-50)
    - category: FK para AplicativoCategory (árvore própria)
    - url: obrigatória, validada com checagem de resolução DNS (equivalente a active_url do Laravel)
    - image/ícone: upload, formatos jpeg/png/jpg/svg, até 1MB
    - is_featured: campo booleano (no legado vivia em options.jsonb)
    - qt_access: contador iniciado em 0 (no legado vivia em options.qt_access)
    """

    # Canal fixo — não exposto no formulário, setado automaticamente no save()
    # O campo 'canal' vem de RecursoBasePage (FK para canais.CanalPage, PROTECT)
    # Vamos sobrescrever o comportamento no save() para forçar canal_id=9

    category = models.ForeignKey(
        "aplicativos.AplicativoCategory",
        verbose_name=_("categoria"),
        on_delete=models.PROTECT,
        related_name="aplicativos",
    )

    url = models.URLField(
        _("URL do aplicativo"),
        max_length=500,
        help_text=_("URL externa do aplicativo. Será validada se resolve corretamente (DNS/HTTP)."),
    )

    description = RichTextField(
        _("descrição"),
        features=["bold", "italic", "link", "ol", "ul", "h3", "h4"],
        help_text=_("Mínimo 140 caracteres (validação do legado)."),
    )

    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name=_("imagem/ícone"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Formatos aceitos: jpeg, png, jpg, svg. Tamanho máximo: 1MB."),
    )

    is_featured = models.BooleanField(_("em destaque"), default=False)

    qt_access = models.PositiveIntegerField(
        _("quantidade de acessos"),
        default=0,
        editable=False,
        help_text=_("Contador iniciado em 0, incrementado a cada acesso."),
    )

    # Tags: usa o TaggableManager de RecursoBasePage, mas com validação 3-15
    # O campo 'tags' já existe em RecursoBasePage

    # parent_page_types: apenas CanalPage (canal fixo id=9)
    parent_page_types = ["canais.CanalPage"]
    subpage_types = []

    content_panels = RecursoBasePage.content_panels + [
        FieldPanel("category"),
        FieldPanel("url"),
        FieldPanel("description"),
        FieldPanel("image"),
        FieldPanel("is_featured"),
    ]

    promote_panels = RecursoBasePage.promote_panels + [
        MultiFieldPanel(
            [
                FieldPanel("tags"),
            ],
            heading=_("Tags (3 a 15)"),
        ),
    ]

    # Configurações de busca
    search_fields = Page.search_fields + [
        # Campos para filtro na busca avançada (RF001)
        index.FilterField("canal_id"),
        index.FilterField("category_id"),
        index.FilterField("is_featured"),
        index.FilterField("first_published_at"),
        # Campos de busca textual
        index.SearchField("title", partial_match=True, boost=2.0),
        index.SearchField("search_description", partial_match=True),
        index.SearchField("description", partial_match=True),
        index.RelatedFields("category", [
            index.SearchField("name", partial_match=True, boost=1.5),
            index.FilterField("id"),
        ]),
        index.RelatedFields("canal", [
            index.SearchField("title", partial_match=True, boost=1.5),
            index.FilterField("id"),
        ]),
        index.RelatedFields("tags", [
            index.SearchField("name", partial_match=True),
            index.FilterField("id"),
        ]),
    ]

    class Meta:
        verbose_name = _("aplicativo educacional")
        verbose_name_plural = _("aplicativos educacionais")

    def clean(self) -> None:
        """
        Valida o aplicativo antes de salvar.

        Aplica as regras do legado (``AplicativoRequest::rules()``):
        descrição com no mínimo 140 caracteres (ignorando tags HTML), quantidade
        de tags entre 3 e 15 (somente quando já há ``pk`` e tags), e validação
        de URL ativa e da imagem quando presentes.
        """
        super().clean()

        # Validação de descrição: mínimo 140 caracteres (legado: AplicativoRequest::rules())
        if self.description:
            # Remove tags HTML para contar caracteres reais
            from wagtail.rich_text import get_text_for_indexing

            plain_text = get_text_for_indexing(self.description)
            if len(plain_text) < 140:
                raise ValidationError(
                    {
                        "description": _(
                            "A descrição deve ter no mínimo 140 caracteres (atual: %(count)d)."
                        )
                        % {"count": len(plain_text)}
                    }
                )

        # Validação de tags: 3 a 15 (diferente de conteudos: 3-50)
        # O TaggableManager não valida quantidade no clean, faremos aqui
        # Só valida se o objeto já tem PK (tags só podem ser acessadas com PK)
        # e se tags foram explicitamente adicionadas (count > 0)
        # Isso permite criar a página sem tags inicialmente e adicionar depois
        if self.pk:
            tag_count = self.tags.count()
            if tag_count > 0:
                if tag_count < 3:
                    raise ValidationError(
                        {"tags": _("Mínimo 3 tags obrigatórias (atual: %(count)d).") % {"count": tag_count}}
                    )
                if tag_count > 15:
                    raise ValidationError(
                        {"tags": _("Máximo 15 tags permitidas (atual: %(count)d).") % {"count": tag_count}}
                    )

        # Validação de URL ativa (equivalente a active_url do Laravel)
        # Checa se a URL resolve (DNS + HTTP HEAD/GET)
        if self.url:
            self._validar_url_ativa()

        # Validação de imagem: formatos e tamanho
        if self.image:
            self._validar_imagem()

    def _validar_url_ativa(self) -> None:
        """
        Valida se a URL resolve de fato (DNS + resposta HTTP).

        Equivalente à regra ``active_url`` do Laravel: resolve o domínio via
        DNS e tenta uma requisição HTTP (HEAD, com fallback para GET), lançando
        :class:`ValidationError` se a URL não responder corretamente.

        Raises:
            ValidationError: Se a URL for malformada, o DNS não resolver ou a
                resposta HTTP for maior/igual a 400.
        """
        import socket
        from urllib.parse import urlparse

        import requests

        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError({"url": _("URL inválida.")})

            # Resolução DNS
            socket.gethostbyname(parsed.netloc)

            # Requisição HTTP HEAD (mais leve que GET)
            response = requests.head(self.url, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                # Tenta GET se HEAD falhar (alguns servidores não suportam HEAD)
                response = requests.get(self.url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    raise ValidationError(
                        {
                            "url": _(
                                "A URL não responde corretamente (HTTP %(code)d). Verifique se o link está acessível."
                            )
                            % {"code": response.status_code}
                        }
                    )

        except socket.gaierror:
            raise ValidationError(
                {"url": _("A URL não pôde ser resolvida (DNS). Verifique o domínio.")}
            )
        except requests.RequestException as e:
            raise ValidationError(
                {"url": _("Erro ao validar a URL: %(error)s") % {"error": str(e)}}
            )

    def _validar_imagem(self) -> None:
        """
        Valida formato e tamanho da imagem.

        Limite de 1MB e formatos aceitos ``jpeg``/``png``/``jpg``/``svg``.

        Raises:
            ValidationError: Se a imagem exceder 1MB ou tiver extensão não
                permitida.
        """
        if not self.image or not self.image.file:
            return

        # Tamanho: 1MB = 1024 * 1024 bytes
        max_size = 1024 * 1024
        if self.image.file.size > max_size:
            raise ValidationError(
                {
                    "image": _(
                        "A imagem excede o tamanho máximo de 1MB (atual: %(size).2f MB)."
                    )
                    % {"size": self.image.file.size / (1024 * 1024)}
                }
            )

        # Formato: verificar extensão do arquivo original
        allowed_extensions = {"jpeg", "jpg", "png", "svg"}
        if self.image.file.name:
            ext = self.image.file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    {
                        "image": _(
                            "Formato de imagem não permitido. Use: %(allowed)s."
                        )
                        % {"allowed": ", ".join(allowed_extensions)}
                    }
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Sobrescreve ``save`` para forçar canal fixo e contador inicial.

        1. Força ``canal_id=CANAL_ID`` (Aplicativos Educacionais), não editável
           pelo usuário (com fallback para ``CANAL_SLUG_FALLBACK``).
        2. Garante ``qt_access=0`` na criação (já é padrão, mas reforça).
        3. Não valida tags aqui (já feita no ``clean``).

        Args:
            *args, **kwargs: Argumentos repassados ao ``super().save()``.

        Raises:
            ValidationError: Se nenhum canal fixo (id=9 ou slug de contingência)
                existir no banco.
        """
        # Forçar canal fixo (CANAL_ID)
        # Importa aqui para evitar circular import
        from canais.models import CanalPage

        try:
            canal_fixo = CanalPage.objects.get(pk=CANAL_ID)
            self.canal = canal_fixo
        except CanalPage.DoesNotExist:
            # Se o canal CANAL_ID não existe, tenta buscar pelo slug de contingência
            # ou levanta erro claro
            try:
                canal_fixo = CanalPage.objects.get(slug=CANAL_SLUG_FALLBACK)
                self.canal = canal_fixo
            except CanalPage.DoesNotExist:
                raise ValidationError(
                    _(
                        "Canal fixo para aplicativos (id=%(id)d ou slug='%(slug)s') não encontrado. "
                        "Crie o canal 'Aplicativos Educacionais' antes de adicionar aplicativos."
                    )
                    % {"id": CANAL_ID, "slug": CANAL_SLUG_FALLBACK}
                )

        # qt_access já tem default=0, mas garantimos na criação
        if not self.pk:
            self.qt_access = 0

        super().save(*args, **kwargs)

    def get_context(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Adiciona a instância do aplicativo ao contexto do template.

        Disponibiliza `aplicativo` no template da página para acesso direto aos
        campos do model (ex: `url`, `description`, `image`).

        Args:
            request: HttpRequest da requisição.
            *args, **kwargs: Argumentos adicionais repassados ao super().

        Returns:
            dict de contexto com a chave `aplicativo`.
        """
        context = super().get_context(request, *args, **kwargs)
        context["aplicativo"] = self
        return context

    def __str__(self) -> str:
        return self.title