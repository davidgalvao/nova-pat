"""
URLs do app `conteudos`.

Rotas dedicadas ao cadastro administrativo de conteúdo de mídia
(fora do fluxo de sub-página do Wagtail) e gerenciamento de Séries (RF008).
"""

from django.urls import path

from . import views

app_name = "conteudos"

urlpatterns = [
    path(
        "cadastro/",
        views.cadastro_conteudo,
        name="cadastro_conteudo",
    ),
    path(
        "series/",
        views.lista_series,
        name="lista_series",
    ),
    path(
        "series/<int:serie_id>/editar/",
        views.editar_serie,
        name="editar_serie",
    ),
    path(
        "series/<int:serie_id>/adicionar-ep/",
        views.adicionar_ep,
        name="adicionar_ep",
    ),
    path(
        "api/series/<int:serie_id>/temporadas/",
        views.api_temporadas_por_serie,
        name="api_temporadas_por_serie",
    ),
path(
        "api/tags/autocomplete/",
        views.api_tags_autocomplete,
        name="api_tags_autocomplete",
    ),
]
