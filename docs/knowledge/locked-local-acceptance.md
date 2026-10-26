# Validação local com o ambiente travado

Os gates Python devem usar `uv run --locked python scripts/check_full.py`. O script usa `sys.executable` para seus subprocessos; chamar com o Python global também executa os testes e consumidores fora do `.venv`, produzindo falsos diagnósticos de dependências ausentes.

A execução corrigida dos checks offline passou os 127 testes, RAG determinístico, OpenAPI e proveniência dos cinco pacotes. A regressão deliberada foi rejeitada com o exit esperado. A saída antiga foi preservada em `artifacts/evidence/live-token-reservations/full-skip-services.txt`; a nova está em `full-locked-skip-services.txt`.

A validação de serviços deve usar um namespace Docker vazio e portas loopback livres, com `P05_COMPOSE_PROJECT` e `P05_EVIDENCE_PREFIX` próprios. O gate recusa um projeto já ocupado e limpa somente os recursos que criou. O worker live existente deve permanecer parado até autorização e cumprimento dos gates de campanha.

Nesta execução, o gate completo terminou com exit 0 no projeto temporário `p05-locked-acceptance-021`, incluindo segurança, traces e recuperação após efeito. O comparativo dos containers existentes não apresentou diferenças de identidade/estado; os recursos temporários foram removidos. A evidência está em `artifacts/evidence/locked-acceptance/` e a qualidade do modelo real continua pendente.

## Entrevista — PT-BR

**Como você distingue um defeito do produto de um problema de ambiente?** Confiro o interpretador e os pacotes realmente usados pelo comando, preservo a falha original e executo o gate no ambiente travado. O resultado só vale para as camadas exercitadas: fixtures e serviços fake não comprovam qualidade do modelo real.

## Interview — English

**How do you distinguish a product defect from an environment issue?** I verify the actual interpreter and installed packages, preserve the original failure, and run the gate in the locked environment. Its result applies only to exercised layers: fixtures and fake services do not establish real model quality.
