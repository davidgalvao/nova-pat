"""
Testes do management command ``seed_conteudos_fake``: criação,
idempotência e regeneração de mídia com ``--force``.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from canais.models import CanalPage
from conteudos.models import ConteudoPage


class SeedConteudosFakeTestCase(TestCase):
    def _run_seed(self, **kwargs):
        out = StringIO()
        call_command("seed_conteudos_fake", stdout=out, **kwargs)
        return out.getvalue()

    def test_cria_conteudos_nos_canais(self):
        self._run_seed()
        canals = CanalPage.objects.live()
        self.assertGreaterEqual(canals.count(), 4)
        self.assertEqual(ConteudoPage.objects.count(), 10 * canals.count())
        for canal in canals:
            qs = ConteudoPage.objects.live().child_of(canal).filter(
                is_approved=True
            )
            self.assertEqual(qs.count(), 10, canal.name)
            mecanismos = set(qs.values_list("mecanismo_exibicao", flat=True))
            self.assertIn(ConteudoPage.MECANISMO_VIDEO, mecanismos)
            self.assertIn(ConteudoPage.MECANISMO_LINK_EXTERNO, mecanismos)

    def test_conteudo_video_tem_arquivo_e_og_image(self):
        self._run_seed()
        video = ConteudoPage.objects.filter(
            mecanismo_exibicao=ConteudoPage.MECANISMO_VIDEO
        ).first()
        self.assertTrue(video.arquivo)
        self.assertIsNotNone(video.og_image_id)

    def test_canais_orfaos_sao_reparentados_ao_site_root(self):
        """Canal esperado pendurado no Wagtail root (url=None) é movido."""
        from wagtail.models import Page, Site

        root = Page.get_first_root_node()
        orfao = CanalPage(
            title="Recursos Educacionais",
            name="Recursos Educacionais",
            slug="recursos-educacionais",
            is_active=True,
        )
        root.add_child(instance=orfao)
        orfao.save_revision().publish()
        self.assertIsNone(orfao.get_site())

        self._run_seed()
        orfao.refresh_from_db()
        self.assertEqual(
            orfao.get_parent().pk,
            Site.objects.get(is_default_site=True).root_page.pk,
        )

    def test_idempotente_segunda_execucao_nao_duplica(self):
        self._run_seed()
        total = ConteudoPage.objects.count()
        out = self._run_seed()
        self.assertEqual(ConteudoPage.objects.count(), total)
        self.assertIn("Skipping.", out)

    def test_force_regenera_midia_ausente(self):
        self._run_seed()
        conteudo = ConteudoPage.objects.filter(
            mecanismo_exibicao=ConteudoPage.MECANISMO_VIDEO
        ).first()
        # Simular execução anterior sem mídia (rede bloqueada)
        conteudo.arquivo = None
        conteudo.og_image = None
        conteudo.save()

        self._run_seed(force=True)
        conteudo.refresh_from_db()
        self.assertTrue(conteudo.arquivo)
        self.assertIsNotNone(conteudo.og_image_id)

    def test_cobre_os_sete_mecanismos(self):
        """Cada canal deve cobrir os 7 mecanismos de exibição."""
        self._run_seed()
        esperados = {escolha[0] for escolha in ConteudoPage.MECANISMO_CHOICES}
        encontrados = set(
            ConteudoPage.objects.values_list("mecanismo_exibicao", flat=True)
        )
        self.assertEqual(encontrados, esperados)

    def test_modos_de_midia_sao_exclusivos(self):
        """MODO A usa só `arquivo`; MODO B usa só `source` (ver ARCHITECTURE.md)."""
        self._run_seed()
        modo_upload = {
            ConteudoPage.MECANISMO_VIDEO,
            ConteudoPage.MECANISMO_AUDIO,
            ConteudoPage.MECANISMO_DOCUMENTO_PDF,
            ConteudoPage.MECANISMO_APRESENTACAO,
            ConteudoPage.MECANISMO_DOWNLOAD_BINARIO,
        }
        for conteudo in ConteudoPage.objects.all():
            if conteudo.mecanismo_exibicao in modo_upload:
                self.assertTrue(conteudo.arquivo, conteudo.mecanismo_exibicao)
                self.assertEqual(conteudo.source, "", conteudo.mecanismo_exibicao)
            else:
                self.assertFalse(conteudo.arquivo, conteudo.mecanismo_exibicao)
                self.assertTrue(conteudo.source, conteudo.mecanismo_exibicao)

    def test_midia_gerada_e_real_nao_um_stub(self):
        """CASO C: a mídia do seed precisa ser tocável, não um stub de 10 bytes."""
        self._run_seed()
        for mecanismo, minimo, assinatura in (
            (ConteudoPage.MECANISMO_VIDEO, 1024, b"ftyp"),
            (ConteudoPage.MECANISMO_AUDIO, 1024, b"ID3"),
        ):
            conteudo = ConteudoPage.objects.filter(
                mecanismo_exibicao=mecanismo
            ).first()
            self.assertIsNotNone(conteudo.arquivo, mecanismo)
            self.assertGreater(conteudo.arquivo.size, minimo, mecanismo)
            with conteudo.arquivo.open("rb") as arquivo:
                cabecalho = arquivo.read(12)
            if assinatura == b"ID3":
                self.assertTrue(
                    cabecalho.startswith(b"ID3") or cabecalho[0] == 0xFF,
                    f"{mecanismo}: cabeçalho inesperado {cabecalho!r}",
                )
            else:
                self.assertIn(assinatura, cabecalho, mecanismo)
