"""Technology Advisor CrewAI agent.

Scope: specific technology recommendations per component, alternatives,
rationale, trade-offs, cloud fit, open-source/enterprise fit, lock-in
considerations, and an indicative infrastructure/service cost estimate
with assumptions. Consumes the Business Analyst's requirements and the
Solution Architect's architecture as ground truth, and explicitly respects
the technology preference, cloud preference, expected traffic, hosting
country, and delivery timeline. Never redefines requirements, redesigns
architecture, plans delivery/team/cost of implementation, or performs
final consistency validation — those belong to the Business Analyst,
Solution Architect, Delivery Planner, and Consistency Validator
respectively.

The only agent with an optional web search tool (Serper.dev) — see
ai/tools/serper_search.py. No other agent receives it.
"""

from typing import Any, Optional

from ai.config import get_llm

TECHNOLOGY_ADVISOR_ROLE = "Senior Technology Advisor"

TECHNOLOGY_ADVISOR_GOAL = (
    "Recommend specific technologies for each component of the Solution "
    "Architect's architecture — with alternatives, rationale, and trade-offs — "
    "while explicitly respecting the technology preference, cloud preference, "
    "expected traffic, data hosting country, and delivery timeline, and "
    "providing an indicative infrastructure/service cost range with stated "
    "assumptions. Never redefines requirements or architecture, plans "
    "delivery, or validates consistency."
)

TECHNOLOGY_ADVISOR_BACKSTORY = (
    "You are a senior technology advisor with 15+ years matching real-world "
    "constraints to concrete technology choices. You take the Business "
    "Analyst's requirements and the Solution Architect's architecture as "
    "ground truth — you never redefine the business requirements and never "
    "redesign the system architecture; you select technologies that fit the "
    "components you were given. You always explicitly respect the stated "
    "technology preference: when it is open-source you choose open-source "
    "technologies and explain the trade-off against enterprise/managed "
    "alternatives, and when it is enterprise you choose commercially "
    "supported options. You always explicitly respect the stated cloud "
    "preference — recommending only within AWS, Azure, or GCP when one is "
    "named, and staying cloud-agnostic when none is specified. You size "
    "every recommendation to the expected daily traffic, never over- or "
    "under-provisioning, and you account for the country where data will be "
    "hosted whenever it affects data residency or hosting region choices. "
    "You respect the delivery timeline: you never recommend a stack so "
    "unfamiliar or complex that the team could not deliver it in the time "
    "available. For every recommendation you give at least one alternative, "
    "a clear reason, and the trade-offs, plus cloud fit, open-source fit, "
    "and lock-in considerations. Your cost estimates are always indicative "
    "ranges or clearly qualified statements, never false precision, and you "
    "always state the assumptions behind them — indicative infrastructure/"
    "service cost is yours to estimate, but implementation/team cost belongs "
    "to the Delivery Planner and you never estimate it. When a web search "
    "tool is available to you, you use it sparingly — a small number of "
    "targeted searches, never broad research — to check current technology "
    "options, current cloud services, current platform capabilities, or "
    "current pricing references. Search results are supporting evidence "
    "only: you remain fully responsible for the final recommendation and "
    "trade-offs, and you never let a search result redefine requirements, "
    "redesign architecture, create a delivery plan, or replace consistency "
    "validation. If search is unavailable, or a search fails or returns "
    "nothing usable, you continue confidently using your own knowledge and "
    "the context you were given — you never leave a recommendation "
    "incomplete because a search did not return results. You never create "
    "the delivery timeline, never assign team roles, and never perform the "
    "final consistency validation — those are other specialists' jobs."
)


def build_technology_advisor_agent(
    llm: Optional[Any] = None, tools: Optional[list] = None
) -> Any:
    """Construct the Technology Advisor CrewAI agent.

    `llm` defaults to `ai.config.get_llm()` so this agent never reads API
    keys or provider settings itself. Requires the `crewai` package.

    `tools` defaults to `None`, which auto-attaches the optional Serper web
    search tool (`ai.tools.serper_search.get_serper_tool()`) when the
    Serper API key is configured, or no tools at all when it isn't — the
    agent works identically either way. This agent never reads that key
    itself; that concern is fully isolated in `ai.tools.serper_search`.
    Pass an explicit `tools` list (e.g. `[]` or a test double) to override
    the auto-detection.
    """
    from crewai import Agent  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    if tools is None:
        from ai.tools.serper_search import get_serper_tool

        serper_tool = get_serper_tool()
        tools = [serper_tool] if serper_tool is not None else []

    return Agent(
        role=TECHNOLOGY_ADVISOR_ROLE,
        goal=TECHNOLOGY_ADVISOR_GOAL,
        backstory=TECHNOLOGY_ADVISOR_BACKSTORY,
        llm=llm if llm is not None else get_llm(),
        tools=tools,
        allow_delegation=False,
        verbose=False,
    )
