"""
Signals para o app interacoes.
Registrado automaticamente via InteracoesConfig.ready().
"""

# O signal já está definido em models.py com @receiver
# Este arquivo existe para garantir que o módulo seja importado
# e os signals registrados quando o app carrega.

# Importa os models para garantir que os signals sejam conectados
from interacoes.models import (  # noqa: F401
    AvaliacaoConteudo,
    atualizar_media_avaliacao,
)