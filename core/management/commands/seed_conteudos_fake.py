"""
Semeia conteúdo fake nos canais para permitir teste visual dos blocos
de fallback (hero player + carrossel) da página de canal.

Uso: ``python manage.py seed_conteudos_fake [--force]``. Idempotente:
a checagem por (canal, ``options.indice``) pula conteúdos já criados;
``--force`` mantém a página e regenera mecanismo/título/mídia/capa.

Cobre os 7 mecanismos de exibição, nos dois modos de mídia:
- MODO A (upload em ``arquivo``): video, audio, documento_pdf,
  apresentacao, download_binario.
- MODO B (URL externa em ``source``): link_externo e animacao_externa,
  com URLs reais de plataforma (YouTube/Vimeo/Spotify) — resolvidas por
  ``{% embed %}`` no template — e uma URL não-embeddável para exercitar
  o fallback de link seguro.

Mídia real e offline-determinística: MP3/MP4 versionados em
``core/fixtures/seed_media/`` (gerados uma vez com ffmpeg; o seed não
depende de ffmpeg, rede ou faker-file), PDF mínimo e ZIP gerados em
memória, e capas PNG desenhadas com Pillow.
"""

import zipfile
from io import BytesIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from wagtail.images import get_image_model
from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import CategoriaConteudo, ConteudoPage, Licenca, Tipo
from curriculo.models import CurricularComponent


