"""
Testes para models do app interacoes.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Avg, Count
from unittest.mock import patch, MagicMock

from wagtail.models import Site

from canais.models import CanalPage
from conteudos.models import ConteudoPage, Tipo
from aplicativos.models import AplicativoCategory, AplicativoEducacionalPage
from usuarios.models import User, Role
from interacoes.models import Comentario, Like, FavoritoConteudo, AvaliacaoConteudo


class InteracoesModelsTestCase(TestCase):
    """Testes para os models do app interacoes."""

    @classmethod
    def setUpTestData(cls):
        """Configuração inicial para todos os testes."""
        # Roles já existem via migration 0003_create_default_roles
        cls.role_super_admin = Role.objects.get(slug="super-admin")
        cls.role_admin = Role.objects.get(slug="admin")
        cls.role_coordenador = Role.objects.get(slug="coordenador")
        cls.role_editor = Role.objects.get(slug="editor")
        cls.role_convidado = Role.objects.get(slug="convidado")

        cls.super_admin = User.objects.create_user(
            username="superadmin",
            email="superadmin@test.com",
            password="testpass123",
            role=cls.role_super_admin,
        )
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role=cls.role_admin,
        )
        cls.coordenador = User.objects.create_user(
            username="coordenador",
            email="coordenador@test.com",
            password="testpass123",
            role=cls.role_coordenador,
        )
        cls.editor = User.objects.create_user(
            username="editor",
            email="editor@test.com",
            password="testpass123",
            role=cls.role_editor,
        )
        cls.convidado = User.objects.create_user(
            username="convidado",
            email="convidado@test.com",
            password="testpass123",
            role=cls.role_convidado,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        # Criar canal para conteúdos
        cls.canal = CanalPage(
            title="Canal Teste",
            name="Canal Teste",
            slug="canal-teste",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        # Criar tipo de conteúdo
        cls.tipo = Tipo.objects.create(
            name="Vídeo",
            slug="video",
            options={"formatos": ["mp4", "webm"]},
            is_active=True,
            ordem=1,
        )

        # Criar categoria para o canal
        from conteudos.models import CategoriaConteudo
        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Teste",
            slug="categoria-teste",
            canal=cls.canal,
            ordem=1,
            is_active=True,
        )

        # Criar ConteudoPage
        cls.conteudo = ConteudoPage(
            title="Conteúdo Teste",
            tipo=cls.tipo,
            category=cls.categoria,
            arquivo="conteudos/teste.mp4",
            autor=cls.editor,
            canal=cls.canal,
        )
        cls.canal.add_child(instance=cls.conteudo)
        cls.conteudo.save_revision().publish()

        # Criar canal fixo para aplicativos (slug='aplicativos-educacionais')
        # O save() do AplicativoEducacionalPage busca por pk=9 OU slug='aplicativos-educacionais'
        cls.canal_apps = CanalPage(
            title="Aplicativos Educacionais",
            name="Aplicativos Educacionais",
            slug="aplicativos-educacionais",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal_apps)
        cls.canal_apps.save_revision().publish()

        # Criar categoria de aplicativo
        cls.categoria_app = AplicativoCategory.objects.create(
            name="Ferramentas",
            slug="ferramentas",
            ordem=1,
            is_active=True,
        )

        # Criar AplicativoEducacionalPage
        with patch('requests.head') as mock_head, patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "192.168.1.1"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            cls.aplicativo = AplicativoEducacionalPage(
                title="App Teste",
                category=cls.categoria_app,
                url="https://app.exemplo.com",
                description="A" * 140,
                autor=cls.editor,
            )
            cls.canal_apps.add_child(instance=cls.aplicativo)
            cls.aplicativo.tags.add("tag1", "tag2", "tag3")
            cls.aplicativo.save_revision().publish()

    # ==================== TESTES COMENTARIO ====================

    def test_comentario_creation_conteudo(self):
        """Testa criação de Comentario em ConteudoPage."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
            body="Ótimo conteúdo!",
        )

        self.assertEqual(comentario.user, self.convidado)
        self.assertEqual(comentario.conteudo, self.conteudo)
        self.assertIsNone(comentario.aplicativo)
        self.assertEqual(comentario.body, "Ótimo conteúdo!")
        self.assertFalse(comentario.is_approved)  # Convidado não é privilegiado

    def test_comentario_creation_aplicativo(self):
        """Testa criação de Comentario em AplicativoEducacionalPage."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            aplicativo=self.aplicativo,
            body="App muito útil!",
        )

        self.assertEqual(comentario.aplicativo, self.aplicativo)
        self.assertIsNone(comentario.conteudo)
        self.assertFalse(comentario.is_approved)

    def test_comentario_auto_approve_privileged_roles(self):
        """Testa auto-aprovação para roles privilegiados (super-admin, admin, coordenador)."""
        for user in [self.super_admin, self.admin, self.coordenador]:
            with self.subTest(user=user.username):
                comentario = Comentario.objects.create(
                    user=user,
                    conteudo=self.conteudo,
                    body="Comentário aprovado",
                )
                self.assertTrue(comentario.is_approved)

    def test_comentario_no_auto_approve_editor_convidado(self):
        """Testa que editor e convidado NÃO têm auto-aprovação."""
        for user in [self.editor, self.convidado]:
            with self.subTest(user=user.username):
                comentario = Comentario.objects.create(
                    user=user,
                    conteudo=self.conteudo,
                    body="Comentário pendente",
                )
                self.assertFalse(comentario.is_approved)

    def test_comentario_clean_requires_exactly_one_target(self):
        """Testa validação: exatamente um target (conteudo OU aplicativo)."""
        # Nenhum target
        comentario = Comentario(
            user=self.convidado,
            body="Sem target",
        )
        with self.assertRaises(ValidationError) as cm:
            comentario.clean()
        self.assertIn("exatamente um", str(cm.exception))

        # Ambos targets
        comentario = Comentario(
            user=self.convidado,
            conteudo=self.conteudo,
            aplicativo=self.aplicativo,
            body="Dois targets",
        )
        with self.assertRaises(ValidationError) as cm:
            comentario.clean()
        self.assertIn("exatamente um", str(cm.exception))

    def test_comentario_anonymize_on_user_delete(self):
        """Testa anonimização (SET_NULL) ao excluir usuário."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
            body="Será anonimizado",
        )
        comentario_id = comentario.id

        # Deletar usuário
        self.convidado.delete()

        # Comentário deve existir mas user=None
        comentario.refresh_from_db()
        self.assertIsNone(comentario.user)
        self.assertEqual(comentario.body, "Será anonimizado")

    def test_comentario_cascade_on_conteudo_delete(self):
        """Testa CASCADE ao deletar ConteudoPage."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
            body="Será deletado",
        )
        comentario_id = comentario.id

        # Deletar conteúdo
        self.conteudo.delete()

        # Comentário deve ser deletado
        self.assertFalse(Comentario.objects.filter(id=comentario_id).exists())

    def test_comentario_cascade_on_aplicativo_delete(self):
        """Testa CASCADE ao deletar AplicativoEducacionalPage."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            aplicativo=self.aplicativo,
            body="Será deletado",
        )
        comentario_id = comentario.id

        # Deletar aplicativo
        self.aplicativo.delete()

        # Comentário deve ser deletado
        self.assertFalse(Comentario.objects.filter(id=comentario_id).exists())

    def test_comentario_ordering(self):
        """Testa ordenação por -criado_em."""
        Comentario.objects.create(user=self.convidado, conteudo=self.conteudo, body="Primeiro")
        Comentario.objects.create(user=self.convidado, conteudo=self.conteudo, body="Segundo")
        Comentario.objects.create(user=self.convidado, conteudo=self.conteudo, body="Terceiro")

        comentarios = list(Comentario.objects.filter(conteudo=self.conteudo))
        self.assertEqual(comentarios[0].body, "Terceiro")
        self.assertEqual(comentarios[1].body, "Segundo")
        self.assertEqual(comentarios[2].body, "Primeiro")

    def test_comentario_str(self):
        """Testa representação string."""
        comentario = Comentario.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
            body="Teste",
        )
        # O model usa get_full_name() que retorna string vazia se não preenchido
        # O fallback para username só acontece se user for None
        expected = f"Comentário de  em {self.conteudo}"
        self.assertEqual(str(comentario), expected)

    # ==================== TESTES LIKE ====================

    def test_like_creation_conteudo(self):
        """Testa criação de Like em ConteudoPage."""
        like = Like.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
        )

        self.assertEqual(like.user, self.convidado)
        self.assertEqual(like.conteudo, self.conteudo)
        self.assertIsNone(like.aplicativo)

    def test_like_creation_aplicativo(self):
        """Testa criação de Like em AplicativoEducacionalPage."""
        like = Like.objects.create(
            user=self.convidado,
            aplicativo=self.aplicativo,
        )

        self.assertEqual(like.aplicativo, self.aplicativo)
        self.assertIsNone(like.conteudo)

    def test_like_unique_together_conteudo(self):
        """Testa unique_together (user, conteudo)."""
        Like.objects.create(user=self.convidado, conteudo=self.conteudo)

        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.convidado, conteudo=self.conteudo)

    def test_like_unique_together_aplicativo(self):
        """Testa unique_together (user, aplicativo)."""
        Like.objects.create(user=self.convidado, aplicativo=self.aplicativo)

        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.convidado, aplicativo=self.aplicativo)

    def test_like_clean_requires_exactly_one_target(self):
        """Testa validação: exatamente um target."""
        # Nenhum target
        like = Like(user=self.convidado)
        with self.assertRaises(ValidationError) as cm:
            like.clean()
        self.assertIn("exatamente um", str(cm.exception))

        # Ambos targets
        like = Like(user=self.convidado, conteudo=self.conteudo, aplicativo=self.aplicativo)
        with self.assertRaises(ValidationError) as cm:
            like.clean()
        self.assertIn("exatamente um", str(cm.exception))

    def test_like_cascade_on_user_delete(self):
        """Testa CASCADE ao deletar usuário."""
        like = Like.objects.create(user=self.convidado, conteudo=self.conteudo)
        like_id = like.id

        self.convidado.delete()

        self.assertFalse(Like.objects.filter(id=like_id).exists())

    def test_like_cascade_on_conteudo_delete(self):
        """Testa CASCADE ao deletar ConteudoPage."""
        like = Like.objects.create(user=self.convidado, conteudo=self.conteudo)
        like_id = like.id

        self.conteudo.delete()

        self.assertFalse(Like.objects.filter(id=like_id).exists())

    def test_like_str(self):
        """Testa representação string."""
        like = Like.objects.create(user=self.convidado, conteudo=self.conteudo)
        expected = f"Like de {self.convidado} em {self.conteudo}"
        self.assertEqual(str(like), expected)

    # ==================== TESTES FAVORITOCONTEUDO ====================

    def test_favorito_creation(self):
        """Testa criação de FavoritoConteudo."""
        favorito = FavoritoConteudo.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
        )

        self.assertEqual(favorito.user, self.convidado)
        self.assertEqual(favorito.conteudo, self.conteudo)

    def test_favorito_unique_together(self):
        """Testa unique_together (user, conteudo)."""
        FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)

        with self.assertRaises(IntegrityError):
            FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)

    def test_favorito_only_conteudo_scope(self):
        """Testa que FavoritoConteudo só aceita ConteudoPage (não Aplicativo)."""
        # O model só tem FK para ConteudoPage, não para Aplicativo
        # Isso é testado implicitamente pela estrutura do model
        favorito = FavoritoConteudo.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
        )
        self.assertIsNotNone(favorito.conteudo)
        self.assertFalse(hasattr(favorito, 'aplicativo'))

    def test_favorito_cascade_on_user_delete(self):
        """Testa CASCADE ao deletar usuário."""
        favorito = FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)
        favorito_id = favorito.id

        self.convidado.delete()

        self.assertFalse(FavoritoConteudo.objects.filter(id=favorito_id).exists())

    def test_favorito_cascade_on_conteudo_delete(self):
        """Testa CASCADE ao deletar ConteudoPage."""
        favorito = FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)
        favorito_id = favorito.id

        self.conteudo.delete()

        self.assertFalse(FavoritoConteudo.objects.filter(id=favorito_id).exists())

    def test_favorito_ordering(self):
        """Testa ordenação por -criado_em."""
        FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)
        # Criar outro conteúdo para testar
        conteudo2 = ConteudoPage(
            title="Conteúdo 2",
            tipo=self.tipo,
            category=self.categoria,
            arquivo="conteudos/teste2.mp4",
            autor=self.editor,
            canal=self.canal,
        )
        self.canal.add_child(instance=conteudo2)
        conteudo2.save_revision().publish()
        FavoritoConteudo.objects.create(user=self.convidado, conteudo=conteudo2)

        favoritos = list(FavoritoConteudo.objects.filter(user=self.convidado))
        self.assertEqual(favoritos[0].conteudo, conteudo2)
        self.assertEqual(favoritos[1].conteudo, self.conteudo)

    def test_favorito_str(self):
        """Testa representação string."""
        favorito = FavoritoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo)
        expected = f"Favorito de {self.convidado} em {self.conteudo}"
        self.assertEqual(str(favorito), expected)

    # ==================== TESTES AVALIACAOCONTEUDO ====================

    def test_avaliacao_creation(self):
        """Testa criação de AvaliacaoConteudo."""
        avaliacao = AvaliacaoConteudo.objects.create(
            user=self.convidado,
            conteudo=self.conteudo,
            nota=5,
        )

        self.assertEqual(avaliacao.user, self.convidado)
        self.assertEqual(avaliacao.conteudo, self.conteudo)
        self.assertEqual(avaliacao.nota, 5)

    def test_avaliacao_unique_together(self):
        """Testa unique_together (user, conteudo) - permite reeditar."""
        AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)

        with self.assertRaises(IntegrityError):
            AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=5)

    def test_avaliacao_clean_validates_nota_range(self):
        """Testa validação de nota entre 1 e 5."""
        # Nota 0
        avaliacao = AvaliacaoConteudo(user=self.convidado, conteudo=self.conteudo, nota=0)
        with self.assertRaises(ValidationError) as cm:
            avaliacao.clean()
        self.assertIn("nota", cm.exception.message_dict)

        # Nota 6
        avaliacao = AvaliacaoConteudo(user=self.convidado, conteudo=self.conteudo, nota=6)
        with self.assertRaises(ValidationError) as cm:
            avaliacao.clean()
        self.assertIn("nota", cm.exception.message_dict)

        # Notas válidas
        for nota in [1, 2, 3, 4, 5]:
            with self.subTest(nota=nota):
                avaliacao = AvaliacaoConteudo(user=self.convidado, conteudo=self.conteudo, nota=nota)
                avaliacao.clean()  # Não deve levantar

    def test_avaliacao_signal_updates_conteudo_on_save(self):
        """Testa signal atualiza media_avaliacao/total_avaliacoes no save."""
        # Estado inicial
        self.assertEqual(self.conteudo.media_avaliacao, 0)
        self.assertEqual(self.conteudo.total_avaliacoes, 0)

        # Adicionar avaliação
        AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)
        self.conteudo.refresh_from_db()

        self.assertEqual(self.conteudo.media_avaliacao, 4.0)
        self.assertEqual(self.conteudo.total_avaliacoes, 1)

        # Adicionar segunda avaliação (outro usuário)
        user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        AvaliacaoConteudo.objects.create(user=user2, conteudo=self.conteudo, nota=5)
        self.conteudo.refresh_from_db()

        self.assertEqual(self.conteudo.media_avaliacao, 4.5)
        self.assertEqual(self.conteudo.total_avaliacoes, 2)

    def test_avaliacao_signal_updates_conteudo_on_delete(self):
        """Testa signal atualiza media_avaliacao/total_avaliacoes no delete."""
        AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)
        user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="testpass123",
            role=self.role_convidado,
        )
        AvaliacaoConteudo.objects.create(user=user2, conteudo=self.conteudo, nota=5)
        self.conteudo.refresh_from_db()

        self.assertEqual(self.conteudo.total_avaliacoes, 2)

        # Deletar uma avaliação
        self.convidado.avaliacoes.first().delete()
        self.conteudo.refresh_from_db()

        self.assertEqual(self.conteudo.total_avaliacoes, 1)
        self.assertEqual(self.conteudo.media_avaliacao, 5.0)

    def test_avaliacao_cascade_on_user_delete(self):
        """Testa CASCADE ao deletar usuário."""
        avaliacao = AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)
        avaliacao_id = avaliacao.id

        self.convidado.delete()

        self.assertFalse(AvaliacaoConteudo.objects.filter(id=avaliacao_id).exists())

    def test_avaliacao_cascade_on_conteudo_delete(self):
        """Testa CASCADE ao deletar ConteudoPage."""
        avaliacao = AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)
        avaliacao_id = avaliacao.id

        self.conteudo.delete()

        self.assertFalse(AvaliacaoConteudo.objects.filter(id=avaliacao_id).exists())

    def test_avaliacao_str(self):
        """Testa representação string."""
        avaliacao = AvaliacaoConteudo.objects.create(user=self.convidado, conteudo=self.conteudo, nota=4)
        expected = f"Avaliação 4/5 de {self.convidado} em {self.conteudo}"
        self.assertEqual(str(avaliacao), expected)


