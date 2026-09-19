"""Single lightweight completion patch over the requirement ->
architecture -> technology -> delivery traceability graph.

Runs once, after the Delivery Planner, in plain Python: no LLM call, no
agent rerun, no loop. It only closes obvious structural gaps by attaching
a missing mapping to the best-fit item that already exists, so existing
generated content is never rewritten. It is internal — nothing it does is
reported to the user.

Three gaps are closed, in dependency order, because closing an earlier one
can create a later one:

1. An MVP/must requirement that no component or security control claims.
2. A component that no technology decision supports.
3. A component that no delivery workstream addresses.
"""

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput, Workstream
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

# Which layer should own a requirement of a given category, best first.
_CATEGORY_LAYERS: dict[str, tuple[str, ...]] = {
    "functional": ("application", "domain", "api"),
    "non_functional": ("infrastructure", "application"),
    "security": ("api", "infrastructure", "application"),
    "compliance": ("data", "infrastructure", "application"),
    "performance": ("infrastructure", "application", "data"),
    "availability": ("infrastructure", "application"),
    "scalability": ("infrastructure", "application"),
    "integration": ("external", "api", "application"),
    "data": ("data", "domain"),
    "ux": ("presentation", "api"),
}

# Words that suggest a technology decision serves a given layer.
_LAYER_TECH_WORDS: dict[str, tuple[str, ...]] = {
    "presentation": ("frontend", "ui", "web", "client", "mobile", "css", "react"),
    "api": ("api", "gateway", "backend", "framework", "http", "rest"),
    "application": ("backend", "framework", "runtime", "language", "service"),
    "domain": ("backend", "framework", "language", "runtime"),
    "data": ("database", "storage", "cache", "persistence", "sql", "queue"),
    "infrastructure": ("cloud", "host", "container", "deploy", "ci", "monitor", "infra"),
    "external": ("integration", "third", "payment", "email", "notification", "api"),
}


def _best_component_for(category: str, architecture: ArchitectureOutput):
    """The component that should own a requirement of this category."""
    for layer in _CATEGORY_LAYERS.get(category, ()):
        for component in architecture.components:
            if component.layer == layer:
                return component
    return architecture.components[0]


def _best_decision_for(layer: str, technology: TechnologyOutput):
    """The technology decision that most plausibly serves this layer."""
    words = _LAYER_TECH_WORDS.get(layer, ())
    for decision in technology.decisions:
        haystack = f"{decision.category} {decision.technology} {decision.purpose}".lower()
        if any(word in haystack for word in words):
            return decision
    return technology.decisions[0]


def _next_workstream_id(delivery: DeliveryOutput) -> str:
    highest = 0
    for workstream in delivery.workstreams:
        try:
            highest = max(highest, int(workstream.id.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return f"TASK-{highest + 1:03d}"


def _patch_requirement_coverage(
    requirements: RequirementsOutput, architecture: ArchitectureOutput
) -> ArchitectureOutput:
    claimed: set[str] = set()
    for component in architecture.components:
        claimed.update(component.satisfies)
    for control in architecture.security_controls:
        claimed.update(control.satisfies)

    mvp_ids = set(requirements.mvp_requirement_ids)
    missing = [
        req
        for req in requirements.requirements
        if (req.priority == "must" or req.id in mvp_ids) and req.id not in claimed
    ]
    if not missing:
        return architecture

    additions: dict[str, list[str]] = {}
    for req in missing:
        additions.setdefault(_best_component_for(req.category, architecture).id, []).append(req.id)

    components = [
        component.model_copy(update={"satisfies": component.satisfies + additions[component.id]})
        if component.id in additions
        else component
        for component in architecture.components
    ]
    return architecture.model_copy(update={"components": components})


def _patch_component_technology(
    architecture: ArchitectureOutput, technology: TechnologyOutput
) -> TechnologyOutput:
    supported: set[str] = set()
    for decision in technology.decisions:
        supported.update(decision.supports)

    orphaned = [c for c in architecture.components if c.id not in supported]
    if not orphaned:
        return technology

    additions: dict[str, list[str]] = {}
    for component in orphaned:
        additions.setdefault(_best_decision_for(component.layer, technology).id, []).append(
            component.id
        )

    decisions = [
        decision.model_copy(update={"supports": decision.supports + additions[decision.id]})
        if decision.id in additions
        else decision
        for decision in technology.decisions
    ]
    return technology.model_copy(update={"decisions": decisions})


def _patch_component_delivery(
    architecture: ArchitectureOutput, delivery: DeliveryOutput
) -> DeliveryOutput:
    addressed: set[str] = set()
    for workstream in delivery.workstreams:
        addressed.update(workstream.addresses)

    orphaned = [c for c in architecture.components if c.id not in addressed]
    if not orphaned:
        return delivery

    names = ", ".join(c.name for c in orphaned)
    workstream = Workstream(
        id=_next_workstream_id(delivery),
        name=f"Implement {names}",
        purpose=f"Build the {names} component(s), which no other workstream covers.",
        activities=[f"Implement {c.name}: {c.responsibility}" for c in orphaned],
        dependencies=["None"],
        deliverable=f"{names} implemented and integrated",
        addresses=[c.id for c in orphaned],
        effort="To be estimated with the delivery team",
    )
    return delivery.model_copy(update={"workstreams": delivery.workstreams + [workstream]})


def apply_completion_patch(
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
) -> tuple[ArchitectureOutput, TechnologyOutput, DeliveryOutput]:
    """Close obvious traceability gaps in one pass and return the patched
    architecture, technology, and delivery outputs. Never reruns an agent,
    never loops, and never reports anything to the user."""
    architecture = _patch_requirement_coverage(requirements, architecture)
    technology = _patch_component_technology(architecture, technology)
    delivery = _patch_component_delivery(architecture, delivery)
    return architecture, technology, delivery
