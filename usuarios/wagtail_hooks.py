from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Role, UserCanal


class RoleSnippetViewSet(SnippetViewSet):
    model = Role
    icon = "group"
    menu_label = _("Papéis (Roles)")
    menu_order = 700
    list_display = ("name", "slug", "ordem", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("slug"),
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]


class UserCanalSnippetViewSet(SnippetViewSet):
    model = UserCanal
    icon = "link"
    menu_label = _("Usuários × Canais")
    menu_order = 720
    list_display = ("user", "canal", "criado_em")
    list_filter = ("canal", "criado_em")
    search_fields = ("user__username", "user__email", "canal__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    panels = [
        FieldPanel("user"),
        FieldPanel("canal"),
    ]


# Registro dos snippets (padrão Wagtail 8).
# `User` é o AUTH_USER_MODEL e é gerenciado pelo `wagtail.users` — o antigo
# `UserModelAdmin` foi removido.
register_snippet(RoleSnippetViewSet)
register_snippet(UserCanalSnippetViewSet)


class ExpurgarInativosMenuItem(MenuItem):
    """
    Item de menu "Retenção de usuários inativos" no admin.

    Leva à página de retenção de usuários inativos (card NOVAPAT-62),
    renderizada com o template base do admin do Wagtail (mesma aparência
    do painel). Visível apenas ao nível mais alto de admin
    (papel ``super-admin``).
    """

    def __init__(self, order=850):
        self.label = _("Retenção de usuários inativos")
        self.name = "expurgar-usuarios-inativos"
        self.icon_name = "delete"
        self.order = order
        self.classname = ""
        self.attrs = {}
        self._url = ""

    def is_shown(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_super_admin", False)

    def get_url(self, request=None):
        return reverse("usuarios:expurgar_inativos")

    @property
    def url(self):
        """Property required by Wagtail's MenuItem base class."""
        return self.get_url()


@hooks.register("register_admin_menu_item")
def register_expurgar_inativos_menu_item():
    """Registra o item de menu de retenção de usuários inativos."""
    return ExpurgarInativosMenuItem()