class InteracoesSignalTestCase(TestCase):
    """Testes específicos para signals do app interacoes."""

    @classmethod
    def setUpTestData(cls):
        cls.role_convidado = Role.objects.get(slug="convidado")
        cls.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            role=cls.role_convidado,
        )

        cls.root_page = Site.objects.get(is_default_site=True).root_page

        cls.canal = CanalPage(
            title="Canal Teste",
            name="Canal Teste",
            slug="canal-teste-signal",
            is_active=True,
        )
        cls.root_page.add_child(instance=cls.canal)
        cls.canal.save_revision().publish()

        cls.tipo = Tipo.objects.create(
            name="Vídeo",
            slug="video-signal",
            options={"formatos": ["mp4"]},
            is_active=True,
            ordem=1,
        )

        from conteudos.models import CategoriaConteudo
        cls.categoria = CategoriaConteudo.objects.create(
            name="Categoria Signal",
            slug="categoria-signal",
            canal=cls.canal,
            ordem=1,
            is_active=True,
        )

        cls.conteudo = ConteudoPage(
            title="Conteúdo Signal",
            tipo=cls.tipo,
            category=cls.categoria,
            arquivo="conteudos/signal.mp4",
            autor=cls.user,
            canal=cls.canal,
        )
        cls.canal.add_child(instance=cls.conteudo)
        cls.conteudo.save_revision().publish()

    def test_signal_post_save_updates_media_avaliacao(self):
        """Testa signal post_save atualiza media_avaliacao."""
        AvaliacaoConteudo.objects.create(user=self.user, conteudo=self.conteudo, nota=3)
        self.conteudo.refresh_from_db()
        self.assertEqual(self.conteudo.media_avaliacao, 3.0)
        self.assertEqual(self.conteudo.total_avaliacoes, 1)

    def test_signal_post_delete_updates_media_avaliacao(self):
        """Testa signal post_delete atualiza media_avaliacao."""
        AvaliacaoConteudo.objects.create(user=self.user, conteudo=self.conteudo, nota=3)
        self.conteudo.refresh_from_db()

        # Criar outro usuário e avaliação
        role = Role.objects.get(slug="convidado")
        user2 = User.objects.create_user(
            username="testuser2",
            email="test2@test.com",
            password="testpass123",
            role=role,
        )
        AvaliacaoConteudo.objects.create(user=user2, conteudo=self.conteudo, nota=5)
        self.conteudo.refresh_from_db()
        self.assertEqual(self.conteudo.total_avaliacoes, 2)

        # Deletar primeira avaliação
        self.user.avaliacoes.first().delete()
        self.conteudo.refresh_from_db()
        self.assertEqual(self.conteudo.total_avaliacoes, 1)
        self.assertEqual(self.conteudo.media_avaliacao, 5.0)

    def test_signal_multiple_avaliacoes_calculates_correct_average(self):
        """Testa média correta com múltiplas avaliações."""
        role = Role.objects.get(slug="convidado")
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@test.com",
                password="testpass123",
                role=role,
            )
            users.append(user)

        notas = [1, 2, 3, 4, 5]
        for user, nota in zip(users, notas):
            AvaliacaoConteudo.objects.create(user=user, conteudo=self.conteudo, nota=nota)

        self.conteudo.refresh_from_db()
        self.assertEqual(self.conteudo.total_avaliacoes, 5)
        self.assertEqual(self.conteudo.media_avaliacao, 3.0)  # (1+2+3+4+5)/5 = 3.0