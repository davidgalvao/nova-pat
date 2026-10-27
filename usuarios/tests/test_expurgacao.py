"""
Testes da política de retenção de usuário inativo (card NOVAPAT-62).

Cobre o serviço de retenção, a view administrativa e o item de menu, todos
restritos ao nível mais alto de admin (papel ``super-admin``).
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from usuarios.models import User, Role
from usuarios.services import expurgar_usuarios_inativos, usuarios_elegiveis_para_expurgar
from usuarios.wagtail_hooks import ExpurgarInativosMenuItem

# Momento fixo para tornar os prazos de retenção determinísticos nos testes.
FIXED_NOW = timezone.make_aware(datetime(2026, 6, 1, 12, 0, 0))


def _patch_now():
    """Fixa ``usuarios.services.timezone.now`` em FIXED_NOW."""
    return patch("usuarios.services.timezone.now", return_value=FIXED_NOW)


def _criar_usuario(username, email, role_slug="convidado", verified=False,
                   last_login=None, date_joined=None, is_active=True,
                   is_superuser=False):
    role = Role.objects.get(slug=role_slug)
    data = {
        "username": username,
        "email": email,
        "password": "senha-teste-123",
        "role": role,
        "verified": verified,
        "is_active": is_active,
        "is_superuser": is_superuser,
    }
    if last_login is not None:
        data["last_login"] = last_login
    if date_joined is not None:
        data["date_joined"] = date_joined
    return User.objects.create_user(**data)


class RetencaoServicoTestCase(TestCase):
    """Testes para ``usuarios_elegiveis_para_expurgar`` e ``expurgar_usuarios_inativos``."""

    # --- Grupo A: convidado não verificado que nunca acessou (> 3 meses) ---

    def test_convidado_nao_verificado_nao_acessou_mais_de_3_meses_elegivel(self):
        with _patch_now():
            u = _criar_usuario(
                "convidado_antigo", "antigo@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),  # > 90 dias
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertIn(u, resultado["convidados_nao_verificados"])
            self.assertNotIn(u, resultado["ativos_inativos"])

    def test_convidado_nao_verificado_menos_de_3_meses_nao_elegivel(self):
        with _patch_now():
            _criar_usuario(
                "convidado_recente", "recente@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=30),  # < 90 dias
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    def test_convidado_nao_verificado_mas_ja_acessou_nao_elegível_grupo_a(self):
        with _patch_now():
            _criar_usuario(
                "convidado_acessou", "acessou@test.com",
                role_slug="convidado", verified=False,
                last_login=FIXED_NOW - timedelta(days=5),
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    def test_convidado_verificado_nao_elegível(self):
        with _patch_now():
            _criar_usuario(
                "convidado_verificado", "verificado@test.com",
                role_slug="convidado", verified=True, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    # --- Grupo B: ativo inativo (> 18 meses sem login) ---

    def test_ativo_inativo_mais_de_18_meses_elegível(self):
        with _patch_now():
            u = _criar_usuario(
                "ativo_muito_antigo", "muitoantigo@test.com",
                role_slug="coordenador", verified=True,
                last_login=FIXED_NOW - timedelta(days=600),  # > 540 dias
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertIn(u, resultado["ativos_inativos"])

    def test_ativo_inativo_menos_de_18_meses_nao_elegível(self):
        with _patch_now():
            _criar_usuario(
                "ativo_recente", "recente@test.com",
                role_slug="admin", verified=True,
                last_login=FIXED_NOW - timedelta(days=100),  # < 540 dias
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["ativos_inativos"].count(), 0)

    def test_nunca_acessado_sem_role_convidado_nao_elegível(self):
        with _patch_now():
            _criar_usuario(
                "sem_login", "semlogin@test.com",
                role_slug="admin", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)
            self.assertEqual(resultado["ativos_inativos"].count(), 0)

    def test_usuario_ja_desativado_nao_elegível(self):
        with _patch_now():
            _criar_usuario(
                "desativado", "desativado@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
                is_active=False,
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    # --- Preservação de super-admin / superuser ---

    def test_super_admin_nao_elegível_mesmo_antigo(self):
        with _patch_now():
            _criar_usuario(
                "super_admin_antigo", "sa@test.com",
                role_slug="super-admin", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    def test_superuser_nao_elegível_mesmo_antigo(self):
        with _patch_now():
            _criar_usuario(
                "superuser_antigo", "su@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
                is_superuser=True,
            )
            resultado = usuarios_elegiveis_para_expurgar()
            self.assertEqual(resultado["convidados_nao_verificados"].count(), 0)

    # --- Execução do expurgo (soft delete) ---

    def test_execucao_desativa_e_marca_deletado_em(self):
        with _patch_now():
            u = _criar_usuario(
                "expurgo1", "expurgo1@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            admin = _criar_usuario(
                "admin_exec", "admin_exec@test.com",
                role_slug="super-admin",
            )
            resultado = expurgar_usuarios_inativos(
                dry_run=False, executado_por=admin
            )
            self.assertEqual(resultado["dry_run"], False)
            self.assertEqual(resultado["total_expurgados"], 1)
            u.refresh_from_db()
            self.assertFalse(u.is_active)
            self.assertIsNotNone(u.deleted_at)
            self.assertEqual(u.deleted_by, admin)

    def test_dry_run_nao_modifica_nada(self):
        with _patch_now():
            _criar_usuario(
                "dryrun", "dryrun@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            expurgar_usuarios_inativos(dry_run=True)
            self.assertTrue(
                User.objects.filter(username="dryrun", is_active=True).exists()
            )

    def test_nao_elegiveis_nao_sao_expurgados(self):
        with _patch_now():
            _criar_usuario(
                "valido", "valido@test.com",
                role_slug="convidado", verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=30),  # dentro do prazo
            )
            expurgar_usuarios_inativos(dry_run=False)
            self.assertTrue(
                User.objects.filter(username="valido", is_active=True).exists()
            )


class RetencaoViewTestCase(TestCase):
    """Testes da view administrativa de retenção (acesso apenas a super-admin).

    O expurgo em si é feito pelo comando de gestão
    ``expurgar_usuarios_inativos`` (testado em ``RetencaoServicoTestCase``);
    esta view apenas exibe candidatos e já expurgados.
    """

    @classmethod
    def setUpTestData(cls):
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.role_convidado = Role.objects.get(slug="convidado")

    def test_super_admin_acessa_view(self):
        user = User.objects.create_user(
            username="sa_view", email="sa_view@test.com",
            password="senha-teste-123", role=self.role_super_admin,
        )
        self.client.force_login(user)
        url = reverse("usuarios:expurgar_inativos")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_convidado_nao_acessa_view(self):
        user = User.objects.create_user(
            username="conv_view", email="conv_view@test.com",
            password="senha-teste-123", role=self.role_convidado,
        )
        self.client.force_login(user)
        url = reverse("usuarios:expurgar_inativos")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_anonimo_nao_acessa_view(self):
        url = reverse("usuarios:expurgar_inativos")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_view_exibe_candidatos_e_expurgados(self):
        with _patch_now():
            # Cria um convidado elegível (criado > 90 dias, nunca acessou, não verificado)
            User.objects.create_user(
                username="cand", email="cand@test.com",
                password="senha-teste-123", role=self.role_convidado,
                verified=False, last_login=None,
                date_joined=FIXED_NOW - timedelta(days=100),
            )
            # Cria um já expurgado (soft delete)
            exp = User.objects.create_user(
                username="expulso", email="expulso@test.com",
                password="senha-teste-123", role=self.role_convidado,
            )
            exp.soft_delete(deleted_by=None)

            admin = User.objects.create_user(
                username="sa_exec_view", email="sa_exec_view@test.com",
                password="senha-teste-123", role=self.role_super_admin,
            )
            self.client.force_login(admin)
            url = reverse("usuarios:expurgar_inativos")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "cand")
            self.assertContains(response, "expulso")


class RetencaoMenuItemTestCase(TestCase):
    """Testes do item de menu de retenção (visível apenas a super-admin)."""

    @classmethod
    def setUpTestData(cls):
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.role_convidado = Role.objects.get(slug="convidado")
        cls.factory = RequestFactory()

    def test_menu_item_mostrado_para_super_admin(self):
        request = self.factory.get("/admin/usuarios/expurgar-inativos/")
        user = User.objects.create_user(
            username="sa_menu", email="sa_menu@test.com",
            password="senha-teste-123", role=self.role_super_admin,
        )
        request.user = user
        item = ExpurgarInativosMenuItem()
        self.assertTrue(item.is_shown(request))

    def test_menu_item_oculto_para_convidado(self):
        request = self.factory.get("/admin/usuarios/expurgar-inativos/")
        user = User.objects.create_user(
            username="conv_menu", email="conv_menu@test.com",
            password="senha-teste-123", role=self.role_convidado,
        )
        request.user = user
        item = ExpurgarInativosMenuItem()
        self.assertFalse(item.is_shown(request))

    def test_menu_item_url(self):
        item = ExpurgarInativosMenuItem()
        self.assertEqual(item.get_url(), "/admin/usuarios/expurgar-inativos/")
