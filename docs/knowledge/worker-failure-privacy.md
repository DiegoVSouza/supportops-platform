# Privacidade de falhas do worker / Worker failure privacy

## Resultado

Atualização da fase 025: spans P05 agora desativam tanto eventos automáticos de exceção quanto descrições automáticas de status. Testes com exporter em memória verificam os limites `worker.run` e `agent.triage`; a prova fake isolada observou sete spans correlacionados sem o sentinel. O trace persistido como evidência contém somente nomes de operações/serviços, nomes de atributos e contagens. A fase 024 permanece registrada como falha histórica e não foi consultada ou repetida.

A fase 022 converte texto arbitrário de exceção em categorias fixas antes da persistência local, da fila durável e da resposta autenticada da API. A fase 023 verificou esse contrato com PostgreSQL/Redis e serviços isolados em modo fake: o worker persistiu `invalid_input`; uma linha legada com texto sentinel foi retornada pela API apenas como `worker_failure`; chamadas sem token receberam 401. O sentinel não apareceu no banco, no outbox ou na resposta da API.

A aceitação fake completa passou com 133 testes, integração de serviço, isolamento de tenant, rastreamento correlacionado e recuperação após interrupção depois de um efeito sintético. O probe de falha específico não encontrou seu trace no Jaeger. A regressão com exporter em memória comprova a ausência de evento de exceção; o gate de serviço verifica rastreamento correlacionado na execução normal. Não inferimos entrega de trace para o probe específico.

O teste de serviço usou apenas o projeto Compose `p05-phase023-failure-privacy`, imagem local existente e mounts somente leitura do source/scripts P05. O inventário final confirma que os recursos temporários foram removidos e que containers, redes e volumes preexistentes mantiveram identidade e estado normalizado. O texto temporal de status de um container alheio avançou enquanto permaneceu em `Restarting (1)`; nenhum comando o selecionou.

Qualidade de modelo, dispatcher live, billing/quota, revisões humana e independente, aprovação de campanha e promoção continuam `PENDING`/`INCOMPLETE`. Esta verificação não avaliou respostas live e não autoriza chamadas ao provider.

## Interview answers

**PT — Como evitamos que um erro interno vaze pelo endpoint de tarefas?**

Persistimos e retornamos somente códigos de falha de uma lista fechada. A integração isolada verificou tanto o novo fluxo do worker quanto o mascaramento de um erro legado na API autenticada, sem reescrever o histórico.

**EN — How do we prevent internal errors from leaking through task status?**

We persist and return only fixed allowlisted failure codes. The isolated integration verified both the new worker flow and masking of a legacy error through the authenticated API, without rewriting historical records.

## Evidence

- `artifacts/evidence/service-failure-privacy-023/full-verified-command.txt`
- `artifacts/evidence/service-failure-privacy-023/full-verified-output.txt`
- `artifacts/evidence/service-failure-privacy-023/targeted-service-retry2.txt`
- `.planning/phases/023-service-failure-privacy/evidence/docker-inventory-reconciliation.json`
