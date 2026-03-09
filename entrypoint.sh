#!/usr/bin/env sh
set -e

# Aguarda o DB ficar disponível (mensagem informativa)
if [ -n "${DATABASE_URL:-}" ]; then
  echo "Database URL detectada."
fi

# Executa migrações se RUN_MIGRATIONS=1 — tenta várias vezes até o DB aceitar conexões
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Executando migrations..."

  MAX_RETRIES=${MIGRATE_MAX_RETRIES:-30}
  SLEEP_SECONDS=${MIGRATE_SLEEP_SECONDS:-1}
  n=0

  until python manage.py migrate --noinput; do
    n=$((n+1))
    if [ "$n" -ge "$MAX_RETRIES" ]; then
      echo "Erro: migrations falharam após $n tentativas. Saindo."
      exit 1
    fi
    echo "Aguardando DB... tentativa $n/$MAX_RETRIES. Re-tentando em ${SLEEP_SECONDS}s."
    sleep $SLEEP_SECONDS
  done
fi

# Coleta estáticos se COLLECTSTATIC=1
if [ "${COLLECTSTATIC:-0}" = "1" ]; then
  echo "Coletando arquivos estáticos..."
  python manage.py collectstatic --noinput --clear
fi

# Executa o comando passado para o container (ex: runserver)
exec "$@"