from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail_modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from .models import Serie, Temporada


class SerieModelAdmin(ModelAdmin):
    model = Serie
    menu_label = _("Séries")
    menu_icon = "list-ol"
    menu_order = 400
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "canal", "autor", "first_published_at")
    list_filter = ("canal",)
    search_fields = ("title", "sinopse")
    list_per_page = 25
    ordering = ("-first_published_at",)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("sinopse"),
            FieldPanel("capa"),
        ], heading=_("Informações da Série")),
        
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


class TemporadaModelAdmin(ModelAdmin):
    model = Temporada
    menu_label = _("Temporadas")
    menu_icon = "order"
    menu_order = 410
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("__str__", "serie", "numero")
    list_filter = ("serie",)
    search_fields = ("serie__title", "sinopse")
    list_per_page = 25
    ordering = ("serie", "numero")
    
    panels = [
        MultiFieldPanel([
            FieldPanel("serie"),
            FieldPanel("numero"),
            FieldPanel("sinopse"),
            FieldPanel("capa"),
        ], heading=_("Informações da Temporada")),
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
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


class SeriesModelAdminGroup(ModelAdminGroup):
    items = (
        SerieModelAdmin,
        TemporadaModelAdmin,
    )
    menu_label = _("Séries")
    menu_icon = "list-ol"
    menu_order = 400


modeladmin_register(SeriesModelAdminGroup)