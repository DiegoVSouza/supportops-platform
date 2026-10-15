# P05 — Plataforma SupportOps

Serviço independente para suporte multi-tenant com API autenticada por JWT, retrieval
determinístico com citações, fronteira MCP local, tarefas assíncronas, aprovação humana
para refunds e interfaces de observabilidade. `LLM_MODE=fake` é o padrão.

## Demonstração local

```powershell
uv sync --locked
uv run --locked python scripts/demo.py
```

A demonstração usa memória do processo, tokens curtos, documentos sintéticos e nenhum
provedor de LLM. A aprovação de refund não produz efeito financeiro. Em fake mode, a
chave JWT é aleatória e efêmera; configure `JWT_SECRET` se os tokens precisarem sobreviver
a reinícios.

## Validação

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

O `check_full.py` reporta como incompletos os gates que dependem de serviços externos.
P00–P04 usam wheels locais versionadas e com proveniência no lock. Consulte
`artifacts/evidence/`.

A rota `POST /v1/tickets/{ticket_id}/triage` exige o escopo `triage:run`, consulta
somente documentos do tenant autenticado e devolve as citações junto ao trace fake do
agente. O servidor MCP Streamable HTTP verifica bearer token e deriva tenant/papéis do
contexto autenticado do SDK. O teste usa cliente oficial sobre ASGI no processo; não
comprova serviço TCP implantado.

## Limitações

PostgreSQL/pgvector, Redis, broker em serviço, recuperação persistente, serviço MCP TCP,
avaliação replay e tracing end-to-end seguem INCOMPLETE. O adaptador P04 0.1.2 passou com SQLite e
broker em memória; isso não substitui os serviços reais. A avaliação local de
hit@k mede somente o conjunto determinístico versionado, não qualidade de modelo.
