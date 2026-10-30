---
name: card-single-flow
description: Use esta skill para desenvolver um único card na main (sem worktree), do início ao commit e merge.
---

# Skill: card-single-flow

Fluxo de desenvolvimento de um único card na branch `main`. Não use worktrees para tarefa simples.

## Passo 1 — Leia o card

Leia o card no YouTrack (usando a skill `youtrack-sync` / CLI `youtrack.py`).

## Passo 2 — Crie a branch

Crie uma branch com o ID do card:

```bash
git checkout -b novapat-XX
```

Substitua `XX` pelo número do card.

## Passo 3 — Implemente e teste

Faça a implementação e rode os testes.

## Passo 4 — Mostre o diff e os testes

Exiba o `git diff` e os resultados dos testes.

## Passo 5 — Pausa para OK do usuário

PARE E AGUARDE o OK do usuário.

Se o usuário pedir correções, continue na mesma branch.

## Passo 6 — Após a aprovação

1. Faça o commit
2. Merge na main
3. Mova o card no YouTrack para **Review** (usando a skill `youtrack-sync`)
4. Delete a branch

**Regras invioláveis (Git):**
- NUNCA rode `git push`. Isso é feito exclusivamente pelo humano.
- NUNCA rode `git reset --hard`, `git clean -fd`, `git checkout .` sem OK explícito.
- NUNCA faça `git commit` ou `git merge` sem a aprovação explícita do usuário.
- Para operações destrutivas, mostre o comando primeiro e aguarde.
