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

from core.models import RedeSocial, SiteSettings
from core.wagtail_hooks import RedeSocialForm

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


class RedeSocialTest(TestCase):
    """Testes do model `core.models.RedeSocial` (NOVAPAT-68).

    Cobre:
    - detecção automática de tipo por URL (Instagram, YouTube, Facebook, Flickr);
    - preenchimento automático do nome com base na rede social detectada;
    - rejeição de endereços de rede social não suportada;
    - associação automática ao SiteSettings do site default;
    - valor default de `ativo` (True);
    - ordenação por `sort_order`;
    - propriedade `icone_classe_efetiva` (classe Font Awesome do tipo detectado);
    - `__str__` retorna o nome da rede social.
    """

    def setUp(self):
        self.site, _ = Site.objects.get_or_create(
            is_default_site=True,
            defaults={
                "hostname": "localhost",
                "port": 80,
                "site_name": "Nova PAT",
            },
        )
        self.settings = SiteSettings.objects.create(site=self.site)

    def _make_rede(self, **kwargs):
        dados = dict(
            site_settings=self.settings,
            url="https://www.instagram.com/novapat",
            ativo=True,
            sort_order=0,
        )
        dados.update(kwargs)
        return RedeSocial.objects.create(**dados)

    def test_criacao_rede_social(self):
        """RedeSocial aceita URL e ativo; tipo e nome são preenchidos automaticamente."""
        rede = self._make_rede()
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_INSTAGRAM)
        self.assertEqual(rede.nome, "Instagram")
        self.assertEqual(rede.url, "https://www.instagram.com/novapat")
        self.assertTrue(rede.ativo)
        self.assertEqual(rede.site_settings, self.settings)

    def test_nome_eh_preenchido_automaticamente(self):
        """O nome é preenchido com base no tipo de rede social detectado."""
        rede = self._make_rede(url="https://www.youtube.com/novapat")
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_YOUTUBE)
        self.assertEqual(rede.nome, "YouTube")

    def test_ativo_default_eh_true(self):
        """Quando não informado, `ativo` padrão é True."""
        rede = RedeSocial.objects.create(
            site_settings=self.settings, url="https://youtube.com/novapat"
        )
        self.assertTrue(rede.ativo)

    def test_ordenacao_por_sort_order(self):
        """Redes sociais são ordenadas por `sort_order` (menor primeiro)."""
        rede_a = self._make_rede(url="https://www.instagram.com/a", sort_order=10)
        rede_b = self._make_rede(url="https://www.instagram.com/b", sort_order=5)
        redes = list(RedeSocial.objects.filter(site_settings=self.settings))
        self.assertEqual([r.pk for r in redes], [rede_b.pk, rede_a.pk])

    def test_str_retorna_nome(self):
        """__str__ retorna o nome da rede social."""
        rede = self._make_rede()
        self.assertEqual(str(rede), "Instagram")

    def test_icone_url_eh_none_sem_upload(self):
        """Não há upload de ícone, então `icone_url` é sempre None."""
        rede = self._make_rede()
        self.assertIsNone(rede.icone_url)

    def test_detecta_tipo_por_url_instagram(self):
        """URL do Instagram é detectada automaticamente como instagram."""
        rede = self._make_rede()
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_INSTAGRAM)

    def test_detecta_tipo_por_url_youtube(self):
        """URL do YouTube é detectada automaticamente como youtube."""
        rede = self._make_rede(url="https://www.youtube.com/novapat")
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_YOUTUBE)

    def test_detecta_tipo_por_url_youtube_curto(self):
        """URL curta do YouTube (youtu.be) é detectada como youtube."""
        rede = self._make_rede(url="https://youtu.be/abc123")
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_YOUTUBE)

    def test_detecta_tipo_por_url_facebook(self):
        """URL do Facebook é detectada automaticamente como facebook."""
        rede = self._make_rede(url="https://www.facebook.com/novapat")
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_FACEBOOK)

    def test_detecta_tipo_por_url_flickr(self):
        """URL do Flickr é detectada automaticamente como flickr."""
        rede = self._make_rede(url="https://www.flickr.com/novapat")
        self.assertEqual(rede.tipo_rede, RedeSocial.TIPO_REDE_FLICKR)

    def test_url_nao_suportada_leva_validation_error(self):
        """Endereço de rede social não suportada levanta ValidationError ao salvar."""
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            RedeSocial.objects.create(
                site_settings=self.settings,
                url="https://www.exemplo.com/perfil",
            )

    def test_site_settings_eh_associado_automaticamente(self):
        """Quando não informado, `site_settings` é associado ao site default."""
        rede = RedeSocial.objects.create(url="https://www.instagram.com/novapat")
        self.assertEqual(rede.site_settings, self.settings)

    def test_icone_classe_efetiva_retorna_classe_por_tipo(self):
        """`icone_classe_efetiva` retorna a classe Font Awesome do tipo detectado."""
        rede = self._make_rede(url="https://www.youtube.com/novapat")
        self.assertEqual(rede.icone_classe_efetiva, "fa-youtube")

    def test_form_filtra_redes_ja_cadastradas(self):
        """O seletor do formulário não exibe redes sociais já cadastradas."""
        # Cadastra Instagram
        RedeSocial.objects.create(
            site_settings=self.settings,
            url="https://www.instagram.com/novapat",
        )
        form = RedeSocialForm()
        choices = dict(form.fields["tipo_rede"].choices)
        self.assertNotIn("instagram", choices)
        self.assertIn("youtube", choices)
        self.assertIn("facebook", choices)
        self.assertIn("flickr", choices)

    def test_form_exibe_todas_redes_quando_nenhuma_cadastrada(self):
        """Quando nenhuma rede está cadastrada, o seletor exibe todas as opções."""
        form = RedeSocialForm()
        choices = dict(form.fields["tipo_rede"].choices)
        self.assertIn("instagram", choices)
        self.assertIn("youtube", choices)
        self.assertIn("facebook", choices)
        self.assertIn("flickr", choices)