MINIMAL_PDF = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
70 720 TD
/F1 24 Tf
(Fake PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000053 00000 n
0000000102 00000 n
0000000175 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
245
%%EOF
"""

# Mídia de exemplo REAL, versionada no repositório (core/fixtures/seed_media/).
# Geradas uma única vez com ffmpeg e commitadas: o seed não depende de ffmpeg
# em tempo de execução, nem de rede, nem de faker-file (cujos providers de
# mídia exigem geradores opcionais — imgkit/pdfkit/gtts — ausentes na imagem).
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "seed_media"
SAMPLE_AUDIO_PATH = FIXTURES_DIR / "sample_audio.mp3"
SAMPLE_VIDEO_PATH = FIXTURES_DIR / "sample_video.mp4"

# MODO A: upload em `arquivo`. MODO B: URL externa em `source`.
# Nenhum mecanismo usa os dois campos ao mesmo tempo (ver ARCHITECTURE.md).
MECANISMOS_UPLOAD = (
    ConteudoPage.MECANISMO_VIDEO,
    ConteudoPage.MECANISMO_AUDIO,
    ConteudoPage.MECANISMO_DOCUMENTO_PDF,
    ConteudoPage.MECANISMO_APRESENTACAO,
    ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
)
MECANISMOS_URL = (
    ConteudoPage.MECANISMO_LINK_EXTERNO,
    ConteudoPage.MECANISMO_ANIMACAO_EXTERNA,
)

# Ordem do ciclo de mecanismos por canal. O deslocamento por canal (ver handle)
# faz o conteúdo mais recente — o que o hero exibe — variar entre os canais:
# player de vídeo, player de áudio, embed (MODO B) e visualizador de PDF.
MECANISMOS_CICLO = (
    ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
    ConteudoPage.MECANISMO_APRESENTACAO,
    ConteudoPage.MECANISMO_VIDEO,
    ConteudoPage.MECANISMO_AUDIO,
    ConteudoPage.MECANISMO_LINK_EXTERNO,
    ConteudoPage.MECANISMO_ANIMACAO_EXTERNA,
    ConteudoPage.MECANISMO_DOCUMENTO_PDF,
)

# URLs de plataforma, resolvidas por {% embed %} (oEmbed) no template.
# Ordem importa: o hero usa o índice final do ciclo, então as plataformas com
# embed 16:9 (YouTube/Vimeo) ficam nas posições que o hero alcança.
SAMPLE_EMBED_URLS = (
    "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    "https://vimeo.com/1084537",
)
# URL válida porém NÃO-embeddável: exercita o fallback de link seguro.
SAMPLE_FALLBACK_URL = "https://example.com/material-externo"

# Cores da paleta brand (mesmos valores do tailwind.config do base.html).
BRAND_700 = (30, 58, 138)
BRAND_600 = (30, 64, 175)
BRAND_500 = (29, 78, 216)
BRAND_100 = (217, 230, 255)

# Glifos FontAwesome por mecanismo (a fonte vem do static do DRF já instalado).
GLIFOS_POR_MECANISMO = {
    ConteudoPage.MECANISMO_VIDEO: "\uf008",             # film
    ConteudoPage.MECANISMO_AUDIO: "\uf001",             # music
    ConteudoPage.MECANISMO_DOCUMENTO_PDF: "\uf15c",     # file-text
    ConteudoPage.MECANISMO_APRESENTACAO: "\uf108",      # desktop
    ConteudoPage.MECANISMO_DOWNLOAD_BINARIO: "\uf019",  # download
    ConteudoPage.MECANISMO_LINK_EXTERNO: "\uf0c1",      # link
    ConteudoPage.MECANISMO_ANIMACAO_EXTERNA: "\uf04b",  # play
}


def _fonte_icones_path():
    """Caminho da fonte FontAwesome (static do DRF); None se indisponível."""
    try:
        import rest_framework

        caminho = (
            Path(rest_framework.__file__).parent
            / "static"
            / "rest_framework"
            / "fonts"
            / "fontawesome-webfont.ttf"
        )
        return caminho if caminho.exists() else None
    except Exception:
        return None


class Command(BaseCommand):
    help = "Populate the database with realistic fake content for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenera arquivo/og_image de conteúdos já semeados.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding fake content...")
        force = options["force"]

        tipo, _ = Tipo.objects.get_or_create(
            name="Tipo Genérico para Testes",
            defaults={
                "slug": "tipo-generico-para-testes",
                "description": "Tipo usado para conteúdos de teste, permite todas as extensões.",
                "options": {"formatos": []},
                "is_active": True,
                "ordem": 0,
            },
        )

        licenca, _ = Licenca.objects.get_or_create(
            name="Licença de Teste",
            defaults={
                "slug": "licenca-de-teste",
                "description": "Licença usada para conteúdos de teste.",
                "url": "https://creativecommons.org/licenses/by/4.0/",
                "is_active": True,
                "ordem": 0,
            },
        )

        # autor é FK PROTECT obrigatória (RecursoBasePage) — sem ela, falha no banco
        autor = self._get_or_create_autor()

        curricular_component = self._get_curricular_component()
        if curricular_component is None:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhum CurricularComponent disponível; M2M ficará vazio."
                )
            )

        canals = self._ensure_canals()

        # Ciclo com os 7 mecanismos (10 itens por canal: todos aparecem e os 3
        # primeiros repetem, dando volume ao carrossel). O deslocamento por
        # canal varia qual mecanismo é o mais recente — ou seja, o que o hero
        # exibe — cobrindo player de vídeo, de áudio, embed (MODO B) e PDF.
        mechanisms = MECANISMOS_CICLO

        for canal_index, canal in enumerate(canals):
            self.stdout.write(f"Creating fake content for canal: {canal.name}")
            # category é FK PROTECT obrigatória e escopada por canal (D2/D4)
            categoria, _ = CategoriaConteudo.objects.get_or_create(
                slug="categoria-de-teste",
                canal=canal,
                defaults={
                    "name": f"Categoria de Teste ({canal.name})",
                    "is_active": True,
                    "ordem": 0,
                },
            )

            for i in range(10):
                mechanism = mechanisms[(i + canal_index) % len(mechanisms)]
                title = f"{canal.name} - Conteúdo Educacional {i + 1} - {mechanism}"

                # Idempotência por (canal, indice): estável mesmo quando o ciclo
                # de mecanismos muda. Fallback por título para registros antigos
                # que ainda não tenham `options.indice`.
                existing = (
                    ConteudoPage.objects.child_of(canal)
                    .filter(options__indice=i)
                    .first()
                )
                if existing is None:
                    existing = (
                        ConteudoPage.objects.child_of(canal)
                        .filter(title=title)
                        .first()
                    )
                if existing is not None:
                    if not force:
                        self.stdout.write(
                            f"  Content '{title}' already exists under {canal.name}. Skipping."
                        )
                        continue
                    # --force: atualiza mecanismo/título/mídia/capa no lugar,
                    # sem criar página duplicada.
                    existing.mecanismo_exibicao = mechanism
                    existing.title = title
                    existing.options = {**(existing.options or {}), "indice": i}
                    self._set_mecanismo_payload(existing, mechanism, force=True)
                    self._set_og_image(existing, title, force=True)
                    existing.save_revision().publish()
                    self.stdout.write(
                        self.style.SUCCESS(f'  Refreshed content: "{title}"')
                    )
                    continue

                content = ConteudoPage(
                    title=title,
                    slug=slugify(title)[:250],
                    canal=canal,
                    autor=autor,
                    tipo=tipo,
                    category=categoria,
                    license=licenca,
                    mecanismo_exibicao=mechanism,  # nome correto do campo
                    is_approved=True,
                    authors="Autor de Teste, outro Autor",
                    options={"teste": True, "indice": i},
                )

                self._set_mecanismo_payload(content, mechanism)
                self._set_og_image(content, title)

                # Wagtail/treebeard: salvar página órfã (save() sem add_child)
                # deixa path/depth nulos e quebra. add_child primeiro.
                canal.add_child(instance=content)
                if curricular_component is not None:
                    content.componentes_curriculares.add(curricular_component)
                content.save_revision().publish()

                self.stdout.write(
                    self.style.SUCCESS(f'  Created content: "{content.title}"')
                )

        self.stdout.write(self.style.SUCCESS("Finished seeding fake content."))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_autor(self):
        User = get_user_model()
        autor = User.objects.filter(is_superuser=True).first()
        if autor is None:
            autor = User.objects.create_superuser(
                username="seed_autor",
                email="seed@example.com",
                password="seed_autor_senha_teste",
            )
            self.stdout.write("Created fallback superuser 'seed_autor'.")
        return autor

    def _get_curricular_component(self):
        """
        Reusa o primeiro CurricularComponent existente; se não houver,
        cria um com os campos mínimos suportados. Retorna None se o model
        exigir campos que não conseguimos suprir (M2M fica opcional no seed).
        """
        existing = CurricularComponent.objects.first()
        if existing is not None:
            return existing
        try:
            # category e nivel são FKs PROTECT obrigatórias no model
            from curriculo.models import CurricularComponentCategory, NivelEnsino

            categoria_cc, _ = CurricularComponentCategory.objects.get_or_create(
                slug="categoria-cc-de-teste",
                defaults={"name": "Categoria de Componente de Teste"},
            )
            nivel, _ = NivelEnsino.objects.get_or_create(
                slug="nivel-de-teste",
                defaults={"name": "Nível de Teste"},
            )
            return CurricularComponent.objects.create(
                name="Componente Curricular de Teste",
                slug="componente-curricular-de-teste",
                category=categoria_cc,
                nivel=nivel,
            )
        except Exception as exc:  # schema divergente do esperado
            self.stdout.write(
                self.style.WARNING(f"Falha ao criar CurricularComponent: {exc}")
            )
            return None

    def _ensure_canals(self):
        """
        Garante os 4 canais esperados. CanalPage é Wagtail Page: precisa ser
        pendurada na árvore via add_child de um parent existente (root),
        caso contrário path/depth ficam nulos e quebram.
        """
        canal_names = [
            "TV Anísio Teixeira",
            "Rádio Anísio Teixeira",
            "EMITEC",
            "Recursos Educacionais",
        ]
        # Parent deve ser o site root (HomePage): canals sob o Wagtail root
        # não são roteáveis (url = None). Reparenta órfãos de execuções antigas.
        parent = Site.objects.get(is_default_site=True).root_page
        for name in canal_names:
            canal = CanalPage.objects.filter(name=name).first()
            if canal is not None:
                if canal.get_site() is None:
                    canal.move(parent, pos="last-child")
                    self.stdout.write(f"Reparented canal: {canal.name}")
                continue
            canal = CanalPage(
                title=name,
                name=name,
                slug=slugify(name),
                description=f"Descrição do {name}.",
                is_active=True,
            )
            parent.add_child(instance=canal)
            canal.save_revision().publish()
            self.stdout.write(f"Created canal: {canal.name}")
        return CanalPage.objects.live().filter(is_active=True).specific()

    def _set_mecanismo_payload(self, content, mechanism, force=False):
        """
        Preenche o campo de mídia conforme o MODO do mecanismo.

        MODO A (upload): grava ``arquivo`` a partir das fixtures reais do repo
        e limpa ``source``. MODO B (URL externa): grava ``source`` e não usa
        ``arquivo``. Nenhum mecanismo usa os dois (regra em ARCHITECTURE.md).
        ``force=True`` sobrescreve mídia existente (corrige stubs antigos).
        """
        mecanismo = content.mecanismo_exibicao
        if mecanismo in MECANISMOS_UPLOAD:
            content.source = ""
            if mecanismo == ConteudoPage.MECANISMO_VIDEO:
                self._attach_arquivo(content, SAMPLE_VIDEO_PATH, "mp4", force)
            elif mecanismo == ConteudoPage.MECANISMO_AUDIO:
                self._attach_arquivo(content, SAMPLE_AUDIO_PATH, "mp3", force)
            elif mecanismo in (
                ConteudoPage.MECANISMO_DOCUMENTO_PDF,
                ConteudoPage.MECANISMO_APRESENTACAO,
            ):
                self._attach_bytes(content, MINIMAL_PDF, "pdf", force)
            else:  # download_binario
                self._attach_bytes(content, self._make_zip_bytes(), "zip", force)
            return

        # MODO B — URL externa: sem arquivo, só source.
        content.arquivo = None
        content.source = self._embed_url_for(content)

    def _embed_url_for(self, content):
        """Alterna URLs embedáveis e uma não-embeddável (fallback do template)."""
        indice = (content.options or {}).get("indice", 0)
        # Um em cada cinco conteúdos usa URL não-embeddável, para exercitar o
        # fallback de link seguro sem esvaziar o hero dos canais de MODO B.
        if indice % 5 == 3:
            return SAMPLE_FALLBACK_URL
        return SAMPLE_EMBED_URLS[indice % len(SAMPLE_EMBED_URLS)]

    @staticmethod
    def _make_zip_bytes():
        """Pacote .zip real e determinístico (timestamp fixo) para download."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            info = zipfile.ZipInfo("leia-me.txt", date_time=(2026, 1, 1, 0, 0, 0))
            zf.writestr(info, "Pacote de teste da Nova PAT.\n")
        return buffer.getvalue()

    def _attach_arquivo(self, content, path, ext, force):
        """Copia uma fixture de mídia do repo para o campo ``arquivo``."""
        if content.arquivo and not force:
            return
        caminho = Path(path)
        if not caminho.exists():
            self.stdout.write(self.style.WARNING(f"  Fixture ausente: {caminho}"))
            return
        self._attach_bytes(content, caminho.read_bytes(), ext, force)

    def _attach_bytes(self, content, data, ext, force):
        """Grava bytes no campo ``arquivo`` (sobrescreve quando ``force``)."""
        if content.arquivo and not force:
            return
        if content.arquivo:
            content.arquivo.delete(save=False)
        content.arquivo.save(
            f"{content.mecanismo_exibicao}_{content.slug}.{ext}",
            ContentFile(data),
            save=False,
        )

    def _set_og_image(self, content, title, force=False):
        """
        og_image é FK para o model de imagem do Wagtail (BasePage), não um
        ImageField — exige criar/recuperar um objeto Image e atribuir a FK.
        Capa desenhada offline com Pillow: gradiente da marca, glifo do
        mecanismo (fonte de ícones do static do DRF) e título com a fonte
        escalável embutida do Pillow. ``force=True`` redesenha a capa.
        """
        Image = get_image_model()
        image = content.og_image if content.og_image_id else None
        if image is not None and not force:
            return
        image_title = f"og {title}"[:100]
        if image is None:
            image = Image.objects.filter(title=image_title).first()
            if image is None:
                image = Image(title=image_title)
            elif not force:
                content.og_image = image
                return

        png_bytes = self._render_cover(content)
        if png_bytes is None:
            return

        from django.core.files.images import ImageFile

        # ImageFile não commitado: o save() calcula width/height (NOT NULL).
        image.file = ImageFile(
            BytesIO(png_bytes), name=f"og_image_{content.slug}.png"
        )
        try:
            image.save()
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f"  Falha ao salvar og_image: {exc}")
            )
            return
        content.og_image = image

    def _render_cover(self, content):
        """Desenha a capa 1200x630 e devolve os bytes PNG (None se falhar)."""
        from PIL import Image as PILImage
        from PIL import ImageDraw

        largura, altura = 1200, 630
        img = PILImage.new("RGB", (largura, altura), color=BRAND_700)
        draw = ImageDraw.Draw(img)

        # Gradiente vertical brand-700 -> brand-500
        for y in range(altura):
            t = y / (altura - 1)
            draw.line(
                [(0, y), (largura, y)],
                fill=tuple(
                    int(BRAND_700[i] + (BRAND_500[i] - BRAND_700[i]) * t)
                    for i in range(3)
                ),
            )
        # Faixa diagonal em brand-600, para dar movimento à composição
        draw.polygon(
            [(-80, 470), (largura, 300), (largura, 420), (-80, 590)],
            fill=BRAND_600,
        )

        # Glifo do mecanismo
        fonte_icone = self._load_icon_font(140)
        glifo = GLIFOS_POR_MECANISMO.get(content.mecanismo_exibicao, "")
        if fonte_icone is not None and glifo:
            draw.text((largura - 220, 80), glifo, font=fonte_icone, fill=BRAND_100)

        # Título em até 2 linhas
        fonte_titulo = self._load_text_font(54)
        linhas = self._wrap_text(
            draw, content.title, fonte_titulo, largura - 120, max_linhas=2
        )
        y = 160
        for linha in linhas:
            draw.text((60, y), linha, font=fonte_titulo, fill=(255, 255, 255))
            y += 68

        # Rodapé: canal + mecanismo
        fonte_rodape = self._load_text_font(26)
        canal = content.canal.name if content.canal else ""
        rodape = f"{canal} · {content.mecanismo_exibicao}"[:80]
        draw.text((60, altura - 64), rodape, font=fonte_rodape, fill=BRAND_100)

        buffer = BytesIO()
        try:
            img.save(buffer, format="PNG", optimize=True)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  Falha ao desenhar capa: {exc}"))
            return None
        return buffer.getvalue()

    @staticmethod
    def _load_text_font(size):
        """Fonte de texto escalável embutida no Pillow (10.1+)."""
        from PIL import ImageFont

        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def _load_icon_font(size):
        """Fonte de ícones do static do DRF; None se indisponível."""
        from PIL import ImageFont

        caminho = _fonte_icones_path()
        if caminho is None:
            return None
        try:
            return ImageFont.truetype(str(caminho), size)
        except Exception:
            return None

    @staticmethod
    def _wrap_text(draw, texto, fonte, largura_max, max_linhas=2):
        """Quebra o texto em no máximo ``max_linhas``; corta com reticências."""
        palavras = texto.split()
        linhas, atual = [], ""
        for palavra in palavras:
            tentativa = f"{atual} {palavra}".strip()
            if not atual or draw.textlength(tentativa, font=fonte) <= largura_max:
                atual = tentativa
                continue
            linhas.append(atual)
            atual = palavra
            if len(linhas) == max_linhas:
                break
        if atual and len(linhas) < max_linhas:
            linhas.append(atual)
        if len(linhas) == max_linhas and len(" ".join(linhas).split()) < len(palavras):
            while linhas[-1] and draw.textlength(
                linhas[-1] + "…", font=fonte
            ) > largura_max:
                linhas[-1] = linhas[-1][:-1].rstrip()
            linhas[-1] = f"{linhas[-1]}…"
        return linhas
