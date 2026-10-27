"""
Management command para executar a política de retenção de usuário inativo.

Por padrão roda em modo de pré-visualização (dry-run): apenas lista os
usuários que seriam expurgados, sem modificar o banco. Use --execute para
realizar o expurgo de fato (soft delete).

Uso:
    python manage.py expurgar_usuarios_inativos              # apenas prevê
    python manage.py expurgar_usuarios_inativos --execute    # expurga de fato
"""

import logging

from django.core.management.base import BaseCommand

from usuarios.services import expurgar_usuarios_inativos

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Executa a política de retenção de usuário inativo (NOVAPAT-62)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Realiza o expurgo de fato. Sem esta opção, apenas prevê (dry-run).",
        )

    def handle(self, *args, **options):
        executar = options["execute"]
        resultado = expurgar_usuarios_inativos(dry_run=not executar)

        modo = "EXECUÇÃO" if executar else "PRÉ-VISUALIZAÇÃO (dry-run)"
        self.stdout.write(self.style.NOTICE(f"Retenção de usuário inativo — {modo}"))
        self.stdout.write(f"Total de candidatos: {resultado['total_candidatos']}")
        self.stdout.write(
            f"  - Convidados não verificados: {resultado['convidados_nao_verificados']}"
        )
        self.stdout.write(f"  - Ativos inativos: {resultado['ativos_inativos']}")

        if executar:
            self.stdout.write(
                self.style.WARNING(f"Usuários expurgados: {resultado['total_expurgados']}")
            )
        else:
            self.stdout.write("Use --execute para realizar o expurgo de fato.")

        for usuario in resultado["candidatos"]:
            self.stdout.write(
                f"  - id={usuario['id']} username={usuario['username']} "
                f"email={usuario['email']} role={usuario['role']} "
                f"last_login={usuario['last_login']} date_joined={usuario['date_joined']}"
            )
