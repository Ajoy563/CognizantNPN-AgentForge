"""Targeted repair-routing for ValidationOutput failures.

Given a ValidationOutput, computes which upstream stage(s) need to be
rerun and in what order — never blindly rerunning every stage on every
failure. This module only plans; it has no CrewAI dependency and never
executes any agent/task itself. A future Crew/service integration maps
each Stage to a callable (its build_*_agent/build_*_task pair) and drives
the loop using the RepairPlan this module returns.
"""

from dataclasses import dataclass, field
from enum import Enum

from ai.schemas.validation import ValidationOutput
from ai.tasks.validation import MAX_REPAIR_ITERATIONS

ABSOLUTE_MAX_REPAIR_ITERATIONS = 3  # matches ValidationOutput.iterations' le=3 bound


class Stage(str, Enum):
    BUSINESS_ANALYST = "business_analyst"
    SOLUTION_ARCHITECT = "solution_architect"
    TECHNOLOGY_ADVISOR = "technology_advisor"
    DELIVERY_PLANNER = "delivery_planner"
    VALIDATOR = "validator"


_FULL_CHAIN: tuple[Stage, ...] = (
    Stage.BUSINESS_ANALYST,
    Stage.SOLUTION_ARCHITECT,
    Stage.TECHNOLOGY_ADVISOR,
    Stage.DELIVERY_PLANNER,
    Stage.VALIDATOR,
)

# Routing rules (02_AI_SPEC.md section 8): each owner reruns from its own
# stage through Delivery Planner, then the Validator. Every route is a
# contiguous suffix of _FULL_CHAIN, so the union of any set of routes is
# always the single most-upstream route among them.
_OWNER_ROUTES: dict[str, tuple[Stage, ...]] = {
    "Business Analyst": _FULL_CHAIN,
    "Solution Architect": _FULL_CHAIN[1:],
    "Technology Advisor": _FULL_CHAIN[2:],
    "Delivery Planner": _FULL_CHAIN[3:],
    "Cross-stage": _FULL_CHAIN,
}


class RepairPlanStatus(str, Enum):
    NO_REPAIR_NEEDED = "no_repair_needed"
    REPAIR_PLANNED = "repair_planned"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    NO_ACTIONABLE_FAILURE = "no_actionable_failure"


@dataclass(frozen=True)
class RepairPlan:
    """The result of determine_repair_plan(). `stages` is empty unless
    `status` is REPAIR_PLANNED."""

    status: RepairPlanStatus
    stages: tuple[Stage, ...]
    owners: tuple[str, ...]
    issues_by_owner: dict[str, tuple[str, ...]] = field(default_factory=dict)
    reason: str = ""

    @property
    def is_actionable(self) -> bool:
        return self.status == RepairPlanStatus.REPAIR_PLANNED


def determine_repair_plan(
    validation_output: ValidationOutput,
    *,
    max_iterations: int = MAX_REPAIR_ITERATIONS,
) -> RepairPlan:
    """Compute the ordered, deduplicated set of stages to rerun.

    - PASS -> NO_REPAIR_NEEDED, empty plan.
    - iterations already at/above the (clamped) maximum -> MAX_ITERATIONS_REACHED,
      empty plan; the caller should stop repairing and return the latest
      results together with this ValidationOutput.
    - FAIL with no failed check naming a known owner -> NO_ACTIONABLE_FAILURE,
      empty plan; never invents a repair target.
    - otherwise -> REPAIR_PLANNED, with `stages` the dependency-ordered union
      of every actionable owner's route and `issues_by_owner` the issue text
      for each of those owners, for the caller to hand to the repaired stage.
    """
    effective_max = min(max_iterations, ABSOLUTE_MAX_REPAIR_ITERATIONS)

    if validation_output.status == "PASS":
        return RepairPlan(
            status=RepairPlanStatus.NO_REPAIR_NEEDED,
            stages=(),
            owners=(),
            reason="Validation status is PASS; no repair is needed.",
        )

    if validation_output.iterations >= effective_max:
        return RepairPlan(
            status=RepairPlanStatus.MAX_ITERATIONS_REACHED,
            stages=(),
            owners=(),
            reason=(
                f"{validation_output.iterations} repair iteration(s) already "
                f"attempted, at or above the maximum of {effective_max}. Stop "
                "repairing and return the latest results with this "
                "ValidationOutput."
            ),
        )

    owners = _actionable_owners(validation_output)
    if not owners:
        return RepairPlan(
            status=RepairPlanStatus.NO_ACTIONABLE_FAILURE,
            stages=(),
            owners=(),
            reason=(
                "Validation status is FAIL but no failed check names a "
                "known owner; refusing to invent a repair target."
            ),
        )

    return RepairPlan(
        status=RepairPlanStatus.REPAIR_PLANNED,
        stages=_merge_routes(owners),
        owners=owners,
        issues_by_owner=_issues_by_owner(validation_output, owners),
        reason=f"Failed check owner(s) {', '.join(owners)} require repair.",
    )


def _actionable_owners(validation_output: ValidationOutput) -> tuple[str, ...]:
    """Distinct owners (in first-seen order) named by a FAIL check, skipping
    any owner this routing table does not recognize rather than guessing."""
    seen: list[str] = []
    for check in validation_output.checks:
        if check.status != "FAIL":
            continue
        owner = check.owner
        if owner is None or owner not in _OWNER_ROUTES:
            continue
        if owner not in seen:
            seen.append(owner)
    return tuple(seen)


def _merge_routes(owners: tuple[str, ...]) -> tuple[Stage, ...]:
    """Union of every owner's route, in canonical dependency order.

    Every route is a suffix of _FULL_CHAIN, so filtering _FULL_CHAIN down
    to the stages any owner needs — rather than concatenating routes in
    owner-encounter order — is what keeps the result dependency-ordered
    regardless of the order owners appear in the failed checks.
    """
    needed = {stage for owner in owners for stage in _OWNER_ROUTES[owner]}
    return tuple(stage for stage in _FULL_CHAIN if stage in needed)


def _issues_by_owner(
    validation_output: ValidationOutput, owners: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    """For each actionable owner, the issue text of every FAIL check it owns —
    the validator's issue information relevant to that stage (requirement 7)."""
    result: dict[str, tuple[str, ...]] = {owner: () for owner in owners}
    for check in validation_output.checks:
        if check.status != "FAIL" or check.owner not in result:
            continue
        if check.issue:
            result[check.owner] = result[check.owner] + (check.issue,)
    return result
