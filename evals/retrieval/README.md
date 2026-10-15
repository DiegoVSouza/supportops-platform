# Retrieval evaluation

`cases.json` is a versioned deterministic query fixture, not a production benchmark.
Run `uv run --locked python scripts/eval_retrieval.py` to compute hit@3 against the
local lexical retriever. This measures only those local documents and queries; it is
not a model-quality metric. No embedding provider or live LLM is called. Future replay
corpora must carry provenance and a separate run record.
