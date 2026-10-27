# Falhas seguras em tarefas assíncronas

## Persistência e exposição de erros

Workers não devem persistir nem retornar `str(exc)`: exceções podem conter conteúdo de tickets, respostas de provedores ou detalhes de infraestrutura. O P05 usa códigos fixos (`timeout`, `dependency_failure`, `invalid_input`, `authorization_failure`, `transient_failure` e `worker_failure`) antes de entregar falhas ao worker P04 instalado. O queue fake aplica a mesma regra.

Todos os spans do P05 desabilitam a gravação automática de eventos de exceção. O status do span ainda pode indicar erro, sem anexar mensagem, traceback ou atributos arbitrários da exceção.

Leituras duráveis também normalizam valores antigos antes de montar o status da tarefa. A rota autenticada `/v1/tasks/{id}` repete a normalização como última fronteira e retorna apenas um código conhecido ou `null`. Isso não reescreve linhas históricas. Reprocessamento e migração de dados exigem uma fase separada, caso sejam necessários.

O teste offline usa o worker P04 instalado e confirma que uma exceção permanente com conteúdo privado chega ao estado do worker como `worker_failure`; uma falha transitória continua usando o contrato de retry. O full gate da fase 022 pulou serviços Docker para preservar a stack P05 em execução, portanto a confirmação com PostgreSQL/Redis permanece INCOMPLETE.

## Safe asynchronous task failures

### How should worker failures be exposed?

**EN:** Do not persist or return `str(exc)`: exception messages may contain ticket data, provider responses, or infrastructure details. Map exceptions to fixed codes before the P04 worker boundary, and disable automatic exception events on P05 spans. Normalize durable reads and the authenticated task-status response again, so legacy raw strings are masked without rewriting historical rows.

**PT:** Não persista nem retorne `str(exc)`: mensagens de exceção podem conter dados de tickets, respostas de provedores ou detalhes da infraestrutura. Converta exceções em códigos fixos antes do limite do worker P04 e desabilite eventos automáticos de exceção nos spans P05. Normalize novamente as leituras duráveis e a resposta autenticada do status da tarefa, mascarando strings antigas sem reescrever o histórico.

Evidence: `artifacts/evidence/worker-failure-privacy/focused-tests.txt` and `full-gate.txt`. The offline gate does not prove service-backed behavior; PostgreSQL/Redis verification remains INCOMPLETE.
