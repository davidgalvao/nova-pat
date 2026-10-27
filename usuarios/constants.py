"""
Constantes de retenção de dados do app `usuarios` (card NOVAPAT-62).

Os prazos seguem `docs/lgpd-mapeamento-dados.md` e a decisão fechada com o
jurídico/cliente:

- convidado cadastrado e nunca verificado: **3 meses** (sem relação de uso
  real estabelecida, prazo mais curto é defensável);
- usuário ativo que ficou inativo: **18 meses** (valor padrão a implementar,
  sujeito à confirmação do cliente).

Os valores são expressos em dias para facilitar comparações com `timedelta`
dos campos `date_joined` e `last_login` do model `User`.
"""

from datetime import timedelta

# 3 meses (aprox. 90 dias) — conta de convidado nunca ativada.
PRAZO_EXPURGAR_CONVIDADO_NAO_VERIFICADO_DIAS = 90

# 18 meses (aprox. 540 dias) — usuário que já usou o sistema e parou de acessar.
PRAZO_EXPURGAR_ATIVO_INATIVO_DIAS = 540

# Papéis preservados de expurgo automático (medida de segurança: nunca se
# expurga o próprio administrador do sistema, para não trancar o acesso).
PAPEIS_PRESERVADOS_EXPURGAR = ("super-admin",)
