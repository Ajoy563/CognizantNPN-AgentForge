"""Derive a concise project title for the report heading.

The AI pipeline is frozen, so no agent produces a title field. This module
recovers a short 4-8 word title from the Business Analyst's existing
problem statement using deterministic, conservative rules — and returns
the neutral fallback whenever it cannot do so confidently. It never
returns the raw business idea, and never truncates a sentence mid-word.
"""

import re

FALLBACK_TITLE = "Solution Blueprint"

# A system noun tells us what is being built; an activity noun tells us
# what it does. A title needs at least one of them to be meaningful.
SYSTEM_NOUNS = (
    "platform", "marketplace", "portal", "dashboard", "system", "application",
    "app", "service", "tool", "hub", "network", "exchange", "tracker",
    "gateway", "suite", "engine", "workspace", "registry", "catalogue", "catalog",
)
ACTIVITY_NOUNS = (
    "management", "booking", "scheduling", "optimization", "optimisation",
    "monitoring", "tracking", "analytics", "payments", "delivery", "onboarding",
    "reporting", "ordering", "billing", "pre-order", "preorder", "checkout",
    "collaboration", "compliance", "forecasting", "recommendation", "matching",
    "provisioning", "automation", "personalization", "personalisation",
)

_STOPWORDS = frozenset("""
a an the and or but for nor so yet of in on at to from by with without within
is are was were be been being has have had do does did will would can could
should may might must there their they them it its this that these those
no not non any all some each every other another such as if then than when
while where which who whom whose what why how about into over under again
more most many much few less least very too also just only own same because
currently today lack lacks lacking need needs needed want wants able easy
way ways make makes making provide provides providing allow allows allowing
using use uses used new existing current single multiple various different
local small large big major minor online offline digital
across through between among per via upon around behind beyond during
before after since until above below off out up down across-the
""".split())

# Words that only ever describe the *shape* of a problem statement.
_NOISE = frozenset({"centralized", "centralised", "solution", "problem", "business", "idea"})

# Without a part-of-speech tagger, verbs and loose adjectives are what turn
# a title into word salad ("Company Waste Money Idle GPU"). Blocking the
# common ones keeps only subject nouns.
_VERBS = frozenset("""
waste wastes wasting manage manages managing showcase showcases sell sells
selling buy buys buying build builds building create creates creating offer
offers offering handle handles handling process processes processing order
orders ordering find finds finding get gets getting keep keeps keeping run
runs running give gives giving take takes taking see sees seeing know knows
knowing help helps helping improve improves improving reduce reduces reducing
increase increases increasing support supports supporting enable enables
enabling connect connects connecting share shares sharing send sends sending
receive receives receiving store stores storing view views viewing search
searches searching browse browses browsing pay pays paying book books
showcasing coordinate coordinates coordinating streamline streamlines
list lists source sources reserve reserves spoil spoils struggle struggles
want wants enter enters submit submits access accesses
""".split())

# Real nouns, but too generic to name a project by. Kept as a last resort
# so "Companies waste money on idle GPU capacity" yields "GPU Capacity
# Management" rather than "Company Money Management".
_GENERIC_SUBJECTS = frozenset("""
company organisation organization firm enterprise customer client user
people person team member money thing place area part item one
""".split())

_ADJECTIVES = frozenset("""
better best good great easy simple quick fast slow idle busy nearby daily
weekly monthly yearly entire whole real live full empty high low old young
modern legacy manual automatic complex simplified seamless efficient
""".split())

# Adverbs are an open class, so they cannot be listed. An "-ly" ending is
# a reliable signal for them; these few real nouns are the exceptions.
_LY_NOUNS = frozenset({"supply", "reply", "family", "assembly", "anomaly", "monopoly", "ally", "rally"})


def _is_adverb(word: str) -> bool:
    return len(word) > 4 and word.endswith("ly") and word not in _LY_NOUNS


_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+&/-]*")


# Endings where a trailing "s" is part of the word, not a plural marker —
# "surplus" must never become "surplu".
_NOT_PLURAL_ENDINGS = ("ss", "us", "is", "os", "as", "ics")


def _singular(word: str) -> str:
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("sses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(_NOT_PLURAL_ENDINGS):
        return word[:-1]
    return word


def _title_case(words: list) -> str:
    out = []
    for word in words:
        if word.isupper() and len(word) <= 4:
            out.append(word)          # keep acronyms like GPU, API, AI
        elif "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)


def derive_project_title(problem: str, business_goals=None) -> str:
    """A concise title for this project, or FALLBACK_TITLE if unsure.

    Reads only the problem statement (plus business goals as a secondary
    source). Never returns the raw text back.
    """
    source = str(problem or "")
    if business_goals:
        source = f"{source} {' '.join(str(goal) for goal in business_goals)}"

    tokens = [match.group(0) for match in _WORD.finditer(source)]
    if not tokens:
        return FALLBACK_TITLE

    system_word = ""
    activity_word = ""
    domain: list = []
    generic: list = []
    seen = set()

    for raw in tokens:
        lowered = raw.lower()
        base = _singular(lowered)

        if not system_word and base in SYSTEM_NOUNS:
            system_word = base
            continue
        if not activity_word and lowered in ACTIVITY_NOUNS:
            activity_word = lowered
            continue
        if lowered in _STOPWORDS or lowered in _NOISE or len(lowered) < 3:
            continue
        if lowered in _VERBS or base in _VERBS or lowered in _ADJECTIVES:
            continue
        if _is_adverb(lowered):
            continue
        if base in SYSTEM_NOUNS or lowered in ACTIVITY_NOUNS:
            continue
        if base in seen:
            continue
        seen.add(base)
        word = raw if raw.isupper() else base
        (generic if base in _GENERIC_SUBJECTS else domain).append(word)

    # Without a system or activity noun there is nothing to call the thing.
    if not system_word and not activity_word:
        return FALLBACK_TITLE
    domain = domain or generic
    if not domain:
        return FALLBACK_TITLE

    # Domain words first (they carry the subject), then what it does, then
    # what it is: "Bakery Pre-order Platform".
    # At most two subject nouns: more than that and the title stops
    # reading like a name and starts reading like a sentence fragment.
    tail = [word for word in (activity_word, system_word) if word]
    words = domain[:2] + tail

    if len(words) < 2:
        return FALLBACK_TITLE
    return _title_case(words[:8])
