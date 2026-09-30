"""
Semeia conteúdo fake nos canais para permitir teste visual dos blocos
de fallback (hero player + carrossel) da página de canal.

Uso: ``python manage.py seed_conteudos_fake [--force]``. Idempotente:
a checagem por (canal, título) pula conteúdos já criados; ``--force``
mantém o conteúdo mas regenera ``arquivo``/``og_image`` ausentes.

Mídia gerada localmente (offline-determinístico): PNG de capa via
Pillow, PDF mínimo embutido e stubs MP4/MP3 (renderizam os players,
não tocam). Sem dependência de rede externa.
"""

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from wagtail.images import get_image_model
from wagtail.models import Page

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

# Stubs mínimos: fazem os elementos <video>/<audio> renderizarem os controles
# (suficiente para teste visual do hero), sem depender de rede.
MINIMAL_MP4 = (
    b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41"
    b"\x00\x00\x00\x08free"
    b"\x00\x00\x00\x08mdat"
)
MINIMAL_MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00"

SAMPLE_VIDEO_URL = "https://www.pexels.com/video/3264594/"
SAMPLE_AUDIO_URL = "https://www.pexels.com/audio/2103023/"


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

        mechanisms = [
            ConteudoPage.MECANISMO_VIDEO,
            ConteudoPage.MECANISMO_AUDIO,
            ConteudoPage.MECANISMO_DOCUMENTO_PDF,
            ConteudoPage.MECANISMO_LINK_EXTERNO,
        ]

        for canal in canals:
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
                mechanism = mechanisms[i % len(mechanisms)]
                title = f"{canal.name} - Conteúdo Educacional {i + 1} - {mechanism}"

                # Idempotência: child_of é método de queryset, não argumento de filter
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
                    # --force: regenera mídia ausente sem duplicar a página
                    self._set_mecanismo_payload(existing, mechanism)
                    self._set_og_image(existing, title)
                    existing.save_revision().publish()
                    self.stdout.write(
                        f'  Refreshed media on existing content: "{title}"'
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
        parent = Page.get_first_root_node()
        for name in canal_names:
            if CanalPage.objects.filter(name=name).exists():
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

    def _set_mecanismo_payload(self, content, mechanism):
        mecanismo = content.mecanismo_exibicao
        if mecanismo == ConteudoPage.MECANISMO_VIDEO:
            content.source = SAMPLE_VIDEO_URL
            if not content.arquivo:
                content.arquivo.save(
                    f"video_{content.slug}.mp4",
                    ContentFile(MINIMAL_MP4),
                    save=False,
                )
        elif mecanismo == ConteudoPage.MECANISMO_AUDIO:
            content.source = SAMPLE_AUDIO_URL
            if not content.arquivo:
                content.arquivo.save(
                    f"audio_{content.slug}.mp3",
                    ContentFile(MINIMAL_MP3),
                    save=False,
                )
        elif mecanismo == ConteudoPage.MECANISMO_DOCUMENTO_PDF:
            content.source = "https://www.example.com/sample.pdf"
            if not content.arquivo:
                content.arquivo.save(
                    f"documento_{content.slug}.pdf",
                    ContentFile(MINIMAL_PDF),
                    save=False,
                )
        elif mecanismo == ConteudoPage.MECANISMO_LINK_EXTERNO:
            content.source = "https://example.com"
            # link_externo não carrega arquivo

    def _set_og_image(self, content, title):
        """
        og_image é FK para o model de imagem do Wagtail (BasePage), não um
        ImageField — exige criar/recuperar um objeto Image e atribuir a FK.
        Capa gerada localmente via Pillow (offline): cor da marca + título.
        """
        if content.og_image_id:
            return
        Image = get_image_model()
        image_title = f"og {title}"[:100]
        existing = Image.objects.filter(title=image_title).first()
        if existing is not None:
            content.og_image = existing
            return

        from io import BytesIO

        from django.core.files.images import ImageFile
        from PIL import Image as PILImage
        from PIL import ImageDraw

        img = PILImage.new("RGB", (1200, 630), color=(30, 58, 138))  # brand-700
        draw = ImageDraw.Draw(img)
        # Faixa central em brand-500 com o slug como texto simples
        draw.rectangle([(0, 480), (1200, 630)], fill=(29, 78, 216))
        draw.text((40, 540), content.slug[:80], fill=(255, 255, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # ImageFile não commitado: o save() do Wagtail/Django calcula
        # width/height (campos NOT NULL) a partir do arquivo.
        image = Image(title=image_title)
        image.file = ImageFile(
            BytesIO(buffer.getvalue()), name=f"og_image_{content.slug}.png"
        )
        try:
            image.save()
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f"  Falha ao salvar og_image: {exc}")
            )
            return
        content.og_image = image
