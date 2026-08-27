from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserCanal(models.Model):
    """
    Vínculo usuário-canal (pivot user_canal do legado).
    Chave composta (user, canal) — usuário pode estar vinculado a múltiplos canais.
    Semântica exata não confirmada no legado (pode ser escopo de curadoria por canal).
    Não presumir regra de negócio sem confirmar em produção.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuário"),
        on_delete=models.CASCADE,
        related_name="canais_vinculados",
    )

    canal = models.ForeignKey(
        "canais.CanalPage",
        verbose_name=_("canal"),
        on_delete=models.CASCADE,
        related_name="usuarios_vinculados",
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("vínculo usuário-canal")
        verbose_name_plural = _("vínculos usuário-canal")
        unique_together = ("user", "canal")
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.user} ↔ {self.canal}"


class Role(models.Model):
    """
    Papéis (roles) do sistema — 5 fixos, vindos do legado.
    Não é gerenciável por admin (só super-admin via migration/fixture).
    """

    SLUG_CHOICES = [
        ("super-admin", "Super Admin"),
        ("admin", "Admin"),
        ("coordenador", "Coordenador"),
        ("editor", "Editor"),
        ("convidado", "Convidado"),
    ]

    slug = models.SlugField(_("slug"), max_length=20, unique=True, choices=SLUG_CHOICES)
    name = models.CharField(_("nome"), max_length=50)
    description = models.TextField(_("descrição"), blank=True)
    ordem = models.PositiveIntegerField(_("ordem"), default=0, help_text=_("Ordem de hierarquia (menor = mais privilégios)."))
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("papel")
        verbose_name_plural = _("papéis")
        ordering = ["ordem", "slug"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_default_role(cls):
        """Retorna o role padrão para novos cadastros (convidado)."""
        return cls.objects.get_or_create(
            slug="convidado",
            defaults={
                "name": "Convidado",
                "description": "Papel padrão de novo cadastro (self-registration).",
                "ordem": 5,
            },
        )[0]

    @classmethod
    def get_privileged_roles(cls):
        """Retorna roles que podem criar/aprovar conteúdo (super-admin, admin, coordenador)."""
        return cls.objects.filter(slug__in=["super-admin", "admin", "coordenador"])


class User(AbstractUser):
    """
    Usuário estendido — herda de AbstractUser (username, email, password, first_name, last_name, etc.).
    Adiciona: role (FK), verified, verification_token, options (JSON).
    Soft delete: usa is_active=False (padrão Django) + deleted_at para auditoria.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Obrigatório. 150 caracteres ou menos. Letras, dígitos e @/./+/-/_ apenas."),
        validators=[username_validator],
        error_messages={
            "unique": _("Já existe um usuário com este username."),
        },
    )

    email = models.EmailField(_("e-mail"), unique=True, error_messages={"unique": _("Já existe um usuário com este e-mail.")})

    role = models.ForeignKey(
        "usuarios.Role",
        verbose_name=_("papel"),
        on_delete=models.PROTECT,
        related_name="users",
        help_text=_("Papel do usuário no sistema (define permissões)."),
    )

    verified = models.BooleanField(
        _("verificado"),
        default=False,
        help_text=_("E-mail verificado via token enviado no cadastro."),
    )

    verification_token = models.CharField(
        _("token de verificação"),
        max_length=100,
        blank=True,
        help_text=_("Token para verificação de e-mail. Expira após uso."),
    )

    verification_token_created_at = models.DateTimeField(
        _("token criado em"),
        null=True,
        blank=True,
        help_text=_("Timestamp de criação do token (para expiração)."),
    )

    options = models.JSONField(
        _("opções extras"),
        default=dict,
        blank=True,
        help_text=_("Metadados flexíveis (ex: preferências de UI, configurações de notificação)."),
    )

    # Soft delete fields
    deleted_at = models.DateTimeField(_("excluído em"), null=True, blank=True, help_text=_("Timestamp de exclusão lógica (soft delete)."))
    deleted_by = models.ForeignKey(
        "self",
        verbose_name=_("excluído por"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_users",
        help_text=_("Usuário que realizou a exclusão lógica."),
    )

    # Override groups e user_permissions para evitar clash com AbstractUser
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_("The groups this user belongs to. A user will get all permissions granted to each of their groups."),
        related_name="usuarios_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="usuarios_user_set",
        related_query_name="user",
    )

    class Meta:
        verbose_name = _("usuário")
        verbose_name_plural = _("usuários")
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    def clean(self):
        super().clean()
        # Garante role padrão se não definido
        if not self.role_id:
            self.role = Role.get_default_role()

    def save(self, *args, **kwargs):
        # Define role padrão na criação se não definido
        if not self.pk and not self.role_id:
            self.role = Role.get_default_role()
        super().save(*args, **kwargs)

    def soft_delete(self, deleted_by=None):
        """Exclusão lógica (soft delete) — mantém dados para LGPD/auditoria."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_active", "deleted_at", "deleted_by"])

    def restore(self):
        """Restaura usuário soft-deletado."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_active", "deleted_at", "deleted_by"])

    @property
    def is_privileged(self) -> bool:
        """Verifica se o usuário tem papel privilegiado (pode criar/aprovar conteúdo)."""
        return self.role and self.role.slug in ("super-admin", "admin", "coordenador")

    @property
    def is_super_admin(self) -> bool:
        """True se o usuário tem o papel `super-admin` (irrestrito)."""
        return self.role and self.role.slug == "super-admin"

    @property
    def is_admin(self) -> bool:
        """True se o usuário tem o papel `admin` (quase irrestrito)."""
        return self.role and self.role.slug == "admin"

    @property
    def is_coordenador(self) -> bool:
        """True se o usuário tem o papel `coordenador` (curadoria de conteúdo)."""
        return self.role and self.role.slug == "coordenador"

    @property
    def is_editor(self) -> bool:
        """
        True se o usuário tem o papel `editor`.

        Nota: o papel `editor` não tem permissão implementada no legado (igual a
        `convidado`). Ver decisão D2 em `docs/adr/README.md` e `usuarios/CLAUDE.md`.
        """
        return self.role and self.role.slug == "editor"

    @property
    def is_convidado(self) -> bool:
        """True se o usuário tem o papel `convidado` (padrão de cadastro público)."""
        return self.role and self.role.slug == "convidado"

    def can_manage_roles(self) -> bool:
        """Só super-admin gerencia estrutura de papéis (RolePolicy do legado)."""
        return self.is_super_admin

    def can_manage_users(self) -> bool:
        """Super-admin e admin gerenciam usuários de terceiros (UserPolicy do legado)."""
        return self.is_super_admin or self.is_admin

