from django import template
from django.db.models import Count, IntegerField, Q, Value
from django.db.models.expressions import Case, When

from conteudos.models import ConteudoPage

register = template.Library()

# Limite padrão de itens exibidos no bloco de relacionados.
RELACIONADOS_LIMIT = 5


@register.filter
def filename(value):
    """
    Retorna o nome base de um caminho de arquivo (sem diretórios).

    Uso: ``{{ page.arquivo.name|filename }}``
    """
    if not value:
        return ""
    return str(value).split("/")[-1]


@register.inclusion_tag("conteudos/includes/relacionados.html", takes_context=True)
def conteudos_relacionados(context, page=None, limit=RELACIONADOS_LIMIT):
    """
    Monta o bloco de conteúdos relacionados da página de detalhe (NOVAPAT-44).

    Regras de negócio:
    - Exclui o próprio conteúdo da página atual.
    - Apenas publicados (``live()``) e aprovados (``is_approved=True``).
    - Prioriza conteúdos da mesma ``CategoriaConteudo`` e, entre eles/fora
      deles, os que têm mais tags em comum com a página atual.
    - Limitado a ``limit`` itens (default 5).
    - Nunca usa ``media_avaliacao``/``total_avaliacoes`` em filtro nem
      ordenação (decisão fechada em docs/requisitos-vs-legado.md:71-76).

    Contexto do template: ``relacionados`` (queryset já limitado) e ``limit``.
    """
    if page is None:
        page = context.get("page")

    relacionados = ConteudoPage.objects.none()

    if page is not None and getattr(page, "pk", None):
        tag_ids = list(page.tags.values_list("id", flat=True))

        relacionados = (
            ConteudoPage.objects.live()
            .filter(is_approved=True)
            .exclude(pk=page.pk)
        )

        if page.category_id:
            relacionados = relacionados.annotate(
                same_category=Case(
                    When(category_id=page.category_id, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
        else:
            relacionados = relacionados.annotate(
                same_category=Value(0, output_field=IntegerField())
            )

        if tag_ids:
            # Exige pelo menos uma tag em comum com a página atual.
            relacionados = relacionados.filter(tags__id__in=tag_ids).annotate(
                num_tags_comum=Count("tags", filter=Q(tags__id__in=tag_ids))
            )
        elif page.category_id:
            # Sem tags: exige mesma categoria.
            relacionados = relacionados.filter(
                category_id=page.category_id
            ).annotate(num_tags_comum=Value(0, output_field=IntegerField()))
        else:
            relacionados = relacionados.annotate(
                num_tags_comum=Value(0, output_field=IntegerField())
            )

        relacionados = (
            relacionados.distinct()
            .order_by("-same_category", "-num_tags_comum", "-first_published_at")[
                : int(limit)
            ]
        )

    return {"relacionados": relacionados, "limit": int(limit)}