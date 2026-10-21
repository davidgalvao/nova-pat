"""
Testes para `core.models.SiteSettings` (NOVAPAT-60).

Cobre:
- criação de configurações com nome do site e logotipo;
- sincronização de `save()` com `Site.site_name` do site padrão;
- valores default (sem nome, sem logo);
- comportamento `on_delete=SET_NULL` do campo logo ao deletar a imagem.
"""

import io

from PIL import Image as PILImage
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.models import Site
from wagtail.images import get_image_model

from core.models import SiteSettings

Image = get_image_model()


def _make_png_image(title="Logo teste"):
    """Cria uma imagem PNG válida em memória para testes de upload."""
    buffer = io.BytesIO()
    pil_image = PILImage.new("RGB", (10, 10), color="red")
    pil_image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(f"{title}.png", buffer.read(), content_type="image/png")


def _make_image(title="Logo teste"):
    """Cria uma imagem de teste válida no banco."""
    return Image.objects.create(
        title=title,
        file=_make_png_image(title),
    )


class SiteSettingsTest(TestCase):
    """Testes do model `SiteSettings` (configurações editáveis do site)."""

    def setUp(self):
        # Garante um site padrão para os testes de sincronização.
        self.site, _ = Site.objects.get_or_create(
            is_default_site=True,
            defaults={
                "hostname": "localhost",
                "port": 80,
                "site_name": "Nova PAT",
            },
        )

    def test_criacao_com_site_name_e_logo(self):
        """SiteSettings aceita nome do site e upload de logotipo."""
        imagem = _make_image()
        settings = SiteSettings.objects.create(
            site=self.site,
            site_name="Nova PAT Educacional",
            logo=imagem,
        )
        self.assertEqual(settings.site_name, "Nova PAT Educacional")
        self.assertEqual(settings.logo, imagem)
        self.assertEqual(settings.site, self.site)

    def test_save_sincroniza_site_name_com_site_padrao(self):
        """save() grava o nome do site em Site.site_name do site padrão."""
        imagem = _make_image()
        settings = SiteSettings.objects.create(
            site=self.site,
            site_name="Meu Site Customizado",
            logo=imagem,
        )
        self.site.refresh_from_db()
        self.assertEqual(self.site.site_name, "Meu Site Customizado")

    def test_valores_default_sem_nome_e_sem_logo(self):
        """Sem preenchimento, site_name é vazio e logo é None."""
        settings = SiteSettings.objects.create(site=self.site)
        self.assertEqual(settings.site_name, "")
        self.assertIsNone(settings.logo)

    def test_str_retorna_site_name_ou_fallback(self):
        """__str__ retorna site_name quando preenchido, senão o fallback."""
        settings_com_nome = SiteSettings.objects.create(site=self.site, site_name="Nome X")
        self.assertEqual(str(settings_com_nome), "Nome X")

        # Mesmo site, outro registro não é permitido (site é unique=True),
        # então testamos o fallback excluindo o primeiro.
        settings_com_nome.delete()
        settings_sem_nome = SiteSettings.objects.create(site=self.site)
        self.assertEqual(str(settings_sem_nome), "Configurações do site")

    def test_logo_on_delete_set_null(self):
        """Deletar a imagem do logo não deleta o SiteSettings (SET_NULL)."""
        imagem = _make_image()
        settings = SiteSettings.objects.create(site=self.site, logo=imagem)
        imagem_id = imagem.pk
        imagem.delete()
        settings.refresh_from_db()
        self.assertIsNone(settings.logo)
        self.assertTrue(SiteSettings.objects.filter(pk=settings.pk).exists())
