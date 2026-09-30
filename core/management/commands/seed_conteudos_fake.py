"""
Semeia conteúdo fake nos canais para permitir teste visual dos blocos
de fallback (hero player + carrossel) da página de canal.

Uso: ``python manage.py seed_conteudos_fake``. Idempotente: a checagem
por (canal, título) pula conteúdos já criados em execuções anteriores.
Downloads externos podem falhar offline; nesse caso o conteúdo é criado
só com metadados e source (o fallback visual continua exercitável).
"""

import requests
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

# Placeholders de vídeo/áudio NÃO usados no seed comprometem o player se a
# URL não existir; downloads com falha são ignorados com warning.
SAMPLE_VIDEO_URL = "https://videos.pexels.com/videos/3264594/video-preview.mp4"
SAMPLE_AUDIO_URL = "https://videos.pexels.com/videos/2103023/audio-preview.mp3"


class Command(BaseCommand):
    help = "Populate the database with realistic fake content for testing"

    def handle(self, *args, **options):
        self.stdout.write("Seeding fake content...")

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
                if ConteudoPage.objects.child_of(canal).filter(
                    title=title
                ).exists():
                    self.stdout.write(
                        f"  Content '{title}' already exists under {canal.name}. Skipping."
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
            self._attach_remote_file(
                content, SAMPLE_VIDEO_URL, f"video_{content.slug}.mp4", kind="video"
            )
        elif mecanismo == ConteudoPage.MECANISMO_AUDIO:
            content.source = SAMPLE_AUDIO_URL
            self._attach_remote_file(
                content, SAMPLE_AUDIO_URL, f"audio_{content.slug}.mp3", kind="audio"
            )
        elif mecanismo == ConteudoPage.MECANISMO_DOCUMENTO_PDF:
            content.source = "https://www.example.com/sample.pdf"
            content.arquivo.save(
                f"documento_{content.slug}.pdf",
                ContentFile(MINIMAL_PDF),
                save=False,
            )
        elif mecanismo == ConteudoPage.MECANISMO_LINK_EXTERNO:
            content.source = "https://example.com"
            # link_externo não carrega arquivo

    def _attach_remote_file(self, content, url, filename, kind):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f"  Download de {kind} falhou ({url}): {exc}")
            )
            return
        content.arquivo.save(filename, ContentFile(response.content), save=False)

    def _set_og_image(self, content, title):
        """
        og_image é FK para o model de imagem do Wagtail (BasePage), não um
        ImageField — exige criar/recuperar um objeto Image e atribuir a FK.
        """
        Image = get_image_model()
        image_title = f"og {title}"[:100]
        existing = Image.objects.filter(title=image_title).first()
        if existing is not None:
            content.og_image = existing
            return
        og_image_url = f"https://via.placeholder.com/1200x630.png?text={content.slug}"
        try:
            response = requests.get(og_image_url, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(f"  Download de og_image falhou: {exc}")
            )
            return
        image = Image(title=image_title)
        image.file.save(
            f"og_image_{content.slug}.png",
            ContentFile(response.content),
            save=False,
        )
        image.save()
        content.og_image = image
