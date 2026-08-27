from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

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


hooks.register("register_snippet_viewset", NivelEnsinoSnippetViewSet)
hooks.register("register_snippet_viewset", CurricularComponentCategorySnippetViewSet)
hooks.register("register_snippet_viewset", CurricularComponentSnippetViewSet)


@hooks.register("register_admin_menu_item")
def register_curriculo_menu_item():
    return MenuItem(
        _("Currículo"),
        "/admin/snippets/curriculo/",
        classnames="icon icon-pilcrow",
        order=300
    )