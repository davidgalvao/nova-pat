"""
Hooks do Wagtail para o app `core`.

Registra o snippet `NavigationItem` via `SnippetViewSet` (padrão Wagtail 8),
criando um item de menu dedicado "Menus" na raiz da barra lateral do admin,
com restrição de acesso para superusuários e grupos administrativos.
"""

from django.utils.translation import gettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from core.models import NavigationItem


class NavigationItemViewSet(SnippetViewSet):
    """
    ViewSet do snippet `NavigationItem`.

    Expõe o modelo como um item de menu dedicado ("Menus") na raiz da barra
    lateral do admin, em vez de escondê-lo no menu genérico de Fragmentos.
    """

    model = NavigationItem
    menu_label = _("Menus")
    menu_icon = "list-ul"
    menu_name = "menus"
    add_to_admin_menu = True

    def get_menu_item(self, order=None):
        """
        Retorna um `MenuItem` com restrição de acesso.

        O item "Menus" só é renderizado na barra lateral para superusuários
        (`request.user.is_superuser`) ou usuários pertencentes a grupos com
        privilégios administrativos (grupos com permissão de acesso ao admin
        do Wagtail).
        """
        item = super().get_menu_item(order=order)
        return RestrictedNavigationMenuItem(
            label=item.label,
            url=item.url,
            name=item.name,
            icon_name=item.icon_name,
            order=item.order,
        )


class RestrictedNavigationMenuItem(MenuItem):
    """
    `MenuItem` que restringe a exibição do item "Menus" no admin.

    Exibe apenas para superusuários ou usuários de grupos com privilégios
    administrativos (grupos que possuem a permissão de acesso ao Wagtail admin).
    """

    def is_shown(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        # Grupos com privilégios administrativos: possuem a permissão de
        # acesso ao admin do Wagtail ("Can access Wagtail admin").
        return user.groups.filter(
            permissions__codename="access_admin"
        ).exists()


register_snippet(NavigationItemViewSet)