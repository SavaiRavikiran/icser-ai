"""Base agent with Langfuse instrumentation."""
import time
import structlog
from typing import Any, Callable
from langfuse import observe

from src.config import settings
from src.observability.langfuse_client import get_langfuse


logger = structlog.get_logger()


class BaseAgent:
    """Base class for all ICSR agents with built-in observability."""

    name: str = "base"

    async def __call__(self, state: dict) -> dict:
        """Execute the agent with Langfuse tracing."""
        case_id = state.get("case_id", "unknown")
        start_time = time.time()

        logger.info("agent_start", agent=self.name, case_id=case_id)

        try:
            result = await self._execute(state)
            duration = time.time() - start_time

            # Update token/cost tracking
            state["total_tokens_input"] += result.pop("_tokens_input", 0)
            state["total_tokens_output"] += result.pop("_tokens_output", 0)
            state["total_cost_usd"] += result.pop("_cost_usd", 0.0)

            logger.info(
                "agent_complete",
                agent=self.name,
                case_id=case_id,
                duration_ms=round(duration * 1000, 1),
            )
            return {**state, **result}

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "agent_failed",
                agent=self.name,
                case_id=case_id,
                error=str(e),
                duration_ms=round(duration * 1000, 1),
            )
            state["error"] = f"{self.name}: {str(e)}"
            return state

    async def _execute(self, state: dict) -> dict:
        """Override in subclass. Return dict of state updates."""
        raise NotImplementedError   