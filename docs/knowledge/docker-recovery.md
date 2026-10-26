# Recuperação do P05 após reinício do Docker

A aplicação reiniciava porque tentava conectar ao PostgreSQL parado. Os processos API/worker tinham `on-failure`, enquanto os serviços de infraestrutura não tinham política de reinício. Os logs mostraram falha de resolução de `postgres`; o estado dos containers confirmou a dependência parada.

A correção aplica `unless-stopped` a todos os serviços. A recuperação existente usou `docker update --restart unless-stopped` nos containers pertencentes apenas aos dois stacks P05, iniciou as dependências e reiniciou os processos. IDs e volumes foram preservados. O worker live fica explicitamente parado para evitar geração sem orçamento aprovado; o ambiente fake pode continuar funcionando.

A política respeita paradas manuais. Após `docker stop`, use `docker start` quando a retomada for desejada. Não é necessário recriar containers ou apagar volumes para recuperar esse incidente. O gate completo usa um terceiro projeto Compose vazio, portas exclusivas e modo fake; ele remove somente os recursos que criou.

## Entrevista — português

**Como você diagnosticou o incidente?** Cruzei o erro de DNS da aplicação com o estado do banco e as políticas de reinício. Corrigi a política de ciclo de vida e preservei os dados, depois verifiquei saúde e aceitação integrada em ambiente isolado.

## Interview — English

**How did you diagnose the incident?** I correlated the application DNS failure with the stopped database and inconsistent restart policies. I repaired lifecycle configuration without recreating containers or volumes, then checked health and isolated integrated acceptance.
