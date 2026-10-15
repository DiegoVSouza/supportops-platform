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
double, so process-crash durability remains incomplete until P04 supports P05's locked
FastAPI version and passes the service-backed gate.

**PT:** O contrato local da fila usa chaves de idempotência por tenant, tentativas
limitadas e leases com expiração. Uma nova entrega reutiliza a identidade da tarefa; o
efeito downstream também deve deduplicar por essa identidade estável. A fila atual é um
double em memória, então a durabilidade após queda do processo segue incompleta até que
P04 seja compatível com a versão FastAPI fixada no P05 e passe o gate com serviço real.

## Como o RAG trata prompt injection?

**EN:** Retrieved passages are citations and remain untrusted data. Retrieval has no
tool capability. Separate tool authorization checks the caller's verified scopes and
roles, while refund execution requires a human approval state. The MCP contract server
is an in-memory synthetic fixture, not a network-authenticated service.

**PT:** Trechos recuperados são citações e continuam sendo dados não confiáveis. O
retriever não possui acesso a ferramentas. A autorização de ferramentas verifica os
escopos e papéis do principal, enquanto um refund exige aprovação humana. O servidor
MCP contratual usa fixtures em memória e não é um serviço autenticado em rede.
