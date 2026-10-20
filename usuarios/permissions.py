"""
Autorização baseada em papel (RBAC) para o app `usuarios`.

Centraliza a lógica de permissões que antes estava espalhada em `can_*`
de cada ModelAdmin (conteúdos, aplicativos, series, canais, usuarios,
interacoes), conforme mitigacao prevista no ADR-004.

O `RolePermissionMixin` expõe ``can_create``, ``can_edit`` e ``can_delete``
com base no papel do usuário (``usuarios.User.role``):

- ``can_create``: restrito a coordenador+ (super-admin, admin, coordenador).
- ``can_edit``: coordenador+.
- ``can_delete``: coordenador+.

Papéis abaixo de coordenador (editor, convidado) não têm nenhuma dessas
permissões — comportamento igual ao `convidado` (decisão D2, fechada).

Uso típico:

    from wagtail.permission_policies.pages import PagePermissionPolicy
    from usuarios.permissions import RolePermissionMixin


    class ConteudoPagePermissionPolicy(RolePermissionMixin, PagePermissionPolicy):
        pass


    class ConteudoPage(Page):
        permission_policy = ConteudoPagePermissionPolicy()
"""

from typing import Optional

from django.contrib.auth.models import AbstractUser

from wagtail.models import Page
from wagtail.permission_policies.pages import PagePermissionPolicy

from usuarios.models import Role


# Papéis que podem criar/editar/excluir conteúdo (coordenador+).
# Mantido como constante para evitar magic strings espalhadas pelo código.
PRIVILEGED_ROLE_SLUGS = ("super-admin", "admin", "coordenador")


def _is_privileged(user: Optional[AbstractUser]) -> bool:
    """Retorna True se o usuário tem papel privilegiado (coordenador+)."""
    if user is None or not user.is_authenticated:
        return False
    role = getattr(user, "role", None)
    if role is None:
        return False
    return role.slug in PRIVILEGED_ROLE_SLUGS


class RolePermissionMixin:
    """
    Mixin centralizado de autorização baseado em Role.

    Fornece ``can_create``, ``can_edit`` e ``can_delete`` aplicando a
    regra de negócio RN-L1: criação/edição/exclusão de conteúdo é
    restrita a papéis privilegiados (super-admin, admin, coordenador).

    Deve ser usado à esquerda da MRO para sobrescrever os métodos da
    classe de política de permissão do Wagtail (ex: ``PagePermissionPolicy``).
    """

    def can_create(self, user: Optional[AbstractUser], parent_page: Optional[Page] = None) -> bool:
        """Verifica se o usuário pode criar páginas deste tipo."""
        return _is_privileged(user)

    def can_edit(self, user: Optional[AbstractUser], page: Optional[Page] = None) -> bool:
        """Verifica se o usuário pode editar uma página deste tipo."""
        return _is_privileged(user)

    def can_delete(self, user: Optional[AbstractUser], page: Optional[Page] = None) -> bool:
        """Verifica se o usuário pode excluir uma página deste tipo."""
        return _is_privileged(user)


class ConteudoPagePermissionPolicy(RolePermissionMixin, PagePermissionPolicy):
    """
    Política de permissão de ``ConteudoPage``.

    Combina a lógica centralizada de papel (``RolePermissionMixin``) com a
    política de página do Wagtail (``PagePermissionPolicy``) para aplicar
    a restrição de criação/edição/exclusão a coordenador+ no admin.
    """
