from django.conf import settings
from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class Comentario(models.Model):
    """
    Comentário em conteúdo educacional ou aplicativo.
    Polimórfico entre ConteudoPage e AplicativoEducacionalPage (duas FKs nullable, fiel ao legado).
    Moderação: usuários privilegiados (super-admin, admin, coordenador) publicam direto;
    demais usuários entram como is_approved=False, pendente de moderação.
    Ao excluir conta do usuário: anonimiza (SET_NULL), não apaga — preserva texto e trilha de moderação.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuário"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comentarios",
        help_text=_("Autor do comentário. SET_NULL ao excluir conta (anonimiza)."),
    )

    conteudo = models.ForeignKey(
        "conteudos.ConteudoPage",
        verbose_name=_("conteúdo"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="comentarios",
        help_text=_("Conteúdo educacional comentado (um dos dois deve ser preenchido)."),
    )

    aplicativo = models.ForeignKey(
        "aplicativos.AplicativoEducacionalPage",
        verbose_name=_("aplicativo"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="comentarios",
        help_text=_("Aplicativo educacional comentado (um dos dois deve ser preenchido)."),
    )

    body = models.TextField(_("texto"), help_text=_("Texto do comentário."))

    is_approved = models.BooleanField(
        _("aprovado"),
        default=False,
        help_text=_("Comentários de usuários privilegiados são aprovados automaticamente."),
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("comentário")
        verbose_name_plural = _("comentários")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["conteudo", "is_approved", "-criado_em"]),
            models.Index(fields=["aplicativo", "is_approved", "-criado_em"]),
        ]

    def __str__(self) -> str:
        target = self.conteudo or self.aplicativo
        autor = self.user.get_full_name() if self.user else "Usuário removido"
        return f"Comentário de {autor} em {target}"

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        # Exatamente um dos dois deve ser preenchido
        if (self.conteudo is None) == (self.aplicativo is None):
            raise ValidationError(
                _("Preencha exatamente um: 'conteudo' OU 'aplicativo', não ambos nem nenhum.")
            )

    def save(self, *args, **kwargs):
        # Auto-aprovação baseada no role do usuário
        # Importa aqui para evitar circular import
        if self.user_id and not self.pk:  # Só na criação
            from usuarios.models import User

            try:
                user = User.objects.get(pk=self.user_id)
                # Papéis privilegiados que publicam direto (conforme RN-L1 / ConteudoPolicy)
                if user.role and user.role.slug in ("super-admin", "admin", "coordenador"):
                    self.is_approved = True
            except User.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class Like(models.Model):
    """
    Like simples (não like/dislike) em conteúdo ou aplicativo.
    Polimórfico igual a Comentario (duas FKs nullable).
    Existência do registro = curtiu. Descurtir = deletar a linha.
    unique_together garante 1 like por usuário por alvo.
    Ao excluir conta: CASCADE (apaga o like — é só sinal de engajamento).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuário"),
        on_delete=models.CASCADE,
        related_name="likes",
    )

    conteudo = models.ForeignKey(
        "conteudos.ConteudoPage",
        verbose_name=_("conteúdo"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    aplicativo = models.ForeignKey(
        "aplicativos.AplicativoEducacionalPage",
        verbose_name=_("aplicativo"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("like")
        verbose_name_plural = _("likes")
        unique_together = [
            ("user", "conteudo"),
            ("user", "aplicativo"),
        ]
        indexes = [
            models.Index(fields=["conteudo", "-criado_em"]),
            models.Index(fields=["aplicativo", "-criado_em"]),
        ]

    def __str__(self) -> str:
        target = self.conteudo or self.aplicativo
        return f"Like de {self.user} em {target}"

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if (self.conteudo is None) == (self.aplicativo is None):
            raise ValidationError(
                _("Preencha exatamente um: 'conteudo' OU 'aplicativo', não ambos nem nenhum.")
            )


class FavoritoConteudo(models.Model):
    """
    Favorito de conteúdo educacional — lista privada do usuário.
    Diferente de Like: favoritar é privado, curtir é público.
    Escopo atual: apenas ConteudoPage (decisão explícita, não estender para Aplicativo sem confirmar).
    Ao excluir conta: CASCADE (apaga o favorito).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuário"),
        on_delete=models.CASCADE,
        related_name="favoritos",
    )

    conteudo = models.ForeignKey(
        "conteudos.ConteudoPage",
        verbose_name=_("conteúdo"),
        on_delete=models.CASCADE,
        related_name="favoritos",
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("favorito")
        verbose_name_plural = _("favoritos")
        unique_together = ("user", "conteudo")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["user", "-criado_em"]),
        ]

    def __str__(self) -> str:
        return f"Favorito de {self.user} em {self.conteudo}"


class AvaliacaoConteudo(models.Model):
    """
    Avaliação 1 a 5 estrelas de conteúdo educacional.
    Para uso futuro em curadoria/ranking — NÃO é critério de busca/filtro/ordenação (decisão de produto).
    unique_together permite reeditar (1 avaliação por par user+conteudo).
    Signal atualiza media_avaliacao/total_avaliacoes em ConteudoPage (desnormalizado).
    Ao excluir conta: CASCADE (apaga a avaliação).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("usuário"),
        on_delete=models.CASCADE,
        related_name="avaliacoes",
    )

    conteudo = models.ForeignKey(
        "conteudos.ConteudoPage",
        verbose_name=_("conteúdo"),
        on_delete=models.CASCADE,
        related_name="avaliacoes",
    )

    nota = models.PositiveSmallIntegerField(
        _("nota"),
        help_text=_("Nota de 1 a 5."),
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("avaliação")
        verbose_name_plural = _("avaliações")
        unique_together = ("user", "conteudo")
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["conteudo", "-criado_em"]),
        ]

    def __str__(self) -> str:
        return f"Avaliação {self.nota}/5 de {self.user} em {self.conteudo}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.core.validators import MaxValueValidator, MinValueValidator

        super().clean()
        if self.nota < 1 or self.nota > 5:
            raise ValidationError({"nota": _("A nota deve ser entre 1 e 5.")})


# Signals para atualizar campos desnormalizados em ConteudoPage
@receiver([post_save, post_delete], sender=AvaliacaoConteudo)
def atualizar_media_avaliacao(sender, instance, **kwargs):
    """
    Atualiza media_avaliacao e total_avaliacoes em ConteudoPage
    sempre que uma AvaliacaoConteudo é salva ou deletada.
    """
    conteudo = instance.conteudo
    agregados = conteudo.avaliacoes.aggregate(media=Avg("nota"), total=Count("id"))
    conteudo.media_avaliacao = agregados["media"] or 0
    conteudo.total_avaliacoes = agregados["total"]
    conteudo.save(update_fields=["media_avaliacao", "total_avaliacoes"])