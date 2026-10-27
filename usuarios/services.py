"""
Serviço de retenção de usuário inativo (card NOVAPAT-62).

Implementa a política de expurgo definida em `docs/lgpd-mapeamento-dados.md`:

- **Convidado não verificado que nunca acessou**: expurgo após 3 meses da
  criação (não há relação de uso real estabelecida).
- **Usuário ativo que ficou inativo**: expurgo após 18 meses sem acesso (já
  estabeleceu relação de uso ao fazer pelo menos um login).

O expurgo é feito por soft delete (`User.soft_delete`), mantendo o registro
para auditoria/LGPD sem deixá-lo ativo no sistema — consistente com o padrão
já usado para exclusão de conta em `usuarios/models.py`.
"""

import logging
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from usuarios.constants import (
    PAPEIS_PRESERVADOS_EXPURGAR,
    PRAZO_EXPURGAR_ATIVO_INATIVO_DIAS,
    PRAZO_EXPURGAR_CONVIDADO_NAO_VERIFICADO_DIAS,
)
from usuarios.models import User

logger = logging.getLogger(__name__)


def usuarios_elegiveis_para_expurgar():
    """
    Retorna os usuários ativos elegíveis ao expurgo pela política de retenção.

    Regras:
      * ``convidados_nao_verificados``: papel ``convidado``, e-mail não
        verificado, nunca fez login (``last_login`` nulo) e criado há mais de
        3 meses (sem relação de uso real estabelecida).
      * ``ativos_inativos``: já fez login ao menos uma vez e o último login
        é mais antigo que 18 meses.

    Medida de segurança: usuários dos papéis em
    ``PAPEIS_PRESERVADOS_EXPURGAR`` e superusers do Django nunca são
    expurgos automaticamente, evitando trancar o acesso ao sistema.

    Returns:
        Dicionário com QuerySets nas chaves
        ``convidados_nao_verificados`` e ``ativos_inativos``.
    """
    agora = timezone.now()
    corte_convidado = agora - timedelta(days=PRAZO_EXPURGAR_CONVIDADO_NAO_VERIFICADO_DIAS)
    corte_ativo_inativo = agora - timedelta(days=PRAZO_EXPURGAR_ATIVO_INATIVO_DIAS)

    convidados_nao_verificados = (
        User.objects.filter(
            role__slug="convidado",
            verified=False,
            last_login__isnull=True,
            date_joined__lte=corte_convidado,
            is_active=True,
        )
        .exclude(role__slug__in=PAPEIS_PRESERVADOS_EXPURGAR)
        .exclude(is_superuser=True)
    )

    ativos_inativos = (
        User.objects.filter(
            last_login__isnull=False,
            last_login__lte=corte_ativo_inativo,
            is_active=True,
        )
        .exclude(role__slug__in=PAPEIS_PRESERVADOS_EXPURGAR)
        .exclude(is_superuser=True)
    )

    return {
        "convidados_nao_verificados": convidados_nao_verificados,
        "ativos_inativos": ativos_inativos,
    }


def _resumo_usuario(user: User) -> dict:
    """Dados reduzidos de um usuário para relatório de expurgo."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.slug if user.role else None,
        "verified": user.verified,
        "last_login": user.last_login,
        "date_joined": user.date_joined,
    }


@transaction.atomic
def expurgar_usuarios_inativos(
    dry_run: bool = True, executado_por: Optional[User] = None
) -> dict:
    """
    Executa (ou prevê) a política de retenção de usuário inativo.

    Args:
        dry_run: quando True (default) apenas apura os candidatos sem modificar
            o banco. Quando False, realiza o soft delete de cada elegível.
        executado_por: usuário que solicitou o expurgo (registrado em
            ``deleted_by``; pode ser None quando executado por comando agendado).

    Returns:
        Dicionário com estatísticas e listas de usuários candidatos/expurgados.
    """
    elegiveis = usuarios_elegiveis_para_expurgar()
    convidados = list(
        elegiveis["convidados_nao_verificados"].order_by("date_joined")
    )
    ativos = list(elegiveis["ativos_inativos"].order_by("last_login"))
    candidatos = convidados + ativos

    expurgados = []
    if not dry_run:
        for usuario in candidatos:
            usuario.soft_delete(deleted_by=executado_por)
            expurgados.append(_resumo_usuario(usuario))
            logger.info(
                "Usuário expurgado por retenção de inatividade: "
                "id=%s username=%s role=%s",
                usuario.id,
                usuario.username,
                usuario.role.slug if usuario.role else None,
            )

    return {
        "dry_run": dry_run,
        "total_candidatos": len(candidatos),
        "convidados_nao_verificados": len(convidados),
        "ativos_inativos": len(ativos),
        "total_expurgados": len(expurgados),
        "candidatos": [_resumo_usuario(u) for u in candidatos],
        "expurgados": expurgados,
    }
