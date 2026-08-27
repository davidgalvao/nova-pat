from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import CanalPage


class CanalPageModelAdmin(ModelAdmin):
    model = CanalPage
    menu_label = _("Canais")
    menu_icon = "site"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "name", "is_active", "first_published_at")
    list_filter = ("is_active",)
    search_fields = ("title", "name", "description")
    list_per_page = 25
    ordering = ("name",)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("name"),
            FieldPanel("slug"),
            FieldPanel("description"),
        ], heading=_("Informações Básicas")),
        
        MultiFieldPanel([
            FieldPanel("is_active"),
            FieldPanel("token"),
            FieldPanel("options"),
        ], heading=_("Configurações")),
        
        MultiFieldPanel([
            FieldPanel("tipos_permitidos", widget=forms.CheckboxSelectMultiple),
            FieldPanel("categorias_componente_permitidas", widget=forms.CheckboxSelectMultiple),
        ], heading=_("Restrições de Conteúdo")),
    ]
    
    def can_create(self, request):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")
    
    def can_edit(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug == "super-admin"


modeladmin_register(CanalPageModelAdmin)