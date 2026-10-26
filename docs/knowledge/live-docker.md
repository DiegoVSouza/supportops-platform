# Validação live com Docker e Groq

O teste sintético confirmou chamadas reais ao modelo openai/gpt-oss-20b. Os comandos, códigos de saída, consumo observado e falhas preservadas estão em artifacts/evidence/live-docker/. O modo fake continua padrão para regressão. Uma amostra pequena valida integração; não demonstra qualidade geral. O custo faturado continua PENDING.

Pergunta de entrevista: como diferenciar integração funcionando de qualidade do modelo?

PT: confirmar modelo, uso real, persistência e invariantes comprova a integração. Qualidade exige um conjunto representativo maior e análise dos erros, sem repetir amostras apenas para obter aprovação.

EN: verify model identity, actual usage, persistence and invariants to establish integration. Model quality requires a larger representative dataset and error analysis, without rerunning samples merely to obtain a pass.
