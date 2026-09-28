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

- Migration hygiene (Django):
  1. Never edit a migration that has already been applied. Create a new
     migration to correct it.
  2. Never delete a migration file without first unmarking it in the
     database: `python manage.py migrate <app> <previous_migration> --fake`.
  3. After reorganizing migrations, clean orphan records in
     `django_migrations` via `MigrationRecorder`.
  4. Before committing any migration change, run:
     `python manage.py migrate --check` and
     `python manage.py makemigrations --check --dry-run`.
     Violating these rules breaks pytest, CI, and other developers'
     environments — not the one who caused the mess.

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

- Higiene de migraciones (Django):
  1. Nunca edite una migración ya aplicada. Cree una nueva migración
     para corregirla.
  2. Nunca borre un archivo de migración sin antes desmarcarlo en la
     base de datos: `python manage.py migrate <app> <migración_anterior> --fake`.
  3. Tras reorganizar migraciones, limpie registros huérfanos en
     `django_migrations` vía `MigrationRecorder`.
  4. Antes de commitear cualquier cambio en migraciones, ejecute:
     `python manage.py migrate --check` y
     `python manage.py makemigrations --check --dry-run`.
     Violar estas reglas rompe pytest, CI y el entorno de otros
     desarrolladores — no el de quien causó el desastre.

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

- Higiene de migrações (Django):
  1. Nunca edite uma migração já aplicada. Crie uma migração nova para
     corrigi-la.
  2. Nunca apague um arquivo de migração sem antes desmarcá-lo no banco:
     `python manage.py migrate <app> <migração_anterior> --fake`.
  3. Após reorganizar migrações, limpe registros órfãos em
     `django_migrations` via `MigrationRecorder`.
  4. Antes de commitar qualquer mudança em migrações, rode:
     `python manage.py migrate --check` e
     `python manage.py makemigrations --check --dry-run`.
     Violar essas regras quebra pytest, CI e o ambiente de outros
     desenvolvedores — não o de quem causou a bagunça.

- Código de Conduta: por favor leia `CODE_OF_CONDUCT.md` e cumpra-o.