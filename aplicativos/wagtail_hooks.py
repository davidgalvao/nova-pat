from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import AplicativoCategory, AplicativoEducacionalPage


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


class AplicativoEducacionalPageModelAdmin(ModelAdmin):
    model = AplicativoEducacionalPage
    menu_label = _("Aplicativos Educacionais")
    menu_icon = "desktop"
    menu_order = 500
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "category", "canal", "is_featured", "first_published_at")
    list_filter = ("category", "canal", "is_featured")
    search_fields = ("title", "description", "url")
    list_per_page = 25
    ordering = ("-first_published_at",)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("category"),
            FieldPanel("url"),
            FieldPanel("description"),
        ], heading=_("Informações Básicas")),
        
        MultiFieldPanel([
            FieldPanel("image"),
            FieldPanel("is_featured"),
        ], heading=_("Exibição")),
        
        MultiFieldPanel([
            FieldPanel("canal"),
            FieldPanel("autor"),
            FieldPanel("tags"),
        ], heading=_("Metadados")),
    ]
    
    def can_create(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin", "coordenador")
    
    def can_edit(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.role and user.role.slug in ("super-admin", "admin"):
            return True
        if user.role and user.role.slug == "coordenador":
            return True
        if obj and obj.autor_id == user.id:
            return True
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


hooks.register("register_snippet_viewset", AplicativoCategorySnippetViewSet)
modeladmin_register(AplicativoEducacionalPageModelAdmin)


@hooks.register("register_admin_menu_item")
def register_aplicativos_menu_item():
    return MenuItem(
        _("Aplicativos Educacionais"),
        "/admin/aplicativos/aplicativoeducacionalpage/",
        classnames="icon icon-desktop",
        order=500
    )