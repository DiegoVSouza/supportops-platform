# P05 — Plataforma SupportOps

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
