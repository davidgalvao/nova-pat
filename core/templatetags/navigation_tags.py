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


@register.simple_tag
def get_navigation_items() -> List[NavigationItem]:
    """
    Retorna os itens de navegação do menu superior (header), ordenados.

    Filtra por `position == 'header'` e ordena por `sort_order` (a ordenação
    padrão do model já cobre `position` + `sort_order` + `title`).
    """
    return list(
        NavigationItem.objects.filter(
            position=NavigationItem.POSITION_HEADER
        ).order_by("sort_order", "title")
    )


@register.simple_tag
def get_footer_items() -> List[NavigationItem]:
    """
    Retorna os itens de navegação do rodapé (footer), ordenados.

    Filtra por `position == 'footer'` e ordena por `sort_order`.
    """
    return list(
        NavigationItem.objects.filter(
            position=NavigationItem.POSITION_FOOTER
        ).order_by("sort_order", "title")
    )