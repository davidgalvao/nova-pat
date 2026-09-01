from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AplicativoCategory


class AplicativoCategorySnippetViewSet(SnippetViewSet):
    model = AplicativoCategory
    icon = "folder"
    list_display = ("name", "slug", "parent", "ordem", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("parent"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]


# Registro do snippet com ViewSet customizado (padrão Wagtail 8).
# `AplicativoEducacionalPage` é uma Page e registra-se automaticamente — o antigo
# `AplicativoEducacionalPageModelAdmin` foi removido.
register_snippet(AplicativoCategorySnippetViewSet)