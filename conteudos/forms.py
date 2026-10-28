"""
Formulário de cadastro de conteúdo de mídia educacional (ConteudoPage).

Dedicado ao cadastro administrativo via menu "Gestão de Conteúdos", fora do
fluxo de sub-página do Wagtail. Layout single column, dentro da área
administrativa do Wagtail.

Implementa as correções do card NOVAPAT-69 conforme feedback do usuário:
- Layout single column (cada item abaixo do outro, na ordem solicitada)
- Campo Arquivo com "x" para remover seleção
- Autor pré-selecionado com o usuário logado
- Tipo de conteúdo: dropdown, somente leitura por padrão, ativando apenas se
  o sistema não identificar pela extensão da URL/arquivo
- Campo "Mecanismo de exibição" REMOVIDO (a view de exibição identifica
  automaticamente o tipo de mídia)
- Tipo de conteúdo = "Site Externo" quando URL externa, a menos que a URL
  aponte para tipo de mídia (.pdf, .mp3, .wav, etc.)
- Episódio de Série no COMEÇO do formulário, com seleção dinâmica:
  selecionar ou cadastrar nova série, selecionar ou cadastrar nova temporada,
  editar número do episódio. Nova série cria automaticamente temporada 1.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os
import re

from wagtail.models import Page

from canais.models import CanalPage
from curriculo.models import NivelEnsino, CurricularComponent
from series.models import Serie, Temporada
from conteudos.models import (
    ConteudoPage,
    Tipo,
    Licenca,
    CategoriaConteudo,
    EXTENSOES_SEGURAS,
)

# Mapeamento de extensão -> nome do Tipo pedagógico
EXTENSAO_PARA_TIPO = {
    ".mp4": "Vídeo",
    ".webm": "Vídeo",
    ".mov": "Vídeo",
    ".avi": "Vídeo",
    ".mkv": "Vídeo",
    ".m4v": "Vídeo",
    ".mp3": "Áudio",
    ".wav": "Áudio",
    ".ogg": "Áudio",
    ".m4a": "Áudio",
    ".aac": "Áudio",
    ".flac": "Áudio",
    ".pdf": "Documento",
    ".doc": "Documento",
    ".docx": "Documento",
    ".odt": "Documento",
    ".rtf": "Documento",
    ".txt": "Documento",
    ".csv": "Documento",
    ".xls": "Documento",
    ".xlsx": "Documento",
    ".ppt": "Apresentação",
    ".pptx": "Apresentação",
    ".odp": "Apresentação",
    ".key": "Apresentação",
    ".zip": "Download binário",
    ".rar": "Download binário",
    ".7z": "Download binário",
    ".exe": "Download binário",
    ".jpg": "Imagem",
    ".jpeg": "Imagem",
    ".png": "Imagem",
    ".gif": "Imagem",
    ".svg": "Imagem",
    ".webp": "Imagem",
}

# Mapeamento de extensão -> mecanismo de exibição (informativo, não no form)
EXTENSAO_PARA_MECANISMO = {
    ".mp4": ConteudoPage.MECANISMO_VIDEO,
    ".webm": ConteudoPage.MECANISMO_VIDEO,
    ".mov": ConteudoPage.MECANISMO_VIDEO,
    ".avi": ConteudoPage.MECANISMO_VIDEO,
    ".mkv": ConteudoPage.MECANISMO_VIDEO,
    ".m4v": ConteudoPage.MECANISMO_VIDEO,
    ".mp3": ConteudoPage.MECANISMO_AUDIO,
    ".wav": ConteudoPage.MECANISMO_AUDIO,
    ".ogg": ConteudoPage.MECANISMO_AUDIO,
    ".m4a": ConteudoPage.MECANISMO_AUDIO,
    ".aac": ConteudoPage.MECANISMO_AUDIO,
    ".flac": ConteudoPage.MECANISMO_AUDIO,
    ".pdf": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".doc": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".docx": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".odt": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".rtf": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".txt": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".csv": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".xls": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".xlsx": ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ".ppt": ConteudoPage.MECANISMO_APRESENTACAO,
    ".pptx": ConteudoPage.MECANISMO_APRESENTACAO,
    ".odp": ConteudoPage.MECANISMO_APRESENTACAO,
    ".key": ConteudoPage.MECANISMO_APRESENTACAO,
    ".zip": ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
    ".rar": ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
    ".7z": ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
    ".exe": ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
}


def extrair_extensao_url(url):
    """Extrai a extensão de uma URL externa."""
    if not url:
        return None
    caminho = url.split("?")[0].split("#")[0]
    partes = caminho.split(".")
    if len(partes) > 1:
        return "." + partes[-1].lower()
    return None


def tipo_por_extensao(extensao):
    """Retorna o nome do Tipo pedagógico para uma extensão, ou None."""
    if not extensao:
        return None
    return EXTENSAO_PARA_TIPO.get(extensao)


class ConteudoCadastroForm(forms.Form):
    """
    Formulário completo de cadastro de ConteudoPage com as regras de negócio
    e correções de UX do card NOVAPAT-69, em layout single column.
    """

    # ==================================================================
    # 12. Episódio de Série — COMEÇO do formulário
    # ==================================================================
    eh_episodio = forms.BooleanField(
        label=_("É episódio de série"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500",
                "data-toggle-serie": "true",
            }
        ),
        help_text=_(
            "Marque se este conteúdo é um episódio de uma série (estilo Netflix). "
            "Esta é uma das primeiras opções no fluxo de cadastro."
        ),
    )

    serie = forms.ModelChoiceField(
        label=_("Série"),
        queryset=Serie.objects.live().order_by("title"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "disabled": "disabled",
                "data-serie-select": "true",
            }
        ),
        empty_label=_("Selecionar série existente"),
        required=False,
        help_text=_("Escolha uma série já cadastrada."),
    )

    serie_nova_nome = forms.CharField(
        label=_("Nome da nova série"),
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("Nome da nova série"),
                "disabled": "disabled",
            }
        ),
        help_text=_("Ou crie uma nova série (será criada a temporada 1 automaticamente)."),
    )

    temporada = forms.ModelChoiceField(
        label=_("Temporada"),
        queryset=Temporada.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "disabled": "disabled",
                "data-temporada-select": "true",
            }
        ),
        empty_label=_("Selecionar temporada existente"),
        required=False,
        help_text=_("Escolha uma temporada da série selecionada."),
    )

    temporada_nova_numero = forms.IntegerField(
        label=_("Número da nova temporada"),
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": "1",
                "disabled": "disabled",
            }
        ),
        help_text=_("Número da nova temporada (padrão: 1)."),
    )

    numero_episodio = forms.IntegerField(
        label=_("Número do episódio"),
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("Próximo número da série"),
                "disabled": "disabled",
            }
        ),
        help_text=_("Número ordinal do episódio dentro da temporada."),
    )

    # ==================================================================
    # Identificação básica
    # ==================================================================
    title = forms.CharField(
        label=_("Título do conteúdo"),
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("Título da vídeo-aula, documento, áudio..."),
            }
        ),
    )

    search_description = forms.CharField(
        label=_("Descrição / resumo"),
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "rows": 3,
                "placeholder": _("Resumo curto usado em buscas e cards do site."),
            }
        ),
        required=False,
    )

    autor = forms.ModelChoiceField(
        label=_("Autor publicador"),
        queryset=None,  # definido no __init__
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
            }
        ),
        help_text=_("Usuário que está publicando este recurso."),
    )

    tags = forms.CharField(
        label=_("Tags"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("tag1, tag2, tag3"),
                "data-role": "tags",
            }
        ),
        help_text=_("Mínimo 3, máximo 50 tags separadas por vírgula."),
    )

    # ==================================================================
    # Canal (com botão "Criar Novo Canal")
    # ==================================================================
    canal = forms.ModelChoiceField(
        label=_("Canal de publicação"),
        queryset=CanalPage.objects.filter(is_active=True).order_by("title"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
            }
        ),
        empty_label=_("Selecione um canal"),
        help_text=_("Canal onde o conteúdo será publicado (metadado, não pai hierárquico)."),
    )

    # ==================================================================
    # Arquivo de mídia (com "x" para remover) × URL externa (travamento mútuo)
    # ==================================================================
    arquivo = forms.FileField(
        label=_("Arquivo de mídia"),
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "accept": ",".join(sorted({f"*{ext}" for ext in EXTENSOES_SEGURAS})),
                "data-arquivo-input": "true",
            }
        ),
        help_text=_(
            "Extensões aceitas: pdf, doc, docx, odt, rtf, txt, csv, xls, xlsx, "
            "ppt, pptx, odp, key, zip, rar, 7z, tar, gz, exe, msi, dmg, apk, "
            "mp3, wav, ogg, m4a, aac, flac, mp4, webm, mov, avi, mkv, m4v, "
            "jpg, jpeg, png, gif, svg, webp."
        ),
    )

    source = forms.URLField(
        label=_("URL de mídia externa"),
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("https://www.youtube.com/watch?v=ID ou https://exemplo.com/arquivo.pdf"),
                "data-url-input": "true",
            }
        ),
        help_text=_(
            "Use para link externo ou animação externa (YouTube, Vimeo, Spotify, etc.) "
            "ou URL direta de arquivo (.pdf, .mp3, .wav...). "
            "Ao preencher este campo, o arquivo de upload fica desabilitado."
        ),
    )

    # ==================================================================
    # Tipo de conteúdo (dropdown, depois de Arquivo/URL, só leitura por padrão)
    # ==================================================================
    tipo = forms.ModelChoiceField(
        label=_("Tipo de conteúdo"),
        queryset=Tipo.objects.filter(is_active=True).order_by("ordem", "name"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "readonly": "readonly",
            }
        ),
        empty_label=_("Identificado automaticamente pela URL/arquivo"),
        required=False,
        help_text=_(
            "Categoria pedagógica (vídeo, documento, podcast, etc.). "
            "É preenchido automaticamente pela extensão da URL ou do arquivo. "
            "Se for URL externa sem extensão reconhecida, fica como 'Site Externo'."
        ),
    )

    # ==================================================================
    # Categoria (com botão "Criar Nova Categoria")
    # ==================================================================
    category = forms.ModelChoiceField(
        label=_("Categoria"),
        queryset=CategoriaConteudo.objects.filter(is_active=True).order_by("canal__title", "ordem", "name"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
            }
        ),
        empty_label=_("Selecione uma categoria"),
        help_text=_("Categoria do conteúdo (árvore escopada por canal)."),
    )

    # ==================================================================
    # Licença (dropdown)
    # ==================================================================
    license = forms.ModelChoiceField(
        label=_("Licença"),
        queryset=Licenca.objects.filter(is_active=True).order_by("ordem", "name"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
            }
        ),
        empty_label=_("Sem licença"),
        required=False,
        help_text=_("Licença de uso (tipo Creative Commons)."),
    )

    # ==================================================================
    # Componentes curriculares (filtro por níveis de ensino)
    # ==================================================================
    componentes_curriculares = forms.ModelMultipleChoiceField(
        label=_("Componentes curriculares"),
        queryset=CurricularComponent.objects.filter(is_active=True).order_by("nivel__ordem", "category__ordem", "name"),
        widget=forms.SelectMultiple(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none h-64",
                "data-componente-filter": "true",
            }
        ),
        required=False,
        help_text=_(
            "Mínimo 1 obrigatório. Filtre por nível de ensino à esquerda para exibir "
            "apenas os componentes daqueles anos."
        ),
    )

    # ==================================================================
    # Metadados adicionais
    # ==================================================================
    authors = forms.CharField(
        label=_("Autores do conteúdo"),
        max_length=500,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none",
                "placeholder": _("Nomes dos autores/criadores do recurso"),
            }
        ),
        help_text=_("Diferente do autor publicador (campo acima)."),
    )

    options = forms.CharField(
        label=_("Opções extras (JSON)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none font-mono text-sm",
                "rows": 3,
                "placeholder": '{"acessibilidade": {"legendas": true}, "site_associado": "https://exemplo.com"}',
            }
        ),
        help_text=_(
            "JSON flexível para dados adicionais (acessibilidade, site associado, etc.). "
            "Exemplo: {\"formato\": \"16:9\", \"legendas\": true}"
        ),
    )

    # ==================================================================
    # Status e destaque
    # ==================================================================
    is_approved = forms.BooleanField(
        label=_("Aprovado para publicação"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500",
            }
        ),
        help_text=_("Somente usuários com papel coordenador+ podem aprovar."),
    )

    is_featured = forms.BooleanField(
        label=_("Em destaque"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500",
            }
        ),
        help_text=_("Exibir em destaque na home e listagens (blocos automáticos)."),
    )

    is_site = forms.BooleanField(
        label=_("É site associado"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        from usuarios.models import User

        # Autor: pré-selecionar com o usuário logado.
        # Nota: quando o form está bound (recebe dados GET/POST), o Django ignora
        # o `initial` para campos não preenchidos. Forçamos o initial aqui para
        # garantir que o autor logado apareça selecionado mesmo em GET com parâmetros
        # (ex: ?serie=1&eh_episodio=1 do "Adicionar EP").
        self.fields["autor"].queryset = User.objects.filter(is_active=True).order_by("username")
        if user and user.is_authenticated:
            self.fields["autor"].initial = user.pk
            # Se o form está bound mas autor não veio nos dados, forçar o initial
            if self.is_bound and "autor" not in self.data:
                self.fields["autor"].initial = user.pk

        # Temporada: começa vazia, preenchida via JS após selecionar Série
        self.fields["temporada"].queryset = Temporada.objects.none()

        # Pré-preencher a partir de parâmetros GET (usado por "Adicionar EP")
        eh_episodio = self.data.get("eh_episodio") or self.initial.get("eh_episodio")
        serie_id = self.data.get("serie") or self.initial.get("serie")
        numero_episodio = self.data.get("numero_episodio") or self.initial.get("numero_episodio")

        if eh_episodio in ("1", "true", "True", True):
            self.fields["eh_episodio"].initial = True

        if serie_id:
            try:
                self.fields["serie"].initial = int(serie_id)
            except (ValueError, TypeError):
                pass

        if numero_episodio:
            try:
                self.fields["numero_episodio"].initial = int(numero_episodio)
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        arquivo = cleaned_data.get("arquivo")
        source = cleaned_data.get("source")

        # Travamento mútuo: arquivo XOR source
        if arquivo and source:
            raise ValidationError(
                _("Não é possível enviar um arquivo e colar uma URL externa ao mesmo tempo. "
                  "Escolha apenas uma das duas opções.")
            )

        if not arquivo and not source:
            raise ValidationError(
                _("Você deve enviar um arquivo de mídia ou informar uma URL externa.")
            )

        # Determinar tipo pelo arquivo ou URL
        tipo = cleaned_data.get("tipo")

        if arquivo:
            extensao = os.path.splitext(arquivo.name)[1].lower()
            tipo_nome = tipo_por_extensao(extensao)
            if tipo_nome:
                try:
                    tipo = Tipo.objects.filter(name=tipo_nome, is_active=True).first()
                except Tipo.DoesNotExist:
                    tipo = None
            # RN-L3: validar extensão contra tipo se houver tipo
            if tipo:
                formatos = tipo.get_formatos_permitidos()
                if formatos and extensao.lstrip(".") not in [f.lower().lstrip(".") for f in formatos]:
                    raise ValidationError(
                        {
                            "arquivo": _(
                                f"Extensão '{extensao}' não permitida para o tipo '{tipo.name}'. "
                                f"Formatos aceitos: {', '.join(formatos) if formatos else 'nenhum configurado'}."
                            )
                        }
                    )
            cleaned_data["tipo"] = tipo

        elif source:
            extensao = extrair_extensao_url(source)
            if extensao:
                tipo_nome = tipo_por_extensao(extensao)
                if tipo_nome:
                    try:
                        tipo = Tipo.objects.filter(name=tipo_nome, is_active=True).first()
                    except Tipo.DoesNotExist:
                        tipo = None
                    cleaned_data["tipo"] = tipo
                else:
                    cleaned_data["tipo"] = None
            else:
                # URL sem extensão reconhecida -> Site Externo
                cleaned_data["tipo"] = None

        # RN-L5: tags mínimo 3, máximo 50
        tags_str = cleaned_data.get("tags", "") or ""
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
        if len(tags_list) < 3:
            raise ValidationError(
                {"tags": _("Informe pelo menos 3 tags (atualmente: %(qtd)d).") % {"qtd": len(tags_list)}}
            )
        if len(tags_list) > 50:
            raise ValidationError(
                {"tags": _("Máximo de 50 tags (atualmente: %(qtd)d).") % {"qtd": len(tags_list)}}
            )

        # RN-L5: componentes_curriculares mínimo 1
        componentes = cleaned_data.get("componentes_curriculares")
        if componentes and len(componentes) < 1:
            raise ValidationError(
                {"componentes_curriculares": _("Informe pelo menos 1 componente curricular.")}
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Cria o ConteudoPage e o anexa ao canal selecionado (Wagtail add_child),
        salva revision e publica. Retorna a instância criada.
        """
        from django.utils import timezone

        canal = self.cleaned_data["canal"]
        titulo = self.cleaned_data["title"]
        autor = self.cleaned_data["autor"]
        tipo = self.cleaned_data.get("tipo")
        category = self.cleaned_data["category"]
        license = self.cleaned_data.get("license")
        arquivo = self.cleaned_data.get("arquivo")
        source = self.cleaned_data.get("source")
        mecanismo = ConteudoPage.MECANISMO_LINK_EXTERNO
        if arquivo:
            mecanismo = EXTENSAO_PARA_MECANISMO.get(
                os.path.splitext(arquivo.name)[1].lower(),
                ConteudoPage.MECANISMO_LINK_EXTERNO,
            )
        elif source:
            ext = extrair_extensao_url(source)
            mecanismo = EXTENSAO_PARA_MECANISMO.get(
                ext, ConteudoPage.MECANISMO_LINK_EXTERNO
            )
        authors = self.cleaned_data.get("authors", "")
        options = self.cleaned_data.get("options") or {}
        is_approved = self.cleaned_data.get("is_approved", False)
        is_featured = self.cleaned_data.get("is_featured", False)
        is_site = self.cleaned_data.get("is_site", False)
        eh_episodio = self.cleaned_data.get("eh_episodio", False)
        temporada = self.cleaned_data.get("temporada")
        numero_episodio = self.cleaned_data.get("numero_episodio")
        tags_str = self.cleaned_data.get("tags", "") or ""
        componentes = self.cleaned_data.get("componentes_curriculares") or []

        # Determinar parent_page (canal ou temporada se episódio)
        parent_page = canal
        if eh_episodio and temporada:
            parent_page = temporada

        conteudo = ConteudoPage(
            title=titulo,
            search_description=self.cleaned_data.get("search_description", ""),
            canal=canal,
            autor=autor,
            tipo=tipo,
            category=category,
            license=license,
            mecanismo_exibicao=mecanismo,
            authors=authors,
            source=source or "",
            options=options,
            is_approved=is_approved,
            is_featured=is_featured,
            is_site=is_site,
            eh_episodio=eh_episodio,
            numero_episodio=numero_episodio,
        )

        # Arquivo
        if arquivo:
            conteudo.arquivo.save(arquivo.name, arquivo, save=False)
        else:
            conteudo.arquivo = None

        # Wagtail treebeard: add_child primeiro, depois salvar
        parent_page.add_child(instance=conteudo)
        conteudo.save_revision().publish()

        # Tags (django-taggit)
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
        conteudo.tags.add(*tags_list)

        # Componentes curriculares (M2M)
        for comp in componentes:
            conteudo.componentes_curriculares.add(comp)

        return conteudo
