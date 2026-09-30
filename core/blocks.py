"""
Repositório Central de Componentes (blocos StreamField reutilizáveis).

Padrões consagrados de UI (Hero, Banners, Grids) implementados como
`StructBlock` do Wagtail, consumidos pela Home (e futuramente por outras
páginas) via `StreamField`. Segue `core/ARCHITECTURE.md`: blocos reutilizáveis
moram aqui, não campos de layout genéricos em `BasePage`.

Cada bloco tem um template modular correspondente em
`core/templates/blocks/<nome_bloco>.html`, renderizado por convenção do
`{% include_block %}` do Wagtail.
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock


class HeroBlock(blocks.StructBlock):
    """
    Seção de destaque principal da página (H1/H2), com título de impacto,
    subtítulo, imagem/vídeo de fundo opcional e chamadas para ação (CTAs).
    """

    titulo = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Título de impacto da seção (renderizado como H1/H2).",
    )
    subtitulo = blocks.TextBlock(
        required=False,
        help_text="Subtítulo de apoio ao título principal.",
    )
    imagem_fundo = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo da seção (recomendado: alta resolução, 16:9).",
    )
    video_fundo = blocks.URLBlock(
        required=False,
        help_text="URL opcional de vídeo de fundo (MP4/WebM).",
    )
    cta_primario_texto = blocks.CharBlock(
        required=False,
        max_length=60,
        help_text="Texto do botão de chamada para ação principal.",
    )
    cta_primario_url = blocks.URLBlock(
        required=False,
        help_text="URL de destino do CTA principal.",
    )
    cta_secundario_texto = blocks.CharBlock(
        required=False,
        max_length=60,
        help_text="Texto do botão de chamada para ação secundário.",
    )
    cta_secundario_url = blocks.URLBlock(
        required=False,
        help_text="URL de destino do CTA secundário.",
    )

    class Meta:
        icon = "placeholder"
        label = "Hero (Destaque Principal)"
        template = "blocks/hero_block.html"


class FullBannerBlock(blocks.StructBlock):
    """
    Banner horizontal de largura total para campanhas/anúncios institucionais,
    com link de redirecionamento.
    """

    titulo = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Título do banner.",
    )
    texto = blocks.TextBlock(
        required=False,
        help_text="Texto de apoio exibido no banner.",
    )
    imagem = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo do banner.",
    )
    link_url = blocks.URLBlock(
        required=False,
        help_text="URL de destino ao clicar no banner.",
    )
    link_texto = blocks.CharBlock(
        required=False,
        max_length=60,
        help_text="Texto do link de redirecionamento.",
    )

    class Meta:
        icon = "form"
        label = "Banner Full-Width"
        template = "blocks/full_banner_block.html"


class CarrosselCategoriaBlock(blocks.StructBlock):
    """
    Carrossel estilo streaming que exibe o acervo de `ConteudoPage` filtrado
    por uma categoria de conteúdo escolhida pelo editor.

    **Decisão de modelagem**: o campo `categoria` usa `SnippetChooserBlock`
    apontando para `conteudos.CategoriaConteudo` (Snippet, não Page — por isso
    `PageChooserBlock` não se aplica). A categoria é a taxonomia escopada por
    canal que filtra diretamente `ConteudoPage.category`, a forma mais direta
    de montar o acervo. A consulta é feita em `get_context()` (padrão Wagtail),
    filtrando apenas conteúdos `live` e `is_approved=True`.
    """

    titulo_secao = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Título exibido na seção do carrossel.",
    )
    categoria = SnippetChooserBlock(
        "conteudos.CategoriaConteudo",
        required=True,
        help_text="Categoria de conteúdo cujo acervo será exibido no carrossel.",
    )
    limite = blocks.IntegerBlock(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Quantidade máxima de conteúdos exibidos no carrossel.",
    )

    def get_context(self, value, parent_context=None):
        """
        Consulta dinamicamente os conteúdos da categoria escolhida.

        Filtra apenas páginas `live` e `is_approved=True`, ordenadas pela data
        de primeira publicação (mais recentes primeiro), limitadas por `limite`.
        """
        context = super().get_context(value, parent_context=parent_context)

        from conteudos.models import ConteudoPage

        categoria = value.get("categoria")
        limite = value.get("limite") or 10

        conteudos = ConteudoPage.objects.none()
        if categoria is not None:
            conteudos = (
                ConteudoPage.objects.live()
                .filter(is_approved=True, category=categoria)
                .order_by("-first_published_at")[:limite]
            )

        context["conteudos"] = conteudos
        return context

    class Meta:
        icon = "list-ul"
        label = "Carrossel por Categoria"
        template = "blocks/carrossel_categoria_block.html"


class DestaquesManuaisBlock(blocks.StructBlock):
    """
    Grade de destaques pinados manualmente pelo editor, selecionando páginas
    específicas (conteúdos, canais, aplicativos, etc.) via `PageChooserBlock`.
    """

    titulo_secao = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Título exibido na seção de destaques.",
    )
    paginas = blocks.ListBlock(
        blocks.PageChooserBlock(
            help_text="Página a ser pinada como destaque (conteúdo, canal, aplicativo, etc.)."
        ),
        min_num=1,
        max_num=12,
        help_text="Selecione as páginas que deseja destacar em grade.",
    )

    class Meta:
        icon = "pick"
        label = "Destaques Manuais"
        template = "blocks/destaques_manuais_block.html"


class FeatureGridBlock(blocks.StructBlock):
    """
    Grade de recursos/serviços (ícone, título e breve texto) para atalhos
    rápidos institucionais.
    """

    titulo_secao = blocks.CharBlock(
        required=True,
        max_length=200,
        help_text="Título exibido na seção de recursos/serviços.",
    )

    class FeatureItemBlock(blocks.StructBlock):
        icone = blocks.CharBlock(
            required=False,
            max_length=50,
            help_text="Identificador do ícone (ex: nome de ícone SVG/emojis).",
        )
        titulo = blocks.CharBlock(
            required=True,
            max_length=120,
            help_text="Título do recurso/serviço.",
        )
        texto = blocks.TextBlock(
            required=False,
            help_text="Breve descrição do recurso/serviço.",
        )
        link_url = blocks.URLBlock(
            required=False,
            help_text="URL de destino do atalho.",
        )

        class Meta:
            icon = "placeholder"
            label = "Item de Recurso"

    itens = blocks.ListBlock(
        FeatureItemBlock(),
        min_num=1,
        max_num=12,
        help_text="Itens de recurso/serviço exibidos em grade.",
    )

    class Meta:
        icon = "grip"
        label = "Grade de Recursos/Serviços"
        template = "blocks/feature_grid_block.html"


class UltimoConteudoPlayerBlock(blocks.StructBlock):
    """
    Hero com o último conteúdo publicado do canal em player de vídeo/áudio
    (ou capa com link, para demais mecanismos de exibição).

    **Decisão de modelagem**: bloco contextual — não tem campos editáveis.
    O canal é resolvido em `get_context()` a partir de `parent_context["page"]`
    (padrão Wagtail), e a consulta segue o padrão de `CarrosselCategoriaBlock`:
    apenas `live()` e `is_approved=True`, ordenado por `-first_published_at`.
    Fora de uma `CanalPage`, o bloco não renderiza nada.
    """

    def get_context(self, value, parent_context=None):
        """Busca o conteúdo mais recente do canal que serve a página."""
        context = super().get_context(value, parent_context=parent_context)

        from conteudos.models import ConteudoPage

        page = (parent_context or {}).get("page")
        conteudo = None
        if page is not None:
            conteudo = (
                ConteudoPage.objects.live()
                .child_of(page)
                .filter(is_approved=True)
                .order_by("-first_published_at")
                .first()
            )

        context["conteudo"] = conteudo
        return context

    class Meta:
        icon = "media"
        label = "Último Conteúdo (Player)"
        template = "blocks/ultimo_conteudo_player.html"


class UltimosConteudosCarrosselBlock(blocks.StructBlock):
    """
    Carrossel estilo streaming com os últimos conteúdos do canal
    (até 9 itens, 3 por página, passadores prev/next via CSS scroll-snap).

    **Decisão de modelagem**: bloco contextual — mesma lógica de resolução
    de canal de `UltimoConteudoPlayerBlock`. Limite fixo de 9 itens
    (decisão do plano), sem campo editável.
    """

    LIMITE = 9

    def get_context(self, value, parent_context=None):
        """
        Busca os últimos conteúdos do canal que serve a página e os
        agrupa em páginas de 3 (`paginas = [[c1,c2,c3], [c4,c5,c6], ...]`),
        para o template iterar páginas sem lógica de paginação nele.
        """
        context = super().get_context(value, parent_context=parent_context)

        from conteudos.models import ConteudoPage

        page = (parent_context or {}).get("page")
        conteudos = ConteudoPage.objects.none()
        if page is not None:
            conteudos = (
                ConteudoPage.objects.live()
                .child_of(page)
                .filter(is_approved=True)
                .order_by("-first_published_at")[: self.LIMITE]
            )

        conteudos = list(conteudos)
        context["paginas"] = [
            conteudos[i : i + 3] for i in range(0, len(conteudos), 3)
        ]
        return context

    class Meta:
        icon = "list-ul"
        label = "Últimos Conteúdos (Carrossel)"
        template = "blocks/ultimos_conteudos_carrossel.html"


class HomeStreamBlock(blocks.StreamBlock):
    """
    Agrega todos os blocos da Home em um `StreamBlock` reutilizável.

    `required=False` permite que a Home renderize corretamente mesmo com o
    `body` vazio (estado inicial limpo).
    """

    hero = HeroBlock()
    full_banner = FullBannerBlock()
    carrossel_categoria = CarrosselCategoriaBlock()
    destaques_manuais = DestaquesManuaisBlock()
    feature_grid = FeatureGridBlock()
    ultimo_conteudo_player = UltimoConteudoPlayerBlock()
    ultimos_conteudos_carrossel = UltimosConteudosCarrosselBlock()

    class Meta:
        required = False