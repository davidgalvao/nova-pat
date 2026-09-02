from django import template

register = template.Library()


@register.filter
def filename(value):
    """
    Retorna o nome base de um caminho de arquivo (sem diretórios).

    Uso: ``{{ page.arquivo.name|filename }}``
    """
    if not value:
        return ""
    return str(value).split("/")[-1]