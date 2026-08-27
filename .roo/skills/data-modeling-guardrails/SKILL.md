---
name: data-modeling-guardrails
description: Ative esta skill sempre que for criar, alterar ou renomear um model Django, adicionar uma ForeignKey, ou implementar lógica que decida "qual tipo de objeto é este" a partir de um ID ou parâmetro recebido.
---

# Data Modeling Guardrails

## Instructions

# Data Modeling Guardrails

## Instruções

### 1. Nunca use apenas um ID para decidir de qual tabela um registro veio
Se dois models diferentes têm auto-increment próprio (cada um começando do 1), o mesmo número de ID pode existir nos dois ao mesmo tempo, representando registros completamente diferentes. Nunca escreva lógica do tipo "esse ID existe na tabela X? então é do tipo X" como forma de desambiguar — isso falha de forma imprevisível dependendo de quais registros existem no banco no momento.

### 2. Prefira desambiguação explícita a inferência por tentativa
Quando o sistema precisa saber "isso é do tipo A ou do tipo B", prefira um parâmetro, campo ou nome explícito que já carregue essa informação (ex: dois campos de formulário separados, um prefixo no valor, um campo de tipo dedicado) em vez de tentar adivinhar checando em qual tabela o valor "bate" primeiro.

### 3. Ao renomear um model, busque referências no projeto inteiro
Não limite a busca por referências ao módulo ou app onde a mudança foi solicitada. Rode uma busca global pelo nome antigo do model (`grep -rn` ou equivalente) cobrindo todos os apps do projeto, incluindo templates, admin, forms, filters e testes — e liste os arquivos encontrados antes de começar a editar, para confirmar escopo com quem pediu a mudança.

### 4. Ao ver nomes de model parecidos, pergunte antes de assumir que são intercambiáveis
Se o projeto tem dois models com nomes semelhantes (ex: `Categoria` e `AplicativoCategory`), não assuma que representam o mesmo conceito ou podem ser tratados de forma equivalente na lógica. Pergunte explicitamente se há uma distinção de domínio antes de escrever código que trata os dois da mesma forma.