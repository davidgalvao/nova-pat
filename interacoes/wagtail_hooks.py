from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import Comentario, Like, FavoritoConteudo, AvaliacaoConteudo


class ComentarioModelAdmin(ModelAdmin):
    model = Comentario
    menu_label = _("Comentários")
    menu_icon = "comment"
    menu_order = 600
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("__str__", "user", "conteudo", "aplicativo", "is_approved", "criado_em")
    list_filter = ("is_approved", "criado_em")
    search_fields = ("body", "user__username", "conteudo__title", "aplicativo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    readonly_fields = ("user", "conteudo", "aplicativo", "body", "criado_em")
    
    def can_create(self, request):
        return False  # Comentários são criados via frontend, não admin
    
    def can_edit(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin", "coordenador")
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


class LikeModelAdmin(ModelAdmin):
    model = Like
    menu_label = _("Likes")
    menu_icon = "thumb-up"
    menu_order = 610
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("__str__", "user", "conteudo", "aplicativo", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("user__username", "conteudo__title", "aplicativo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    readonly_fields = ("user", "conteudo", "aplicativo", "criado_em")
    
    def can_create(self, request):
        return False
    
    def can_edit(self, request, obj=None):
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


class FavoritoConteudoModelAdmin(ModelAdmin):
    model = FavoritoConteudo
    menu_label = _("Favoritos")
    menu_icon = "star"
    menu_order = 620
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("__str__", "user", "conteudo", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("user__username", "conteudo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    readonly_fields = ("user", "conteudo", "criado_em")
    
    def can_create(self, request):
        return False
    
    def can_edit(self, request, obj=None):
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


class AvaliacaoConteudoModelAdmin(ModelAdmin):
    model = AvaliacaoConteudo
    menu_label = _("Avaliações")
    menu_icon = "star"
    menu_order = 630
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("__str__", "user", "conteudo", "nota", "criado_em")
    list_filter = ("nota", "criado_em")
    search_fields = ("user__username", "conteudo__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    readonly_fields = ("user", "conteudo", "nota", "criado_em")
    
    def can_create(self, request):
        return False
    
    def can_edit(self, request, obj=None):
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


modeladmin_register(ComentarioModelAdmin)
modeladmin_register(LikeModelAdmin)
modeladmin_register(FavoritoConteudoModelAdmin)
modeladmin_register(AvaliacaoConteudoModelAdmin)


@hooks.register("register_admin_menu_item")
def register_interacoes_menu_item():
    return MenuItem(
        _("Interações"),
        "/admin/interacoes/comentario/",
        classnames="icon icon-comment",
        order=600
    )