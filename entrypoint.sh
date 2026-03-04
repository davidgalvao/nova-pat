#!/usr/bin/env sh
set -e

# Aguarda o DB ficar disponível (opcional simples)
# Você pode ajustar/expandir essa espera conforme necessário.
if [ -n "${DATABASE_URL:-}" ]; then
  echo "Database URL detectada."
fi

# Executa migrações se RUN_MIGRATIONS=1
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Executando migrations..."
  python manage.py migrate --noinput
fi

# Coleta estáticos se COLLECTSTATIC=1
if [ "${COLLECTSTATIC:-0}" = "1" ]; then
  echo "Coletando arquivos estáticos..."
  python manage.py collectstatic --noinput --clear
fi

# Executa o comando passado para o container (ex: runserver)
exec "$@"