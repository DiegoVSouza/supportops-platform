"""P02 guardrails and bounded tool wrappers for local P05 adapters."""

from typing import Any, Callable

from supportops_toolkit.guardrails import guard
from supportops_toolkit.tools import ToolError, ToolSpec


def safe_retrieval_query(query: str) -> str:
    verdict = guard(query, role="support")
    if verdict.action == "block":
        raise ValueError("retrieval query blocked by P02 safety guard")
    return verdict.sanitized_text if verdict.action == "redact" else query


def bounded_tool(
    name: str,
    handler: Callable[..., dict[str, Any]],
    input_properties: dict[str, dict[str, Any]],
    output_properties: dict[str, dict[str, Any]],
) -> ToolSpec:
    input_schema = {
        "type": "object",
        "required": list(input_properties),
        "additionalProperties": False,
        "properties": input_properties,
    }
    output_schema = {
        "type": "object",
        "required": list(output_properties),
        "additionalProperties": False,
        "properties": output_properties,
    }
    tool = ToolSpec(name, handler, input_schema, output_schema, timeout_s=1.0, retries=0)

    def invoke(**kwargs: Any) -> dict[str, Any]:
        try:
            return tool(**kwargs)
        except ToolError as exc:
            raise ValueError(str(exc)) from exc

    return invoke
