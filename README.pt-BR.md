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

O `check_full.py` retorna `2` enquanto o gate de dependência do P04 estiver incompleto.
P00–P03 usam wheels locais aprovados. Consulte `artifacts/evidence/`.

## Limitações

PostgreSQL, broker em serviço, recuperação persistente, integração MCP em rede, avaliação
replay e tracing end-to-end seguem INCOMPLETE. O adaptador de diagnóstico P04 passou com
SQLite e broker em memória, mas o wheel exige FastAPI 0.137.1 e conflita com a versão
fixada no P05; aguarda-se um pacote compatível para passar o gate. A avaliação local de
hit@k mede somente o conjunto determinístico versionado, não qualidade de modelo.
