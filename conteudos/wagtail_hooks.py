from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Tipo, Licenca, CategoriaConteudo, ConteudoPage
from series.models import Serie


class TipoSnippetViewSet(SnippetViewSet):
    model = Tipo
    icon = "media"
    list_display = ("name", "slug", "is_active", "ordem")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("options"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]


class LicencaSnippetViewSet(SnippetViewSet):
    model = Licenca
    icon = "doc-full"
    list_display = ("name", "slug", "parent", "is_active", "ordem")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("url"),
        FieldPanel("parent"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]


class CategoriaConteudoSnippetViewSet(SnippetViewSet):
    model = CategoriaConteudo
    icon = "folder"
    list_display = ("name", "slug", "canal", "parent", "is_active", "ordem")
    list_filter = ("is_active", "canal", "parent")
    search_fields = ("name", "slug")
    ordering = ("canal", "ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("canal"),
        FieldPanel("parent"),
        FieldPanel("is_active"),
        FieldPanel("ordem"),
    ]


# Registro dos snippets com ViewSet customizado (padrão Wagtail 8).
# `ConteudoPage` é uma Page e registra-se automaticamente — o antigo
# `ConteudoPageModelAdmin` foi removido.
register_snippet(TipoSnippetViewSet)
register_snippet(LicencaSnippetViewSet)
register_snippet(CategoriaConteudoSnippetViewSet)


class CadastroConteudoMenuItem(MenuItem):
    """
    Atalho "Gestão de Conteúdos" na raiz da barra lateral do admin.

    Leva ao formulário de criação de `ConteudoPage`. O gestor escolhe o
    canal no dropdown do próprio formulário (decisão editorial dele, não
    do código). URL gerada via reverse() de rota nomeada — NUNCA
    dependente de dados em banco, NUNCA retorna string vazia.
    """

    def __init__(self, order=200):
        # Initialize all attributes manually to avoid parent's url setter
        self.label = _("Gestão de Conteúdos")
        self.name = "gestao-conteudos"
        self.icon_name = "doc-full-inverse"
        self.order = order
        self.classname = ""  # Parent expects 'classname' (singular)
        self.attrs = {}
        self._url = ""  # Set directly to avoid property conflict

    def is_shown(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(
            permissions__codename="access_admin"
        ).exists()

    def get_url(self, request=None):
        """
        Retorna a URL da view dedicada de cadastro de conteúdo de mídia
        (fora do fluxo de sub-página do Wagtail).
        
        O item de menu "Gestão de Conteúdos" leva agora a um formulário
        próprio de cadastro, onde o gestor escolhe o canal como metadado
        de publicação (não como pai hierárquico obrigatório).
        """
        return reverse("conteudos:cadastro_conteudo")

    @property
    def url(self):
        """Property required by Wagtail's MenuItem base class."""
        return self.get_url()


@hooks.register("register_admin_menu_item")
def register_cadastro_conteudo_menu_item():
    return CadastroConteudoMenuItem()


class SeriesMenuItem(MenuItem):
    """
    Item de menu "Séries" na barra lateral do admin.
    
    Leva à listagem de séries (RF008), onde o gestor pode
    editar séries existentes ou adicionar episódios.
    """

    def __init__(self, order=210):
        self.label = _("Séries")
        self.name = "series"
        self.icon_name = "media"
        self.order = order
        self.classname = ""
        self.attrs = {}
        self._url = ""

    def is_shown(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(
            permissions__codename="access_admin"
        ).exists()

    def get_url(self, request=None):
        return reverse("conteudos:lista_series")

    @property
    def url(self):
        return self.get_url()


@hooks.register("register_admin_menu_item")
def register_series_menu_item():
    return SeriesMenuItem()