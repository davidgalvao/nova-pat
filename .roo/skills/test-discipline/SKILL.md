---
name: test-discipline
description: Ative esta skill sempre que terminar qualquer alteração de código (view, model, template, service, migration) — antes de reportar a tarefa como concluída ou pedir validação.
---

# Test Discipline

## Instructions

# Test Discipline

## Instruções

### 1. Rode a suíte completa relevante, não só o teste que motivou a mudança
Depois de qualquer alteração, rode toda a suíte de testes do app afetado (ex: `pytest search/tests/ -v`), não apenas o teste específico que você estava tentando corrigir. Uma correção pode consertar um teste e quebrar outro — só rodando o conjunto completo isso aparece.

### 2. Reporte o resultado sempre no mesmo formato, sem que seja pedido
Ao final de qualquer rodada de testes, informe: quantos passaram, quantos falharam, e o nome de cada teste que falhou. Não espere o usuário perguntar "e os testes, passaram?" — inclua isso proativamente no relatório da tarefa.

### 3. Nunca declare uma tarefa concluída sem ter rodado os testes por último
Se você alterou código depois da última rodada de testes (mesmo uma alteração pequena), rode a suíte de novo antes de reportar como pronto. "Deveria funcionar" não substitui "rodei e confirmei que funciona".

### 4. Se um teste que passava começar a falhar depois de uma correção não relacionada, avise
Se ao corrigir um bug você notar que um teste diferente, que passava antes, agora falha (ou vice-versa — um teste que falhava começa a passar sem motivo aparente ligado à sua mudança), isso é sinal de acoplamento ou ambiguidade que merece ser sinalizado explicitamente, não apenas corrigido silenciosamente na tentativa seguinte.