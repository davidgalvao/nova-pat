---
name: worktree-review
description: Use esta skill sempre que for iniciar o desenvolvimento de um card usando git worktree, testar o código isoladamente e preparar para revisão visual humana.
---

# Skill: worktree-review

Resumo do **FLUXO 2: DESENVOLVIMENTO PARALELO (WORKTREES)** do AGENTS.md global. Use para desenvolver múltiplos cards em paralelo com isolamento de código.

## Passo 1 — Preparação

Execute na raiz do projeto (main):

```bash
mkdir -p .worktrees
grep -qxF '.worktrees/' .git/info/exclude || echo '.worktrees/' >> .git/info/exclude
git worktree add .worktrees/novapat-XX -b novapat-XX
cp .env .worktrees/novapat-XX/
```

Substitua `XX` pelo número do card.

## Passo 2 — Desenvolvimento

Os subagentes escrevem o código **DENTRO** da pasta da worktree (`.worktrees/novapat-XX/`). Nunca na main.

## Passo 3 — Testes isolados

Na worktree:

```bash
cd .worktrees/novapat-XX
docker compose -p test-novapat-XX run --rm web sh -c "python manage.py makemigrations && pytest -x -q"
```

Após o teste (passando ou falhando), sempre rode:

```bash
docker compose -p test-novapat-XX down -v
```

Para não deixar banco zumbi.

Se passar, prepare o diff:

```bash
git add -u
git add */migrations/*.py  # apenas se houver migrações novas
```

## Passo 4 — Ponto de parada e revisão

```bash
git diff --cached
```

Mova o card no YouTrack para **Review** (usando a skill youtrack-sync / CLI youtrack.py).

**PARE IMEDIATAMENTE** e aguarde o usuário.

## Passo 5 — Checkout para revisão visual (quando o usuário pedir para testar)

O usuário dirá algo como: "Quero testar o card XX que está em Review".

Rode **NA MAIN** (fora da worktree):

```bash
git checkout novapat-XX -- caminho/do/arquivo1 caminho/do/arquivo2
```

Substitua pelos arquivos que apareceram no `git diff --cached`.

Avisar ao usuário:

> Arquivos copiados para a main. Pode testar no navegador. Aguardo seu parecer.

## Passo 6 — Veredito do usuário

**Se o usuário aprovar** ("ok", "aprovado"):

1. Na worktree: `git add -A` e `git commit -m "<mensagem>"`
2. Na main: `git merge novapat-XX`
3. Mova o card no YouTrack para "Done" (ou mantenha em Review, se o usuário preferir)
4. Comente no card com o hash do commit
5. `git worktree remove .worktrees/novapat-XX --force` e `git branch -d novapat-XX`
6. Na main: `git checkout .` para limpar resquício do checkout temporário

**Se o usuário rejeitar** ("não está ok", "corrija X"):

1. Na main: `git checkout .` para descartar cópias temporárias
2. Volte à pasta da worktree e aplique as correções
3. Volte ao Passo 3 (rodar testes e mostrar novo diff)
