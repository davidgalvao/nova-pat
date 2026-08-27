from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import Tipo, Licenca, CategoriaConteudo, ConteudoPage


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


class ConteudoPageModelAdmin(ModelAdmin):
    model = ConteudoPage
    menu_label = _("Conteúdos")
    menu_icon = "doc-full"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "tipo", "category", "canal", "is_approved", "is_featured", "first_published_at")
    list_filter = ("tipo", "category", "canal", "is_approved", "is_featured")
    search_fields = ("title", "search_description", "authors", "source")
    list_export = ("title", "tipo", "category", "canal", "is_approved", "is_featured", "first_published_at")
    list_per_page = 25
    ordering = ("-first_published_at",)
    
    # Panels para edição
    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("tipo"),
            FieldPanel("category"),
            FieldPanel("license"),
        ], heading=_("Informações Básicas")),
        
        MultiFieldPanel([
            FieldPanel("canal"),
            FieldPanel("autor"),
        ], heading=_("Metadados")),
        
        MultiFieldPanel([
            FieldPanel("componentes_curriculares", widget=forms.CheckboxSelectMultiple),
            FieldPanel("tags"),
        ], heading=_("Taxonomias")),
        
        MultiFieldPanel([
            FieldPanel("arquivo"),
            FieldPanel("capa"),
        ], heading=_("Mídia")),
        
        MultiFieldPanel([
            FieldPanel("authors"),
            FieldPanel("source"),
            FieldPanel("options"),
            FieldPanel("numero_episodio"),
        ], heading=_("Informações Adicionais")),
        
        MultiFieldPanel([
            FieldPanel("is_approved"),
            FieldPanel("is_featured"),
            FieldPanel("is_site"),
        ], heading=_("Status")),
    ]
    
    # Inspeção de permissão baseada em role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filtros adicionais podem ser aplicados aqui baseados no role do usuário
        return qs
    
    def can_create(self, request):
        # RN-L1: só super-admin, admin, coordenador podem criar
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin", "coordenador")
    
    def can_edit(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        # Super-admin e admin podem editar tudo
        if user.role and user.role.slug in ("super-admin", "admin"):
            return True
        # Coordenador pode editar
        if user.role and user.role.slug == "coordenador":
            return True
        # Autor pode editar seu próprio conteúdo
        if obj and obj.autor_id == user.id:
            return True
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        # Só super-admin e admin podem deletar
        return user.role and user.role.slug in ("super-admin", "admin")


# Registrar snippets
hooks.register("register_snippet_viewset", TipoSnippetViewSet)
hooks.register("register_snippet_viewset", LicencaSnippetViewSet)
hooks.register("register_snippet_viewset", CategoriaConteudoSnippetViewSet)

# Registrar ModelAdmin
modeladmin_register(ConteudoPageModelAdmin)