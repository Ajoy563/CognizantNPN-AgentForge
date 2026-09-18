"""Optional Serper.dev web search tool — available only to the Technology
Advisor (02_AI_SPEC.md section 5, "Optional Serper").

Serper is disabled unless SERPER_API_KEY is set in the environment (and
.env, if present); the workflow must work identically without it. No other
module reads SERPER_API_KEY directly — everything goes through
is_serper_configured()/get_serper_tool() so the concern stays isolated
here, exactly like ai/config.py isolates the LLM provider key(s).
"""

from typing import Any, Optional
import os

from dotenv import load_dotenv

load_dotenv()

# "A small number of targeted searches, not broad research" — bounds total
# Serper calls per task run and results per call, so a chatty agent can't
# threaten the ~2-minute end-to-end generation budget.
MAX_SERPER_SEARCHES = 3
SERPER_RESULTS_PER_SEARCH = 5


def is_serper_configured() -> bool:
    """Whether SERPER_API_KEY is present (non-blank) in the environment."""
    return bool(os.getenv("SERPER_API_KEY", "").strip())


def get_serper_tool() -> Optional[Any]:
    """Construct the Serper web search tool when it's configured.

    Returns None — never raises — when SERPER_API_KEY is missing or when
    `crewai_tools` isn't installed; callers must treat None as "no tool
    available" and continue without it, which is exactly what
    `ai.agents.technology_advisor.build_technology_advisor_agent` does.

    Bounded to a small number of targeted searches (`max_usage_count`)
    with a small result set per search (`n_results`), and configured with
    `tool_failure_policy=WARN` so that a failed/slow/unusable Serper call
    is recorded and the agent continues with its existing LLM context
    instead of aborting the whole Technology Advisor stage.
    """
    if not is_serper_configured():
        return None

    try:
        from crewai.tools.tool_failure import ToolFailurePolicy
        from crewai_tools import SerperDevTool
    except ImportError:
        return None

    return SerperDevTool(
        n_results=SERPER_RESULTS_PER_SEARCH,
        max_usage_count=MAX_SERPER_SEARCHES,
        tool_failure_policy=ToolFailurePolicy.WARN,
    )
