"""
Templatetags de navegação do portal Nova PAT.

Fornece tags de inclusão para injetar os itens de navegação editáveis
(snippet `NavigationItem`) no header e no footer.

Uso nos templates:

    {% load navigation_tags %}
    {% get_navigation_items as nav_items %}
    {% get_footer_items as footer_items %}
"""

from typing import List

from django import template

from core.models import NavigationItem

register = template.Library()


def _build_tree(items: List[NavigationItem]) -> List[NavigationItem]:
    """
    Monta a árvore hierárquica de itens de navegação.

    Recebe a lista plana de itens (já filtrada por posição e ordenada) e
    retorna apenas os itens raiz (sem `parent`). Os descendentes são obtidos
    no template via a property `get_children` do model (que consulta o reverse
    manager `children` ordenado por `sort_order`/`title`).

    A hierarquia é derivada exclusivamente do campo explícito `parent`
    (FK auto-referencial) — nunca de IDs ou heurísticas (ver "Models e dados"
    em `AGENTS.md`).
    """
    return [item for item in items if not item.parent_id]


@register.simple_tag
def get_navigation_items() -> List[NavigationItem]:
    """
    Retorna a árvore de itens de navegação do menu superior (header).

    Filtra por `position == 'header'`, monta a hierarquia via `parent` e
    retorna apenas os itens raiz (com `children` pré-carregados).
    """
    items = list(
        NavigationItem.objects.filter(
            position=NavigationItem.POSITION_HEADER
        ).order_by("sort_order", "title")
    )
    return _build_tree(items)


@register.simple_tag
def get_footer_items() -> List[NavigationItem]:
    """
    Retorna a árvore de itens de navegação do rodapé (footer).

    Filtra por `position == 'footer'`, monta a hierarquia via `parent` e
    retorna apenas os itens raiz (com `children` pré-carregados).
    """
    items = list(
        NavigationItem.objects.filter(
            position=NavigationItem.POSITION_FOOTER
        ).order_by("sort_order", "title")
    )
    return _build_tree(items)