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
P00–P04 usam wheels locais aprovados no lock. Consulte `artifacts/evidence/`.

A rota `POST /v1/tickets/{ticket_id}/triage` exige o escopo `triage:run`, consulta
somente documentos do tenant autenticado e devolve as citações junto ao trace fake do
agente. O servidor MCP continua somente em memória: injete um principal confiável ao
criá-lo; sem principal, as ferramentas falham fechadas.

## Limitações

PostgreSQL, broker em serviço, recuperação persistente, autenticação MCP em rede, avaliação
replay e tracing end-to-end seguem INCOMPLETE. O adaptador P04 0.1.1 passou com SQLite e
broker em memória; isso não substitui os serviços reais. A avaliação local de
hit@k mede somente o conjunto determinístico versionado, não qualidade de modelo.
