"""
Hooks do Wagtail para o app `core`.

Registra o snippet `NavigationItem` via `SnippetViewSet` (padrão Wagtail 8),
criando um item de menu dedicado "Menus" na raiz da barra lateral do admin,
com restrição de acesso para superusuários e grupos administrativos.

Também registra o atalho "Gestão da Home" na raiz da barra lateral, que
redireciona diretamente para a edição da instância da `HomePage` (resolvida
dinamicamente, sem hardcode de ID).
"""

from django import forms
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.models import Site
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from core.models import NavigationItem, RedeSocial, SiteSettings
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


class RedeSocialForm(forms.ModelForm):
    """
    Formulário do snippet `RedeSocial`.

    Filtra o seletor "Selecione a rede social" para exibir apenas as redes
    que ainda não foram cadastradas para as configurações do site,
    impedindo duplicatas.
    """

    class Meta:
        model = RedeSocial
        # site_settings é associado automaticamente no save(); não aparece no form.
        fields = ["tipo_rede", "nome", "url", "ativo", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Descobre o SiteSettings: na edição usa o da instância; na criação,
        # busca pelo site default.
        site_settings = None
        if self.instance and self.instance.pk and self.instance.site_settings_id:
            site_settings = self.instance.site_settings
        else:
            default_site = Site.objects.filter(is_default_site=True).first()
            if default_site:
                site_settings = SiteSettings.objects.filter(
                    site=default_site
                ).first()

        tipos_cadastrados = []
        if site_settings:
            queryset = RedeSocial.objects.filter(
                site_settings=site_settings
            )
            # Na edição, não exclui a própria rede que está sendo editada.
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            tipos_cadastrados = list(
                queryset.values_list("tipo_rede", flat=True)
            )

        # Exibe apenas as redes ainda não cadastradas.
        self.fields["tipo_rede"].choices = [
            (valor, label)
            for valor, label in RedeSocial.TIPO_REDE_CHOICES
            if valor not in tipos_cadastrados
        ]


class RedeSocialViewSet(SnippetViewSet):
    """
    ViewSet do snippet `RedeSocial`.

    Expõe o modelo como um item de menu dedicado ("Redes sociais") na raiz da
    barra lateral do admin, permitindo que gestores cadastrem os links e ícones
    que aparecem na toolbar do site (NOVAPAT-68).
    """

    model = RedeSocial
    menu_label = _("Redes sociais")
    menu_icon = "site"
    menu_name = "redes_sociais"
    add_to_admin_menu = True

    def get_form_class(self, for_update=False):
        """
        Retorna a classe do formulário a ser usada nos forms de criar/editar.

        O Wagtail 8 ignora o atributo ``form_class`` e constrói o formulário
        via ``get_form_class()``. Sobrescrevemos para retornar o
        ``RedeSocialForm``, que filtra o seletor de redes já cadastradas.
        """
        return RedeSocialForm

    def get_menu_item(self, order=None):
        item = super().get_menu_item(order=order)
        return RestrictedNavigationMenuItem(
            label=item.label,
            url=item.url,
            name=item.name,
            icon_name=item.icon_name,
            order=item.order,
        )


@hooks.register("insert_admin_js")
def inserir_js_chooser_toolbar():
    """
    Injetar o JS que preenche automaticamente o campo URL quando uma página
    é selecionada no PageChooserWidget dos links da toolbar.
    """
    return '<script src="%s"></script>' % static("js/toolbar-settings-chooser.js")


@hooks.register("insert_global_admin_css")
def inserir_css_separadores_toolbar():
    """
    Injetar CSS com separadores visuais entre cada opção de link da toolbar
    no painel "Links da toolbar" do SiteSettings (admin do Wagtail).
    """
    return '<link rel="stylesheet" href="%s">' % static("css/admin-toolbar-links.css")


register_snippet(NavigationItemViewSet)
register_snippet(RedeSocialViewSet)