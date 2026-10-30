# Progress — Nova PAT

- **Entregues (últimos commits/merges na main):** NOVAPAT-69 (cadastro de conteúdo de mídia finalizado); NOVAPAT-68 (redes sociais configuráveis na toolbar); NOVAPAT-67 (links da toolbar editáveis via SiteSettings); NOVAPAT-64/65/66 (toolbar de acessibilidade: fontes, alto contraste, UI/UX); NOVAPAT-63 (logo no header); NOVAPAT-62 (política de retenção e expurgo de usuários inativos).
- **Qualidade:** suíte estável com 211 testes automatizados aprovados (`pytest`).
- **Faltando:** 7 cards no Backlog do YouTrack (NOVAPAT-45, 46, 51, 54, 58, 59, 70); `django-simple-history` não instalado (ADR-005 pendente); `analytics` não está em `INSTALLED_APPS`; importador sem management command; `gspread` não em `requirements.txt`.
- **Dívidas técnicas conhecidas:** embed do Google Slides não suportado nativamente (fallback = link seguro); confirmação pendente do canal `id=9` para aplicativos em produção; `editor` sem permissão definida; `user_canal` sem efeito de permissão (reavaliar com produção).
