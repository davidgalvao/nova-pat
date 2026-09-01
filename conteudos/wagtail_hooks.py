from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Tipo, Licenca, CategoriaConteudo


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