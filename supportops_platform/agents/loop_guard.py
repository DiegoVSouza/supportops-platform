"""P03-backed deterministic loop guard for agent execution boundaries."""

from supportops_obs.loopdetect import LoopDetector, StepRecord


class AgentExecutionGuard:
    def __init__(self, *, max_steps: int = 40, repeat_threshold: int = 3) -> None:
        self._detector = LoopDetector(max_steps=max_steps, repeat_threshold=repeat_threshold)

    def observe(self, *, tool: str | None = None, arguments: object = None,
                state: str | None = None, step_number: int = 0) -> dict[str, object]:
        signal = self._detector.observe(
            StepRecord(tool=tool, arguments=arguments, state=state, step_number=step_number)
        )
        return {"terminate": signal.detected, "reason": signal.reason, "count": signal.repeated_count}

    def reset(self) -> None:
        self._detector.reset()
