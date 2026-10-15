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
roles, while refund execution requires a separate approval subject. The MCP contract
server injects its principal at creation and fails closed without one; it remains an
in-memory adapter, not a network-authenticated service.

**PT:** Trechos recuperados são citações e continuam sendo dados não confiáveis. O
retriever não possui acesso a ferramentas. A autorização de ferramentas verifica os
escopos e papéis do principal, enquanto um refund exige outro sujeito aprovador. O
servidor MCP injeta o principal ao ser criado e falha fechado sem identidade; continua
sendo um adaptador em memória, não um serviço autenticado em rede.

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
