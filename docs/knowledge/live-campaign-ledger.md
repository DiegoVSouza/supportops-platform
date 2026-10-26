# Ledger seguro para campanhas RAG — P05

## Aprendizado

Não coloque conteúdo de tenant em estado operacional de campanha. Caso/trial, chamada, tokens e custo estimado bastam para contabilizar limites. Consultas, trechos recuperados, respostas, citações e argumentos de ferramentas continuam nos limites protegidos do runtime e não devem aparecer no ledger nem no relatório de retomada.

Reserve antes do despacho. Se uma resposta se perder e o uso for desconhecido, conserve a reserva integral e impeça o envio automático de novo. O ledger SQLite append-only valida caps cumulativos com transação; o lease do sistema operacional evita duas campanhas locais simultâneas.

## Limites atuais

Esta fase não envia chamadas ao Groq e não altera o stack Docker. A inspeção de retomada é somente leitura. O full fake gate foi executado com services omitidos e portanto reporta `INCOMPLETE`; a fase anterior tem evidência separada de Docker/service recovery. Dispatcher, aprovações, limites da conta, identidade do candidato, preflight, confirmação, campanha ampla, canário e rollback continuam pendentes.

## Resposta de entrevista (PT-BR)

Implementei contabilidade de campanha sem gravar dados de tenant: só IDs e métricas de uso entram no ledger. Reservas desconhecidas ficam contabilizadas e não são repetidas automaticamente. Isso protege contra subcontagem sem prometer exatamente uma chamada. A fase segue incompleta porque não tem dispatcher nem aprovações para o volume planejado.

## Interview answer (English)

I implemented campaign accounting without storing tenant data: only identifiers and usage metrics enter the ledger. Unknown reservations remain charged and are not replayed automatically, preventing undercounting without promising exactly-once calls. The phase remains incomplete because dispatch and campaign approvals are still missing.
