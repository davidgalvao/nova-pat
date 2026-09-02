"""
FilterSets da busca avançada (RF001).

Define os filtros aplicáveis a `ConteudoPage` e `AplicativoEducacionalPage`,
reutilizando uma base comum (`BaseSearchFilterSet`) para os filtros compartilhados
(`query` e `canal`). Os filtros específicos de cada domínio ficam no FilterSet
correspondente (ex: `tipo`/`licenca`/`componente` só existem em conteúdo).

`SafeModelChoiceFilter` ignora valores de URL inválidos em vez de lançar erro,
protegendo a view contra parâmetros manipulados pelo usuário.
"""

from typing import Any

import django_filters
from django.db.models import QuerySet
from wagtail.models import Page
from conteudos.models import ConteudoPage, Tipo, CategoriaConteudo, Licenca
from aplicativos.models import AplicativoEducacionalPage, AplicativoCategory
from canais.models import CanalPage
from curriculo.models import CurricularComponent, NivelEnsino


class SafeModelChoiceFilter(django_filters.ModelChoiceFilter):
    """
    ModelChoiceFilter que ignora valores inválidos em vez de lançar erro.
    Útil para parâmetros de URL que podem vir manipulados pelo usuário.
    """
    def clean(self, value: Any) -> Any:
        """
        Valida e limpa o valor antes de usar no queryset.

        Retorna ``None`` para valores inválidos, o que faz o filtro ser
        ignorado. Valores válidos seguem para a validação padrão do
        ``ModelChoiceFilter``.

        Args:
            value: Valor cru recebido do parâmetro de URL.

        Returns:
            Valor validado (convertido) ou ``None`` se inválido.
        """
        if not value:
            return None
        try:
            # Tenta converter para int para validar
            int(value)
        except (ValueError, TypeError):
            # Valor inválido - retorna None para ignorar o filtro
            return None
        # Valor válido - usa a validação padrão do ModelChoiceFilter
        return super().clean(value)


class BaseSearchFilterSet(django_filters.FilterSet):
    query = django_filters.CharFilter(method='filter_search_query', label='Busca')
    canal = SafeModelChoiceFilter(
        queryset=CanalPage.objects.live().filter(is_active=True),
        field_name='canal', label='Canal'
    )

    class Meta:
        model = Page
        fields = []

    def filter_search_query(
        self, queryset: QuerySet, name: str, value: str
    ) -> QuerySet:
        """
        Aplica a busca textual via Wagtail search.

        `queryset.search(value)` retorna um `PostgresSearchResults` (não um
        QuerySet comum), então extraímos os IDs dos resultados e re-filtramos o
        queryset original por esses IDs. Isso permite combinar a busca full-text
        do Wagtail com os demais filtros do FilterSet.

        Args:
            queryset: QuerySet base do FilterSet.
            name: Nome do campo (`query`).
            value: Termo de busca digitado pelo usuário.

        Returns:
            QuerySet filtrado pelos IDs dos resultados de busca, ou o queryset
            original se `value` estiver vazio.
        """
        if value:
            # Wagtail's search() returns PostgresSearchResults, get page IDs and filter queryset
            search_results = queryset.search(value)
            page_ids = [page.id for page in search_results]
            return queryset.filter(id__in=page_ids)
        return queryset


class ConteudoSearchFilterSet(BaseSearchFilterSet):
    tipo = SafeModelChoiceFilter(queryset=Tipo.objects.filter(is_active=True), field_name='tipo', label='Tipo de Mídia')
    categoria_conteudo = SafeModelChoiceFilter(queryset=CategoriaConteudo.objects.filter(is_active=True), field_name='category', label='Categoria')
    licenca = SafeModelChoiceFilter(queryset=Licenca.objects.filter(is_active=True), field_name='license', label='Licença')
    # Nível de Ensino: filtro independente via M2M componentes_curriculares -> nivel.
    # Usa PK (consistente com os demais filtros SafeModelChoiceFilter). A URL aceita
    # `?nivel_ensino=<pk>`. Decisão documentada em search/services.py e no ADR da busca.
    nivel_ensino = SafeModelChoiceFilter(
        queryset=NivelEnsino.objects.filter(is_active=True),
        field_name='componentes_curriculares__nivel',
        label='Nível de Ensino',
    )
    componente = SafeModelChoiceFilter(queryset=CurricularComponent.objects.filter(is_active=True), field_name='componentes_curriculares', label='Componente Curricular')

    class Meta(BaseSearchFilterSet.Meta):
        model = ConteudoPage
        fields = []


class AplicativoSearchFilterSet(BaseSearchFilterSet):
    categoria_aplicativo = SafeModelChoiceFilter(queryset=AplicativoCategory.objects.filter(is_active=True), field_name='category', label='Categoria')

    class Meta(BaseSearchFilterSet.Meta):
        model = AplicativoEducacionalPage
        fields = []