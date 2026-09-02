"""
Serviços de busca - lógica de decisão de tipo de conteúdo.

Este módulo contém a lógica para inferir qual tipo de conteúdo buscar
baseado nos filtros preenchidos pelo usuário, eliminando a necessidade
de um radio explícito "Todos/Conteúdos/Aplicativos".

A inferência de tipo NÃO depende de checar em qual tabela um ID existe.
Cada tipo de categoria tem seu próprio parâmetro de URL/formulário:
- `categoria_conteudo` → CategoriaConteudo (conteúdos)
- `categoria_aplicativo` → AplicativoCategory (aplicativos)

O parâmetro que veio preenchido já diz o tipo, sem precisar de lookup.
Isso elimina o bug de ambiguidade de ID entre tabelas independentes.
"""

from typing import Literal
from django.http import QueryDict

from conteudos.models import Tipo, Licenca, CategoriaConteudo
from curriculo.models import CurricularComponent, NivelEnsino
from aplicativos.models import AplicativoCategory
from canais.models import CanalPage


TipoBusca = Literal['conteudo', 'aplicativo', 'ambos']


def resolver_tipo_busca(get_params: QueryDict) -> TipoBusca:
    """
    Determina qual tipo de conteúdo buscar baseado nos filtros preenchidos.

    Regras de inferência:
    - Se o usuário preencher Tipo de Mídia, Licença, Componente Curricular ou
      Nível de Ensino → buscar apenas ConteudoPage (esses campos não existem em
      AplicativoEducacionalPage)
    - Se o usuário selecionar uma categoria de conteúdo (`categoria_conteudo`)
      → buscar apenas ConteudoPage
    - Se o usuário selecionar uma categoria de aplicativo (`categoria_aplicativo`)
      → buscar apenas AplicativoEducacionalPage
    - Se nenhum desses filtros for preenchido (só título e/ou Canal)
      → buscar nos dois tipos juntos ('ambos')

    Nota: CategoriaConteudo e AplicativoCategory são modelos diferentes com
    sequences de ID independentes, então o mesmo ID numérico pode existir em
    ambas as tabelas. Por isso a inferência usa parâmetros separados na URL
    (categoria_conteudo vs categoria_aplicativo) — o parâmetro preenchido já
    determina o tipo, sem depender de lookup de ID.

    Args:
        get_params: QueryDict com os parâmetros da request (request.GET)

    Returns:
        'conteudo' | 'aplicativo' | 'ambos'
    """
    # Helper para validar se um ID é um inteiro válido
    def is_valid_id(value):
        if not value:
            return False
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    # Verificar filtros exclusivos de ConteudoPage (apenas se IDs válidos)
    tipo_id = get_params.get('tipo')
    licenca_id = get_params.get('licenca')
    componente_id = get_params.get('componente')
    nivel_ensino_id = get_params.get('nivel_ensino')

    has_conteudo_exclusive_filter = (
        is_valid_id(tipo_id)
        or is_valid_id(licenca_id)
        or is_valid_id(componente_id)
        or is_valid_id(nivel_ensino_id)
    )
    if has_conteudo_exclusive_filter:
        return 'conteudo'

    # Verificar categoria de conteúdo (parâmetro próprio, sem lookup de ID)
    categoria_conteudo_id = get_params.get('categoria_conteudo')
    if is_valid_id(categoria_conteudo_id):
        return 'conteudo'

    # Verificar categoria de aplicativo (parâmetro próprio, sem lookup de ID)
    categoria_aplicativo_id = get_params.get('categoria_aplicativo')
    if is_valid_id(categoria_aplicativo_id):
        return 'aplicativo'

    # Se chegou aqui, nenhum filtro exclusivo foi preenchido
    # Busca nos dois tipos (query e/ou canal apenas)
    return 'ambos'


def get_selected_filter_values(get_params: QueryDict) -> dict:
    """
    Extrai os valores dos filtros selecionados para exibição no template
    (tags de "filtros ativos" removíveis).

    Args:
        get_params: QueryDict com os parâmetros da request (request.GET)

    Returns:
        Dicionário com objetos selecionados (ou None) para cada filtro
    """
    selected = {}

    # Helper para validar se um ID é um inteiro válido
    def is_valid_id(value):
        if not value:
            return False
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    # Canal
    canal_id = get_params.get('canal')
    if is_valid_id(canal_id):
        try:
            selected['canal'] = CanalPage.objects.live().filter(is_active=True).get(pk=canal_id)
        except CanalPage.DoesNotExist:
            selected['canal'] = None
    else:
        selected['canal'] = None

    # Tipo de Mídia (apenas ConteudoPage)
    tipo_id = get_params.get('tipo')
    if is_valid_id(tipo_id):
        try:
            selected['tipo'] = Tipo.objects.filter(is_active=True).get(pk=tipo_id)
        except Tipo.DoesNotExist:
            selected['tipo'] = None
    else:
        selected['tipo'] = None

    # Categoria de conteúdo (parâmetro próprio `categoria_conteudo`)
    categoria_conteudo_id = get_params.get('categoria_conteudo')
    if is_valid_id(categoria_conteudo_id):
        try:
            selected['categoria_conteudo'] = (
                CategoriaConteudo.objects.filter(is_active=True)
                .select_related('canal')
                .get(pk=categoria_conteudo_id)
            )
        except CategoriaConteudo.DoesNotExist:
            selected['categoria_conteudo'] = None
    else:
        selected['categoria_conteudo'] = None

    # Categoria de aplicativo (parâmetro próprio `categoria_aplicativo`)
    categoria_aplicativo_id = get_params.get('categoria_aplicativo')
    if is_valid_id(categoria_aplicativo_id):
        try:
            selected['categoria_aplicativo'] = (
                AplicativoCategory.objects.filter(is_active=True)
                .get(pk=categoria_aplicativo_id)
            )
        except AplicativoCategory.DoesNotExist:
            selected['categoria_aplicativo'] = None
    else:
        selected['categoria_aplicativo'] = None

    # Licença (apenas ConteudoPage)
    licenca_id = get_params.get('licenca')
    if is_valid_id(licenca_id):
        try:
            selected['licenca'] = Licenca.objects.filter(is_active=True).get(pk=licenca_id)
        except Licenca.DoesNotExist:
            selected['licenca'] = None
    else:
        selected['licenca'] = None

    # Componente Curricular (apenas ConteudoPage)
    componente_id = get_params.get('componente')
    if is_valid_id(componente_id):
        try:
            selected['componente'] = CurricularComponent.objects.filter(is_active=True).select_related('nivel', 'category').get(pk=componente_id)
        except CurricularComponent.DoesNotExist:
            selected['componente'] = None
    else:
        selected['componente'] = None

    # Nível de Ensino (apenas ConteudoPage)
    nivel_ensino_id = get_params.get('nivel_ensino')
    if is_valid_id(nivel_ensino_id):
        try:
            selected['nivel_ensino'] = NivelEnsino.objects.filter(is_active=True).get(pk=nivel_ensino_id)
        except NivelEnsino.DoesNotExist:
            selected['nivel_ensino'] = None
    else:
        selected['nivel_ensino'] = None

    return selected