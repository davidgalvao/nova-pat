from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Comentario, Like, FavoritoConteudo, AvaliacaoConteudo


class ComentarioSnippetViewSet(SnippetViewSet):
    model = Comentario
    icon = "comment"
    menu_label = _("Comentários")
    menu_order = 600
    list_display = ("__str__", "user", "conteudo", "aplicativo", "is_approved", "criado_em")
    list_filter = ("is_approved", "criado_em")
    search_fields = ("body", "user__username", "conteudo__title", "aplicativo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    panels = [
        FieldPanel("user"),
        FieldPanel("conteudo"),
        FieldPanel("aplicativo"),
        FieldPanel("body"),
        FieldPanel("is_approved"),
    ]


class LikeSnippetViewSet(SnippetViewSet):
    model = Like
    icon = "thumb-up"
    menu_label = _("Likes")
    menu_order = 610
    list_display = ("__str__", "user", "conteudo", "aplicativo", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("user__username", "conteudo__title", "aplicativo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    panels = [
        FieldPanel("user"),
        FieldPanel("conteudo"),
        FieldPanel("aplicativo"),
    ]


class FavoritoConteudoSnippetViewSet(SnippetViewSet):
    model = FavoritoConteudo
    icon = "star"
    menu_label = _("Favoritos")
    menu_order = 620
    list_display = ("__str__", "user", "conteudo", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("user__username", "conteudo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    panels = [
        FieldPanel("user"),
        FieldPanel("conteudo"),
    ]


class AvaliacaoConteudoSnippetViewSet(SnippetViewSet):
    model = AvaliacaoConteudo
    icon = "star"
    menu_label = _("Avaliações")
    menu_order = 630
    list_display = ("__str__", "user", "conteudo", "nota", "criado_em")
    list_filter = ("nota", "criado_em")
    search_fields = ("user__username", "conteudo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    panels = [
        FieldPanel("user"),
        FieldPanel("conteudo"),
        FieldPanel("nota"),
    ]


# Registro dos snippets (padrão Wagtail 8).
register_snippet(ComentarioSnippetViewSet)
register_snippet(LikeSnippetViewSet)
register_snippet(FavoritoConteudoSnippetViewSet)
register_snippet(AvaliacaoConteudoSnippetViewSet)