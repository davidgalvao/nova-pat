from django.utils.translation import gettext_lazy as _
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