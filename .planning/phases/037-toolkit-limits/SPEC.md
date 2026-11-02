# Phase 037: toolkit limits on the live path

Status: done.

Owner decision (2026-11-02): the P02 feature `token-limit-in-agent-path` closes with a real adapter in P05, not by dropping it.

P02 does not own an LLM runtime, so callers report usage through `ExecutionLimits.consume(tokens=...)`. P05's fake path already does this with word counts. The live demo path (`agents/demo_live.py`) bounds money in a ledger and bytes per request, but never reports real tokens to the toolkit limits.

## Requirements

- LIM-001: each live triage run owns one `ExecutionLimits` (steps, tokens, seconds).
- LIM-002: after each settled provider receipt the run reports the real `input_tokens + output_tokens` and one step. A limit crossing ends the run with `AccountedDenied("execution_limit")`.
- LIM-003: before each provider call the run checks the time limit. An expired run does not contact the provider.
- LIM-004: limit values are policy, not measurements. They are named constants with a comment, and no number is claimed as a result.

## Out of scope

Changing P02, the ledger, the public run list or the API contract.
