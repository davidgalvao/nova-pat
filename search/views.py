from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from wagtail.models import Page
from .filters import ConteudoSearchFilterSet, AplicativoSearchFilterSet
from .services import resolver_tipo_busca, get_selected_filter_values
from canais.models import CanalPage
from conteudos.models import Tipo, CategoriaConteudo, Licenca, ConteudoPage
from curriculo.models import CurricularComponent
from aplicativos.models import AplicativoCategory, AplicativoEducacionalPage


def search(request):
    # Determinar tipo de busca baseado nos filtros preenchidos (inferência)
    tipo_busca = resolver_tipo_busca(request.GET)

    # Obter valores dos filtros selecionados para exibição no template
    selected_filters = get_selected_filter_values(request.GET)

    # Contexto base com todos os filtros disponíveis
    context = {
        'canais': CanalPage.objects.live().filter(is_active=True).order_by('name'),
        'tipos': Tipo.objects.filter(is_active=True).order_by('ordem', 'name'),
        'categorias_conteudo': CategoriaConteudo.objects.filter(is_active=True).select_related('canal').order_by('canal__name', 'name'),
        'categorias_aplicativo': AplicativoCategory.objects.filter(is_active=True).order_by('name'),
        'licencas': Licenca.objects.filter(is_active=True).order_by('ordem', 'name'),
        'componentes': CurricularComponent.objects.filter(is_active=True).select_related('nivel', 'category').order_by('nivel__ordem', 'category__ordem', 'name'),
    }

    # Adicionar filtros selecionados ao contexto
    context.update(selected_filters)

    # Executar busca conforme tipo inferido
    if tipo_busca == 'conteudo':
        filterset = ConteudoSearchFilterSet(request.GET, queryset=ConteudoPage.objects.live())
        search_results = filterset.qs
        context['filterset'] = filterset
    elif tipo_busca == 'aplicativo':
        filterset = AplicativoSearchFilterSet(request.GET, queryset=AplicativoEducacionalPage.objects.live())
        search_results = filterset.qs
        context['filterset'] = filterset
    else:  # 'ambos'
        # Para busca em ambos os tipos, buscamos em cada modelo separadamente
        # e combinamos os resultados, pois cada modelo tem seus próprios campos
        # (ex: canal está em ambos, mas outros campos são específicos)
        
        # Buscar ConteudoPage
        conteudo_filterset = ConteudoSearchFilterSet(request.GET, queryset=ConteudoPage.objects.live())
        conteudo_results = conteudo_filterset.qs
        
        # Buscar AplicativoEducacionalPage
        aplicativo_filterset = AplicativoSearchFilterSet(request.GET, queryset=AplicativoEducacionalPage.objects.live())
        aplicativo_results = aplicativo_filterset.qs
        
        # Combinar resultados usando union (precisa ter mesmos campos)
        # Usamos values_list('id', flat=True) para fazer union de IDs e depois buscar
        conteudo_ids = list(conteudo_results.values_list('id', flat=True))
        aplicativo_ids = list(aplicativo_results.values_list('id', flat=True))
        all_ids = conteudo_ids + aplicativo_ids
        
        # Buscar páginas específicas pelos IDs combinados
        search_results = Page.objects.live().filter(id__in=all_ids).specific()
        
        context['filterset'] = None

    # Paginação
    paginator = Paginator(search_results, 12)
    page = request.GET.get('page')
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    context.update({
        'search_results': search_results,
        'search_query': request.GET.get('query', ''),
        'current_filters': request.GET.urlencode(),
        'tipo_busca': tipo_busca,  # Para debug/template se necessário
    })
    return render(request, 'search/search.html', context)
