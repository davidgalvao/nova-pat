from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import NivelEnsino, CurricularComponentCategory, CurricularComponent


class NivelEnsinoSnippetViewSet(SnippetViewSet):
    model = NivelEnsino
    icon = "pilcrow"
    list_display = ("name", "slug", "ordem", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]


class CurricularComponentCategorySnippetViewSet(SnippetViewSet):
    model = CurricularComponentCategory
    icon = "folder"
    list_display = ("name", "slug", "ordem", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering = ("ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]


class CurricularComponentSnippetViewSet(SnippetViewSet):
    model = CurricularComponent
    icon = "doc-full"
    list_display = ("name", "slug", "category", "nivel", "ordem", "is_active")
    list_filter = ("is_active", "category", "nivel")
    search_fields = ("name", "slug", "description")
    ordering = ("nivel__ordem", "category__ordem", "ordem", "name")
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("category"),
        FieldPanel("nivel"),
        FieldPanel("description"),
        FieldPanel("ordem"),
        FieldPanel("is_active"),
    ]


class CurriculoSnippetViewSetGroup(SnippetViewSetGroup):
    items = (
        NivelEnsinoSnippetViewSet,
        CurricularComponentCategorySnippetViewSet,
        CurricularComponentSnippetViewSet,
    )
    menu_label = _("Currículo")
    menu_icon = "pilcrow"
    menu_order = 300


register_snippet(CurriculoSnippetViewSetGroup)