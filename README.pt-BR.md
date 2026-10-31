# P05 — Plataforma SupportOps

<!-- case:start -->
## O case

- **Problema.** Automação de suporte cruza dados de tenant, ferramentas, trabalho em segundo plano e dinheiro. Um modelo não pode aprovar o próprio reembolso.
- **Decisão.** Tenant e papel vêm do contexto autenticado. O modelo propõe, um gate determinístico confere e uma segunda pessoa aprova; quem pediu é recusado. A busca é isolada por tenant e as respostas citam fontes.
- **Medido.** 179 testes e o gate de serviços isolado passaram na fase 033 (PostgreSQL, pgvector, Redis, MCP, recuperação de crash). O caminho live `demo-live-v1` tem 17 testes contra PostgreSQL 16, incluindo a fronteira do teto e reservas concorrentes. Nenhum provedor foi chamado nesses testes.
- **Como rodar.** `uv sync --locked && uv run --locked pytest`. Gate de serviços: `uv run --locked python scripts/check_full.py` (precisa de Docker).
- **Limites.** O valor do reembolso vem de uma ferramenta determinística, não do modelo. Qualidade semântica, custo e latência ainda não foram medidos.
- **Docs.** [Arquitetura](docs/architecture.md), [modelo de segurança](docs/harness/security.md), [runbook](docs/runbook.md).
<!-- case:end -->

Serviço independente para suporte multi-tenant com API JWT, retrieval determinístico
com citações, fronteira MCP local, tarefas assíncronas, aprovação humana para refunds e
interfaces de observabilidade. `LLM_MODE=fake` é o padrão.

## Demonstração local

```powershell
uv sync --locked
uv run --locked python scripts/demo.py
```

A demonstração usa memória do processo, tokens curtos e documentos sintéticos. Ela não
chama provedor de LLM e uma aprovação de refund não produz efeito financeiro. Em fake mode,
a chave JWT é aleatória e efêmera; defina `JWT_SECRET` se os tokens precisarem sobreviver a reinícios.

## Validação

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

O `check_full.py` executa os gates locais de serviço e retorna INCOMPLETE/código não zero quando um gate obrigatório é omitido.
P00–P04 usam wheels locais versionadas e com proveniência no lock. Consulte
`artifacts/evidence/`.

A rota `POST /v1/tickets/{ticket_id}/triage` exige o escopo `triage:run`, consulta
somente documentos do tenant autenticado e devolve as citações junto ao trace fake do
agente. O servidor MCP Streamable HTTP verifica bearer token e deriva tenant/papéis do
contexto autenticado do SDK. A fase 009 testa MCP assinado por TCP loopback, retrieval
asyncpg nativo, fila durável P04/P01, reinício da API, aprovação distinta e tracing.

## Limitações

PostgreSQL/pgvector, Redis, LocalStack, recuperação de worker após efeito, MCP TCP,
tracing, dashboard e alertas locais passaram. Identidade externa continua INCOMPLETE;
replay/modelo, custo e latência comparável continuam PENDING. O hit@k local mede apenas
fixtures determinísticas, não qualidade de modelo.
