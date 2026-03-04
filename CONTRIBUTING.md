CONTRIBUTING (English)

Thank you for contributing to Nova PAT.

Please follow these guidelines before opening issues or pull requests:

- Use Conventional Commits for commit messages. Examples:
  - feat(scope): add new feature
  - fix(scope): fix a bug
  - chore(repo): update docs

- How to open a PR:
  1. Fork the repo and create a branch named `feat/short-description` or `fix/short-description`.
  2. Ensure tests pass and include a short description in the PR body.
  3. Reference related issues using `#`.

- Run the project locally (Docker Compose):

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
```

- Linting / Tests: add information here if you add linters or tests.

- Code of Conduct: please read `CODE_OF_CONDUCT.md` and follow it.

---

CONTRIBUTING (Español)

Gracias por contribuir a Nova PAT.

Siga estas pautas antes de crear issues o pull requests:

- Use Conventional Commits para los mensajes de commit. Ejemplos:
  - feat(scope): agregar nueva funcionalidad
  - fix(scope): corregir un error
  - chore(repo): actualizar documentación

- Cómo abrir un PR:
  1. Haga fork del repositorio y cree una rama llamada `feat/descripcion-corta` o `fix/descripcion-corta`.
  2. Asegúrese de que las pruebas pasen e incluya una descripción breve en el PR.
  3. Referencie issues relacionadas usando `#`.

- Ejecutar el proyecto localmente (Docker Compose):

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
```

- Linting / Tests: agregue información aquí si incorpora linters o tests.

- Código de conducta: lea `CODE_OF_CONDUCT.md` y sígalo.

---

CONTRIBUTING (Português)

Obrigado por contribuir para o Nova PAT.

Siga estas diretrizes antes de abrir issues ou pull requests:

- Use Conventional Commits para mensagens de commit. Exemplos:
  - feat(scope): adicionar nova funcionalidade
  - fix(scope): corrigir um bug
  - chore(repo): atualizar documentação

- Como abrir um PR:
  1. Fork o repositório e crie uma branch chamada `feat/descricao-curta` ou `fix/descricao-curta`.
  2. Garanta que os testes passem e inclua uma descrição curta no corpo do PR.
  3. Referencie issues relacionadas usando `#`.

- Rodar o projeto localmente (Docker Compose):

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
```

- Lint / Tests: adicione informação aqui se você adicionar linters ou testes.

- Código de Conduta: por favor leia `CODE_OF_CONDUCT.md` e cumpra-o.
