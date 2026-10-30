---
name: docker-local
description: Use esta skill para rodar comandos Docker no container web (testes, manage.py, logs, restart, ps) sabendo o que precisa ou não de aprovação.
---

# Skill: docker-local

Referência de comandos Docker permitidos e comandos que exigem aprovação explícita, para o container web do projeto Nova PAT.

## Comandos permitidos (sem aprovação)

```bash
docker compose -f /home/dgalvao/nova-pat/docker-compose.yml exec -T web pytest -x -q
docker compose ... exec -T web python manage.py <comando>
docker compose ... logs web --tail 30
docker compose ... restart web
docker compose ... ps
docker ps
docker logs <container> --tail 30
```

**A flag `-T` é obrigatória** em `exec` (sem TTY).

## Comandos que exigem aprovação explícita

```bash
docker compose down
docker compose stop
docker system prune
docker volume rm
docker rmi
# Qualquer coisa que toque em db ou postgres_data
docker rm
docker kill
```

**Nunca** rode comandos destrutivos em lote (`rm -rf`, `docker system prune -a`).

## Ambiente de execução (projeto)

- Toda a aplicação roda **exclusivamente** em contêineres via `docker compose`.
- **PROIBIDO** rodar `python`, `pip`, `pytest` ou `manage.py` direto no host.
- O serviço do backend/Django se chama **`web`** (NUNCA `backend`). Leia o `docker-compose.yml` antes de assumir nomes de serviços.
