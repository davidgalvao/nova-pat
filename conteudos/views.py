"""
Views dedicadas ao cadastro de conteúdo de mídia educacional (ConteudoPage)
e gerenciamento de Séries (RF008).

Fora do fluxo de sub-página do Wagtail, acessível pelo item de menu
"Gestão de Conteúdos" no admin.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from taggit.models import Tag

from wagtail.models import Page

from conteudos.forms import ConteudoCadastroForm
from series.models import Serie, Temporada
from usuarios.permissions import _is_privileged


def _pode_cadastrar_conteudo(user):
    """Apenas papéis privilegiados (coordenador+) cadastram conteúdo (RN-L1)."""
    return _is_privileged(user)


@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def cadastro_conteudo(request):
    """
    Formulário dedicado de cadastro de conteúdo de mídia educacional.

    Implementa as 12 correções do card NOVAPAT-69.
    """
    if request.method == "POST":
        form = ConteudoCadastroForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                conteudo = form.save()
                messages.success(
                    request,
                    _(
                        'Conteúdo "%(title)s" cadastrado com sucesso.'
                    ) % {"title": conteudo.title},
                )
                return redirect("conteudos:cadastro_conteudo")
            except Exception as exc:  # noqa: BLE001
                messages.error(
                    request,
                    _("Erro ao salvar o conteúdo: %(error)s") % {"error": exc},
                )
        else:
            messages.error(
                request,
                _("Corrija os erros indicados no formulário."),
            )
    else:
        form = ConteudoCadastroForm(request.GET, user=request.user)

    contexto = {
        "form": form,
        "titulo_pagina": _("Cadastro de Conteúdo de Mídia"),
        "menu_ativo": "gestao-conteudos",
    }
    return render(request, "conteudos/cadastro_conteudo.html", contexto)


# ========================================================================
# Séries (RF008) — cadastro dedicado no admin
# ========================================================================

@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def lista_series(request):
    """
    Lista todas as séries cadastradas, com opção de editar ou adicionar EP.
    """
    series = Serie.objects.live().order_by("title")
    contexto = {
        "series": series,
        "titulo_pagina": _("Séries (estilo Netflix)"),
        "menu_ativo": "series",
    }
    return render(request, "conteudos/lista_series.html", contexto)


@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def editar_serie(request, serie_id):
    """
    Edita uma série existente (Título, Capa, Descrição/Sinopse, Metadados).
    """
    serie = get_object_or_404(Serie, id=serie_id)
    temporadas = serie.temporadas.order_by("numero") if hasattr(serie, "temporadas") else []

    if request.method == "POST":
        titulo = request.POST.get("title", "").strip()
        sinopse = request.POST.get("sinopse", "").strip()

        if not titulo:
            messages.error(request, _("O título da série é obrigatório."))
        else:
            serie.title = titulo
            serie.draft_title = titulo
            serie.sinopse = sinopse
            serie.save_revision().publish()
            messages.success(request, _("Série '%(title)s' atualizada com sucesso.") % {"title": serie.title})
            return redirect("conteudos:lista_series")

    contexto = {
        "serie": serie,
        "temporadas": temporadas,
        "titulo_pagina": _("Editar Série") + f" — {serie.title}",
        "menu_ativo": "series",
    }
    return render(request, "conteudos/editar_serie.html", contexto)


@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def adicionar_ep(request, serie_id):
    """
    Redireciona para o cadastro de conteúdo com a Série já selecionada
    e o número do próximo episódio preenchido.
    """
    serie = get_object_or_404(Serie, id=serie_id)

    # Determinar o próximo número de episódio baseado nas temporadas existentes
    proximo_numero = 1
    temporadas = Temporada.objects.filter(serie=serie).order_by("-numero")
    if temporadas.exists():
        # Pegar o maior numero_episodio entre todos os episódios de todas as temporadas
        from conteudos.models import ConteudoPage
        ultimo_ep = (
            ConteudoPage.objects.child_of(temporadas.first())
            .filter(numero_episodio__isnull=False)
            .order_by("-numero_episodio")
            .first()
        )
        if ultimo_ep and ultimo_ep.numero_episodio:
            proximo_numero = ultimo_ep.numero_episodio + 1

    # Redireciona para o cadastro com parâmetros na URL para pré-preencher
    url = (
        f"{reverse('conteudos:cadastro_conteudo')}?"
        f"serie={serie.id}&eh_episodio=1&numero_episodio={proximo_numero}"
    )
    return redirect(url)


@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def api_temporadas_por_serie(request, serie_id):
    """
    Endpoint API para listar temporadas de uma série (usado via AJAX no formulário).
    """
    try:
        serie = Serie.objects.get(id=serie_id)
    except Serie.DoesNotExist:
        return JsonResponse({"error": "Série não encontrada."}, status=404)

    temporadas = Temporada.objects.filter(serie=serie).order_by("numero")
    dados = [
        {
            "id": t.id,
            "numero": t.numero,
            "sinopse": t.sinopse or "",
        }
        for t in temporadas
    ]
    return JsonResponse({"temporadas": dados})


@login_required
@user_passes_test(_pode_cadastrar_conteudo, login_url="admin:login")
def api_tags_autocomplete(request):
    """
    Endpoint API para autocomplete de tags (usado via AJAX no formulário).
    Busca tags existentes a partir de 3 caracteres, com debounce no frontend.
    """
    query = request.GET.get("q", "").strip()
    if len(query) < 3:
        return JsonResponse({"tags": []})

    tags = Tag.objects.filter(name__icontains=query).order_by("name")[:20]
    dados = [{"name": tag.name, "slug": tag.slug} for tag in tags]
    return JsonResponse({"tags": dados})
