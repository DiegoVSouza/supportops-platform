# Conhecimento do projeto

As respostas de entrevista abaixo são fornecidas em inglês e português.

## Como a plataforma impede acesso entre tenants?

**EN:** A verified JWT supplies the subject, tenant, roles, and scopes. Repository and
tool-gateway methods receive that principal directly and filter by its tenant. A
missing scope is denied, and another tenant's resource is returned as not found.

**PT:** Um JWT verificado fornece sujeito, tenant, papéis e escopos. Os repositórios e
o gateway de ferramentas recebem esse principal diretamente e filtram pelo tenant.
Escopo ausente é negado; recursos de outro tenant retornam como não encontrados.

## Como a recuperação de falhas funciona?

**EN:** The local queue contract uses tenant-scoped idempotency keys, bounded retries,
and expiring worker leases. A redelivery reuses the same task identity; downstream
effects must also deduplicate by that stable identity. The current queue is an in-memory
double, so process-crash durability remains incomplete until PostgreSQL and SQS
service-backed gates pass. The approved P04 0.1.1 package is installed and its local
consumer contract passes.

**PT:** O contrato local da fila usa chaves de idempotência por tenant, tentativas
limitadas e leases com expiração. Uma nova entrega reutiliza a identidade da tarefa; o
efeito downstream também deve deduplicar por essa identidade estável. A fila atual é um
double em memória, então a durabilidade após queda do processo segue incompleta até que
os gates com PostgreSQL e SQS reais passem. O pacote P04 0.1.1 está instalado e seu
contrato consumidor local passou.

## Como o RAG trata prompt injection?

**EN:** Retrieved passages are citations and remain untrusted data. Retrieval has no
tool capability. Separate tool authorization checks the caller's verified scopes and
roles, while refund execution requires a separate approval subject. The offline MCP
mock injects its principal at creation. The separate Streamable HTTP server verifies
bearer tokens and derives identity only from SDK request context. Its authenticated
client test uses in-process ASGI, not a deployed TCP service.

**PT:** Trechos recuperados são citações e continuam sendo dados não confiáveis. O
retriever não possui acesso a ferramentas. A autorização de ferramentas verifica os
escopos e papéis do principal, enquanto um refund exige outro sujeito aprovador. O
mock MCP injeta o principal ao ser criado. O servidor Streamable HTTP separado verifica
bearer tokens e deriva identidade somente do contexto de requisição do SDK. O teste
autenticado usa ASGI no processo; o serviço TCP implantado segue não validado.

The local hybrid retriever uses deterministic hashed-token vectors plus lexical
ranking. Those vectors are control-flow fixtures, not semantic embeddings; model
quality remains PENDING. The PostgreSQL pgvector adapter/query and migration have
fake-connection contract tests, while real PostgreSQL/pgvector execution is INCOMPLETE.

O retriever híbrido local usa vetores determinísticos por hash de tokens e ranking
lexical. São fixtures de fluxo de controle, não embeddings semânticos; qualidade do
modelo permanece PENDING. O adaptador/consulta pgvector e a migration têm testes de
contrato com conexão fake; execução real PostgreSQL/pgvector segue INCOMPLETE.

## Como o agente usa RAG sem cruzar tenants?

**EN:** `POST /v1/tickets/{ticket_id}/triage` loads the ticket through the verified
principal, searches only that tenant's local corpus, and returns citations with the
fake agent trace. The retriever receives tenant identity from server-side ticket data,
not from request arguments. The fake result is a control-flow fixture, not model quality.

**PT:** `POST /v1/tickets/{ticket_id}/triage` carrega o chamado pelo principal
verificado, pesquisa somente o corpus local daquele tenant e devolve as citações com
o trace do agente fake. O tenant vem do chamado carregado no servidor, não dos
argumentos da requisição. O resultado fake valida fluxo de controle, não qualidade de modelo.

## Como o P05 mantém controle dual de refunds?

**EN:** The approval record stores `requested_by` from the verified token subject.
An approval decision is denied when that subject matches the requester, even if the
same subject also has an approver role. Another authorized subject can decide once.

**PT:** O registro da aprovação guarda `requested_by` a partir do sujeito do token
verificado. A decisão é negada quando esse sujeito é o mesmo solicitante, mesmo que
também tenha papel de aprovador. Outro sujeito autorizado pode decidir uma única vez.

## Phase 009 verified durable service flow

**EN:** The isolated local stack passed native asyncpg retrieval and pgvector migration/index checks, Redis atomic limits, signed MCP Streamable HTTP over loopback TCP, and durable API→P04 0.1.3 worker→P01 0.1.1 agent orchestration. It also tested API restart recovery, distinct human approval, indirect-injection blocking, correlated traces, dashboard/alerts, and worker termination after one simulated refund ledger commit. The job completed with one effect row. The API contract is 0.4.0 with additive task result/error fields (ADR-006). External identity, semantic quality, model cost and comparable latency remain INCOMPLETE/PENDING.

**PT:** A stack local isolada passou nos testes de retrieval asyncpg nativo e migration/índices pgvector, limites atômicos do Redis, MCP Streamable HTTP assinado via TCP loopback e fluxo durável API→worker P04 0.1.3→agente P01 0.1.1. Também foram testados reinício da API, aprovação por pessoa distinta, bloqueio de prompt injection indireto, traces correlacionados, dashboard/alertas e encerramento do worker após um único commit de efeito simulado no ledger. A tarefa terminou com uma linha de efeito. O contrato da API é 0.4.0, com campos aditivos de resultado/erro (ADR-006). Identidade externa, qualidade semântica, custo do modelo e latência comparável seguem INCOMPLETE/PENDING.

`artifacts/evidence/phase-009-full-gate-final.txt` is the reproducible acceptance record. `phase-009-crash-recovery.txt` isolates the kill-after-effect scenario. No provider call or external refund was made.


## Phase 010 — retry recovery and release provenance

**EN:** P05 0.4.1 now retries MCP connection failures wrapped in nested exception groups through the P04 retry contract, while authorization and permanent broker errors remain fail-closed. The standalone worker backs off for explicit botocore transport outages. A service E2E confirms the durable authorization snapshot remains unchanged through delayed approval resume; external revocation remains unimplemented. The local wheel has source/artifact commits, SHA-256 provenance, and a verified PostgreSQL migration consumer. Model quality, replay, cost, comparable latency, and production readiness remain unproven.

**PT:** O P05 0.4.1 agora repete falhas de conexão MCP encapsuladas em grupos de exceções através do contrato de retry do P04, mantendo falhas de autorização e erros permanentes do broker em fail-closed. O worker independente aguarda e tenta novamente falhas de transporte botocore explicitamente classificadas. Um E2E de serviços confirma que o snapshot durável de autorização não muda durante a retomada após aprovação; revogação externa ainda não foi implementada. O wheel local tem commits de origem/artefato, proveniência SHA-256 e teste consumidor da migration no PostgreSQL. Qualidade de modelo, replay, custo, latência comparável e prontidão de produção não foram comprovados.
