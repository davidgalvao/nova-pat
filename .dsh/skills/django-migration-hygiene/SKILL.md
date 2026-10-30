---
name: django-migration-hygiene
description: Use esta skill antes de alterar models ou gerar migrações Django para garantir a integridade do banco.
---

# Skill: django-migration-hygiene

Regras de higiene de migrações Django. Aplique antes de alterar models ou gerar migrações.

## Regras

1. **Nunca editar migração já aplicada.** Se houver erro, crie uma migração nova para corrigir.
2. **Limpar órfãos com MigrationRecorder.** Verifique migrações registradas no banco (tabela `django_migrations`) antes de alterar qualquer coisa, usando `MigrationRecorder` do Django para conferir o estado aplicado.
3. **Rodar `makemigrations --check`** para garantir que não há mudanças de model sem migração correspondente.
4. **Antes de commitar:** rodar `python manage.py migrate --check` e `python manage.py makemigrations --check --dry-run`.
5. Nunca rode comandos destrutivos em loto contra o banco (ex: `docker system prune -a`, `docker volume rm`, `docker compose down` sobre db/postgres_data) sem aprovação explícita.

## Comandos de validação

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
```

Se qualquer um falhar, pare e corrija antes de prosseguir.
