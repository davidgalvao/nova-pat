---
name: youtrack-sync
description: Use esta skill sempre que precisar interagir com o board do YouTrack (ler cards, mover estágios, comentar).
---

# Skill: youtrack-sync

Interação com o board do YouTrack via CLI `youtrack.py`.

## Ferramenta e credenciais

- Caminho: `/home/dgalvao/youtrack-tools/youtrack.py`
- Credenciais já configuradas no `.env` — nunca pedir ao usuário.
- Projeto: **NOVAPAT** | Board: **171-8**
- Estágios: Backlog / Develop / Review / Test / Staging / Done

## Regra de workdir

Sempre use o workdir `/home/dgalvao/youtrack-tools`:

```bash
docker exec -w /home/dgalvao/youtrack-tools dsh python youtrack.py <cmd>
```

## Comandos exatos do CLI

- **Listar cards:** `docker exec -w /home/dgalvao/youtrack-tools dsh python youtrack.py list`
- **Mostrar um card:** `docker exec -w /home/dgalvao/youtrack-tools dsh python youtrack.py show <id>`
- **Mover estágio:** `docker exec -w /home/dgalvao/youtrack-tools dsh python youtrack.py move <id> <estagio>`
- **Comentar:** `docker exec -w /home/dgalvao/youtrack-tools dsh python youtrack.py comment <id> "<comentario>"`
- **Criar:** `create` não aceita stage/priority — sempre create + move.
- **Deletar:** `delete` é irreversível, sem confirmação — sempre mostrar ID + título antes.

## Regra de estágios (inviolável)

Nunca mover um card para **Done** sem autorização do usuário. Use **Review** como destino padrão para cards prontos para revisão.
