"""Scorable forecast output — the only structured artifact the agent must emit.

This is kit-piece #3 ("可打分输出"). Deliberately tiny: just enough to compute
Brier / log-loss / numeric error + calibration and to feed the experience library.
NO typed pillar frame, NO coverage state machine (see ../../AGENTS.md guardrail #1).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Source:
    """One cited evidence item behind a number. `as_of` is the source's own timestamp;
    the as-of guard (kit #2) is what guarantees it is <= the question cutoff."""
    url: str
    as_of: Optional[str] = None          # ISO date/datetime of the source content
    note: str = ""


@dataclass
class ScorableForecast:
    """Provider-agnostic forecast record. One per question.

    forecast_type drives which fields matter:
      - number            -> point (+ optional low/high interval)
      - binary choice     -> probability in [0,1] for the resolved-yes option
      - multiple choice   -> option_probabilities (must sum ~1)
      - rank              -> ranking (ordered option ids)
    """
    task_id: str
    forecast_type: str                    # number | binary choice | simple/difficult multiple choice | rank
    as_of: str                            # the cutoff the forecast was made under (leak boundary)

    # answer space (fill what applies to forecast_type)
    answer: Any = None                    # the headline answer to put in \boxed{} (number or option letter)
    point: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    probability: Optional[float] = None   # binary: P(resolved-yes)
    option_probabilities: dict[str, float] = field(default_factory=dict)
    ranking: list[str] = field(default_factory=list)

    # calibration metadata (kit #3) — required, not optional, so overconfidence is measurable
    uncertainty: str = ""                 # short rationale for the interval / spread width
    confidence: str = "med"               # low | med | high

    # provenance + reasoning trail
    sources: list[Source] = field(default_factory=list)
    anchor: str = ""                      # the prior the forecast was anchored on (kit #1, A-class)
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
