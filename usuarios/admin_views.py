"""
View administrativa de retenção de usuários inativos (card NOVAPAT-62).

Integrada ao painel admin do Wagtail (usa o template base do admin),
em vez de uma página Django separada fora do ecossistema.

Exibe:
  * Usuários elegíveis ao expurgo automático (convidados não verificados
    nunca acessados > 3 meses; ativos inativos > 18 meses).
  * Usuários já expurgados (soft delete).

O expurgo em si é executado automaticamente pelo comando de gestão
``expurgar_usuarios_inativos`` (pronto para ser agendado via cron), não por
botão manual nesta tela.
"""
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from usuarios.services import usuarios_elegiveis_para_expurgar

User = get_user_model()


class SuperAdminRequiredMixin:
    """Acesso restrito a super-admin (papel ``super-admin`` do sistema).

    Retorna 403 diretamente (não levanta PermissionDenied) porque o Wagtail
    admin costuma capturar essa exceção e devolver 200 com uma página de erro.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if (
            not user.is_authenticated
            or not getattr(user, "is_super_admin", False)
        ):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class RetencaoUsuariosView(SuperAdminRequiredMixin, TemplateView):
    """
    Página de retenção de usuários inativos dentro do admin do Wagtail.

    Apenas acessível a super-admins (verificado no ``dispatch`` do mixin).
    """

    template_name = "usuarios/admin/retencao.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        elegiveis = usuarios_elegiveis_para_expurgar()
        expurgados = User.objects.filter(
            is_active=False, deleted_at__isnull=False
        ).order_by("-deleted_at")
        context.update(
            {
                "elegiveis": elegiveis,
                "expurgados": expurgados,
                "total_elegiveis": len(
                    elegiveis["convidados_nao_verificados"]
                )
                + len(elegiveis["ativos_inativos"]),
                "total_expurgados": expurgados.count(),
            }
        )
        return context
