"""
Signals para o app interacoes.

O signal `atualizar_media_avaliacao` é **definido em `interacoes/models.py`**
(decorado com `@receiver`), não aqui. Este arquivo existe como ponto de
importação garantido, para que o módulo `models.py` seja importado — e,
portanto, o `@receiver` registrado — no app startup.

Por que definir em `models.py` e importar aqui, em vez de definir o signal
diretamente neste arquivo: o decorador `@receiver` precisa do model
`AvaliacaoConteudo` já definido, e a definição colada ao model mantém a lógica
de atualização junto da entidade que dispara o evento. Este módulo de
`signals.py` é apenas o ponto de carregamento explícito, importado por
`InteracoesConfig.ready()`.
"""

# O signal já está definido em models.py com @receiver
# Este arquivo existe para garantir que o módulo seja importado
# e os signals registrados quando o app carrega.

# Importa os models para garantir que os signals sejam conectados
from interacoes.models import (  # noqa: F401
    AvaliacaoConteudo,
    atualizar_media_avaliacao,
)