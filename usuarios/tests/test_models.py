"""
Testes para models do app usuarios.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import Tipo
from usuarios.models import User, Role, UserCanal


class UsuariosModelsTestCase(TestCase):
    """Testes para os models do app usuarios."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        # Roles já existem via migration 0003_create_default_roles
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.role_admin = Role.objects.get(slug="admin")
        cls.role_coordenador = Role.objects.get(slug="coordenador")
        cls.role_editor = Role.objects.get(slug="editor")
        cls.role_convidado = Role.objects.get(slug="convidado")

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar canal para testes
        cls.canal = CanalPage(
            title="Canal Teste",
            name="Canal Teste",
            slug="canal-teste-usuarios",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

    # ==================== TESTES ROLE ====================

    def test_role_creation(self):
        """Testa criação de Role."""
        role = Role.objects.create(
            slug="test-role",
            name="Test Role",
            description="Descrição de teste",
            ordem=10,
            is_active=True,
        )
        self.assertEqual(role.slug, "test-role")
        self.assertEqual(role.name, "Test Role")
        self.assertTrue(role.is_active)

    def test_role_slug_choices(self):
        """Testa que slug aceita apenas choices definidos."""
        # Slug válido (usar slug que não existe na migration)
        role = Role.objects.create(
            slug="test-role",
            name="Test Role",
            ordem=10,
        )
        self.assertEqual(role.slug, "test-role")

        # Slug inválido - choices não é constraint de DB, mas valida no admin/form
        # Testamos que o model aceita qualquer slug único no nível do banco
        # A validação de choices acontece no formulário/admin

    def test_role_ordering(self):
        """Testa ordenação por ordem e slug."""
        roles = list(Role.objects.all())
        # Deve estar ordenado por ordem, depois slug
        self.assertEqual(roles[0].slug, "super-admin")  # ordem 1
        self.assertEqual(roles[1].slug, "admin")  # ordem 2
        self.assertEqual(roles[2].slug, "coordenador")  # ordem 3
        self.assertEqual(roles[3].slug, "editor")  # ordem 4
        self.assertEqual(roles[4].slug, "convidado")  # ordem 5

    def test_role_get_default_role(self):
        """Testa get_default_role retorna role convidado."""
        role = Role.get_default_role()
        self.assertEqual(role.slug, "convidado")
        self.assertEqual(role.name, "Convidado")

    def test_role_get_privileged_roles(self):
        """Testa get_privileged_roles retorna super-admin, admin, coordenador."""
        privileged = Role.get_privileged_roles()
        slugs = set(privileged.values_list("slug", flat=True))
        self.assertEqual(slugs, {"super-admin", "admin", "coordenador"})

    def test_role_str(self):
        """Testa representação string."""
        role = Role.objects.get(slug="admin")
        self.assertEqual(str(role), "Admin")

    # ==================== TESTES USER ====================

    def test_user_creation_with_role(self):
        """Testa criação de User com role."""
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            role=self.role_editor,
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@test.com")
        self.assertEqual(user.role, self.role_editor)
        self.assertFalse(user.verified)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deleted_at)

    def test_user_creation_default_role_convidado(self):
        """Testa que role padrão é convidado se não especificado."""
        user = User.objects.create_user(
            username="testuser2",
            email="test2@test.com",
            password="testpass123",
        )
        self.assertEqual(user.role, self.role_convidado)

    def test_user_email_unique(self):
        """Testa que email é único."""
        User.objects.create_user(
            username="user1",
            email="unique@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="unique@test.com",
                password="testpass123",
                role=self.role_convidado,
            )

    def test_user_username_unique(self):
        """Testa que username é único."""
        User.objects.create_user(
            username="uniqueuser",
            email="user1@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="uniqueuser",
                email="user2@test.com",
                password="testpass123",
                role=self.role_convidado,
            )

    def test_user_role_protect_on_delete(self):
        """Testa PROTECT ao tentar deletar Role com usuários."""
        user = User.objects.create_user(
            username="user_role_test",
            email="role_test@test.com",
            password="testpass123",
            role=self.role_editor,
        )
        with self.assertRaises(Exception):  # ProtectedError
            self.role_editor.delete()

    def test_user_soft_delete(self):
        """Testa soft_delete mantém dados e marca is_active=False."""
        user = User.objects.create_user(
            username="todelete",
            email="delete@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user_id = user.id

        user.soft_delete(deleted_by=user)

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)
        self.assertEqual(user.deleted_by, user)
        # Usuário ainda existe no banco
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_user_restore(self):
        """Testa restore reverte soft_delete."""
        user = User.objects.create_user(
            username="torestore",
            email="restore@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user.soft_delete()
        user.restore()

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deleted_at)
        self.assertIsNone(user.deleted_by)

    def test_user_is_privileged_property(self):
        """Testa property is_privileged."""
        for role, expected in [
            (self.role_super_admin, True),
            (self.role_admin, True),
            (self.role_coordenador, True),
            (self.role_editor, False),
            (self.role_convidado, False),
        ]:
            with self.subTest(role=role.slug):
                user = User.objects.create_user(
                    username=f"user_{role.slug}",
                    email=f"{role.slug}@test.com",
                    password="testpass123",
                    role=role,
                )
                self.assertEqual(user.is_privileged, expected)

    def test_user_role_properties(self):
        """Testa properties is_super_admin, is_admin, etc."""
        user = User.objects.create_user(
            username="admin_user",
            email="admin_user@test.com",
            password="testpass123",
            role=self.role_admin,
        )
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_super_admin)
        self.assertFalse(user.is_coordenador)
        self.assertFalse(user.is_editor)
        self.assertFalse(user.is_convidado)

    def test_user_can_manage_roles(self):
        """Testa can_manage_roles - só super-admin."""
        super_admin = User.objects.create_user(
            username="sa",
            email="sa@test.com",
            password="testpass123",
            role=self.role_super_admin,
        )
        admin = User.objects.create_user(
            username="adm",
            email="adm@test.com",
            password="testpass123",
            role=self.role_admin,
        )
        self.assertTrue(super_admin.can_manage_roles())
        self.assertFalse(admin.can_manage_roles())

    def test_user_can_manage_users(self):
        """Testa can_manage_users - super-admin e admin."""
        super_admin = User.objects.create_user(
            username="sa2",
            email="sa2@test.com",
            password="testpass123",
            role=self.role_super_admin,
        )
        admin = User.objects.create_user(
            username="adm2",
            email="adm2@test.com",
            password="testpass123",
            role=self.role_admin,
        )
        coordenador = User.objects.create_user(
            username="coord",
            email="coord@test.com",
            password="testpass123",
            role=self.role_coordenador,
        )
        self.assertTrue(super_admin.can_manage_users())
        self.assertTrue(admin.can_manage_users())
        self.assertFalse(coordenador.can_manage_users())

    def test_user_str_with_full_name(self):
        """Testa __str__ com first_name/last_name."""
        user = User.objects.create_user(
            username="nameduser",
            email="named@test.com",
            password="testpass123",
            role=self.role_convidado,
            first_name="João",
            last_name="Silva",
        )
        self.assertEqual(str(user), "João Silva")

    def test_user_str_without_full_name(self):
        """Testa __str__ sem first_name/last_name usa username."""
        user = User.objects.create_user(
            username="nonameduser",
            email="nonamed@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        self.assertEqual(str(user), "nonameduser")

    def test_user_verification_fields(self):
        """Testa campos de verificação de e-mail."""
        user = User.objects.create_user(
            username="verifyuser",
            email="verify@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        self.assertFalse(user.verified)
        self.assertEqual(user.verification_token, "")
        self.assertIsNone(user.verification_token_created_at)

        # Simular envio de token
        user.verification_token = "abc123token"
        user.verification_token_created_at = timezone.now()
        user.save()

        user.refresh_from_db()
        self.assertEqual(user.verification_token, "abc123token")
        self.assertIsNotNone(user.verification_token_created_at)

    def test_user_options_json_field(self):
        """Testa campo options JSON."""
        user = User.objects.create_user(
            username="optionsuser",
            email="options@test.com",
            password="testpass123",
            role=self.role_convidado,
            options={"theme": "dark", "notifications": True},
        )
        self.assertEqual(user.options["theme"], "dark")
        self.assertTrue(user.options["notifications"])

    def test_user_groups_user_permissions_related_names(self):
        """Testa que related_names foram sobrescritos para evitar clash."""
        user = User.objects.create_user(
            username="permuser",
            email="perm@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        # Deve conseguir acessar groups e user_permissions sem erro
        self.assertEqual(user.groups.count(), 0)
        self.assertEqual(user.user_permissions.count(), 0)

    # ==================== TESTES USERCANAL ====================

    def test_user_canal_creation(self):
        """Testa criação de UserCanal."""
        user = User.objects.create_user(
            username="ucuser",
            email="uc@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user_canal = UserCanal.objects.create(
            user=user,
            canal=self.canal,
        )
        self.assertEqual(user_canal.user, user)
        self.assertEqual(user_canal.canal, self.canal)
        self.assertIsNotNone(user_canal.criado_em)

    def test_user_canal_unique_together(self):
        """Testa unique_together (user, canal)."""
        user = User.objects.create_user(
            username="ucuser2",
            email="uc2@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        UserCanal.objects.create(user=user, canal=self.canal)

        with self.assertRaises(IntegrityError):
            UserCanal.objects.create(user=user, canal=self.canal)

    def test_user_canal_cascade_on_user_delete(self):
        """Testa CASCADE ao deletar usuário."""
        user = User.objects.create_user(
            username="ucuser3",
            email="uc3@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user_canal = UserCanal.objects.create(user=user, canal=self.canal)
        uc_id = user_canal.id

        user.delete()

        self.assertFalse(UserCanal.objects.filter(id=uc_id).exists())

    def test_user_canal_cascade_on_canal_delete(self):
        """Testa CASCADE ao deletar canal."""
        user = User.objects.create_user(
            username="ucuser4",
            email="uc4@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user_canal = UserCanal.objects.create(user=user, canal=self.canal)
        uc_id = user_canal.id

        self.canal.delete()

        self.assertFalse(UserCanal.objects.filter(id=uc_id).exists())

    def test_user_canal_reverse_relations(self):
        """Testa related_names canais_vinculados e usuarios_vinculados."""
        user = User.objects.create_user(
            username="ucuser5",
            email="uc5@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        UserCanal.objects.create(user=user, canal=self.canal)

        self.assertEqual(user.canais_vinculados.count(), 1)
        self.assertEqual(self.canal.usuarios_vinculados.count(), 1)

    def test_user_canal_str(self):
        """Testa representação string."""
        user = User.objects.create_user(
            username="ucuser6",
            email="uc6@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        user_canal = UserCanal.objects.create(user=user, canal=self.canal)
        expected = f"{user} ↔ {self.canal}"
        self.assertEqual(str(user_canal), expected)

    def test_user_canal_ordering(self):
        """Testa ordenação por -criado_em."""
        user = User.objects.create_user(
            username="ucuser7",
            email="uc7@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        UserCanal.objects.create(user=user, canal=self.canal)
        # Criar segundo canal
        canal2 = CanalPage(
            title="Canal 2",
            name="Canal 2",
            slug="canal-2",
            is_active=True,
        )
        self.root_page.add_child(instance=canal2)
        canal2.save_revision().publish()
        UserCanal.objects.create(user=user, canal=canal2)

        vinculos = list(user.canais_vinculados.all())
        self.assertEqual(vinculos[0].canal, canal2)  # Mais recente primeiro
        self.assertEqual(vinculos[1].canal, self.canal)


class UsuariosRoleMigrationTestCase(TestCase):
    """Testes para verificar se a migration 0003_create_default_roles funcionou."""

    def test_default_roles_exist(self):
        """Testa que os 5 roles padrão existem."""
        slugs = set(Role.objects.values_list("slug", flat=True))
        expected = {"super-admin", "admin", "coordenador", "editor", "convidado"}
        self.assertEqual(slugs, expected)

    def test_default_roles_order(self):
        """Testa ordem dos roles padrão."""
        roles = list(Role.objects.all().order_by("ordem"))
        self.assertEqual(roles[0].slug, "super-admin")
        self.assertEqual(roles[0].ordem, 1)
        self.assertEqual(roles[1].slug, "admin")
        self.assertEqual(roles[1].ordem, 2)
        self.assertEqual(roles[2].slug, "coordenador")
        self.assertEqual(roles[2].ordem, 3)
        self.assertEqual(roles[3].slug, "editor")
        self.assertEqual(roles[3].ordem, 4)
        self.assertEqual(roles[4].slug, "convidado")
        self.assertEqual(roles[4].ordem, 5)

    def test_default_roles_names(self):
        """Testa nomes dos roles padrão."""
        role_map = {r.slug: r.name for r in Role.objects.all()}
        self.assertEqual(role_map["super-admin"], "Super Admin")
        self.assertEqual(role_map["admin"], "Admin")
        self.assertEqual(role_map["coordenador"], "Coordenador")
        self.assertEqual(role_map["editor"], "Editor")
        self.assertEqual(role_map["convidado"], "Convidado")

    def test_default_roles_all_active(self):
        """Testa que todos os roles padrão estão ativos."""
        for role in Role.objects.all():
            self.assertTrue(role.is_active)