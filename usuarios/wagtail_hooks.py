from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from .models import Role, User, UserCanal


class RoleModelAdmin(ModelAdmin):
    model = Role
    menu_label = _("Papéis (Roles)")
    menu_icon = "group"
    menu_order = 700
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "slug", "ordem", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering = ("ordem", "name")
    readonly_fields = ("slug",)  # Slug não deve ser editado após criação
    
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


class UserModelAdmin(ModelAdmin):
    model = User
    menu_label = _("Usuários")
    menu_icon = "user"
    menu_order = 710
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("username", "email", "get_full_name", "role", "is_active", "verified", "date_joined")
    list_filter = ("role", "is_active", "verified", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    list_per_page = 25
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "password")
    
    panels = [
        MultiFieldPanel([
            FieldPanel("username"),
            FieldPanel("email"),
            FieldPanel("first_name"),
            FieldPanel("last_name"),
        ], heading=_("Informações Pessoais")),
        
        MultiFieldPanel([
            FieldPanel("role"),
            FieldPanel("is_active"),
            FieldPanel("is_staff"),
            FieldPanel("is_superuser"),
            FieldPanel("verified"),
        ], heading=_("Permissões e Status")),
        
        MultiFieldPanel([
            FieldPanel("options"),
        ], heading=_("Opções Adicionais")),
        
        MultiFieldPanel([
            FieldPanel("date_joined"),
            FieldPanel("last_login"),
        ], heading=_("Datas Importantes")),
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
        if user.role and user.role.slug in ("super-admin", "admin"):
            return True
        # Usuário pode editar próprio perfil (exceto role, is_staff, is_superuser)
        if obj and obj.id == user.id:
            return True
        return False
    
    def can_delete(self, request, obj=None):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.role and user.role.slug in ("super-admin", "admin")


class UserCanalModelAdmin(ModelAdmin):
    model = UserCanal
    menu_label = _("Usuários × Canais")
    menu_icon = "link"
    menu_order = 720
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("user", "canal", "criado_em")
    list_filter = ("canal", "criado_em")
    search_fields = ("user__username", "user__email", "canal__title")
    list_per_page = 25
    ordering = ("-criado_em",)
    readonly_fields = ("criado_em",)
    
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
        return user.role and user.role.slug in ("super-admin", "admin")


modeladmin_register(RoleModelAdmin)
modeladmin_register(UserModelAdmin)
modeladmin_register(UserCanalModelAdmin)


@hooks.register("register_admin_menu_item")
def register_usuarios_menu_item():
    return MenuItem(
        _("Usuários e Permissões"),
        "/admin/usuarios/user/",
        classnames="icon icon-user",
        order=700
    )