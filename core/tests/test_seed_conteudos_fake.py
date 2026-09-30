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
