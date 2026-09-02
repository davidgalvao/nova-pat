"""
Hooks do Wagtail para o app `core`.

Registra o snippet `NavigationItem` via `SnippetViewSet` (padrão Wagtail 8),
criando um item de menu dedicado "Menus" na raiz da barra lateral do admin,
com restrição de acesso para superusuários e grupos administrativos.

Também registra o atalho "Gestão da Home" na raiz da barra lateral, que
redireciona diretamente para a edição da instância da `HomePage` (resolvida
dinamicamente, sem hardcode de ID).
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from core.models import NavigationItem
from home.models import HomePage


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


class HomeManagementMenuItem(MenuItem):
    """
    Atalho "Gestão da Home" na raiz da barra lateral do admin.

    Redireciona diretamente para a URL de edição da instância da `HomePage`.
    O ID da HomePage é resolvido dinamicamente (a home é a `root_page` do site
    default, ou a primeira `HomePage` existente) — nunca hardcoded.

    O item só aparece para usuários com permissão de edição de páginas
    (superusuário ou com permissão de edição da HomePage), seguindo o padrão
    do `RestrictedNavigationMenuItem`. Se não existir `HomePage`, o item não
    é exibido (não quebra o admin).
    """

    def __init__(self, order: int = 100):
        super().__init__(
            _("Gestão da Home"),
            url="",
            name="gestao-da-home",
            icon_name="home",
            order=order,
        )

    def is_shown(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.has_perm("wagtailadmin.access_admin"):
            return False
        homepage = self._get_homepage()
        if homepage is None:
            return False
        # Superusuário sempre pode editar; demais precisam de permissão de
        # edição de páginas (change) sobre a HomePage.
        if user.is_superuser:
            return True
        return user.has_perm("wagtailadmin.access_admin") and homepage.permissions_for_user(
            user
        ).can_edit()

    def get_url(self, request=None):
        homepage = self._get_homepage()
        if homepage is None:
            return ""
        return reverse("wagtailadmin_pages:edit", args=[homepage.id])

    @staticmethod
    def _get_homepage():
        """
        Resolve dinamicamente a instância da `HomePage`.

        Prioriza a `root_page` do site default; se não houver site default,
        cai para a primeira `HomePage` existente. Retorna `None` se não existir.
        """
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        if site is not None and site.root_page is not None:
            homepage = HomePage.objects.filter(pk=site.root_page_id).first()
            if homepage is not None:
                return homepage
        return HomePage.objects.first()


@hooks.register("register_admin_menu_item")
def register_home_management_menu_item():
    """
    Registra o atalho "Gestão da Home" na raiz da barra lateral do admin.
    """
    return HomeManagementMenuItem()


register_snippet(NavigationItemViewSet)