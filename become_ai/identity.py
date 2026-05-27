"""AgentIdentity — who an agent is and how it remembers change.

An identity is the sum of an agent's state, traits, capabilities,
locked properties, and the history of transformations it has undergone.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .transformation import TransformationRecord


@dataclass
class AgentIdentity:
    """Represents an agent's identity at a point in time.

    Identities are immutable in spirit — use ``evolve()`` to produce
    a new identity with changes applied, preserving the original.

    Attributes:
        name: The agent's name.
        state: Current state identifier (e.g. "init", "bootcamp", "deployed").
        traits: Mutable key-value properties of the agent.
        capabilities: Skills and equipment the agent possesses.
        locked_traits: Trait keys that cannot be modified or removed.
        scores: Numeric scores for various metrics.
        achieved_milestones: Names of milestones the agent has reached.
        history: Ordered record of all transformations applied.
        created_at: When this identity was first created.
        custom_checks: Boolean flags for custom requirement evaluation.
        metadata: Extension data.
    """

    name: str
    state: str = "init"
    traits: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    locked_traits: set[str] = field(default_factory=set)
    scores: dict[str, float] = field(default_factory=dict)
    achieved_milestones: list[str] = field(default_factory=list)
    history: list[TransformationRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    custom_checks: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def evolve(
        self,
        state: str | None = None,
        traits: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
        locked_traits: set[str] | None = None,
        scores: dict[str, float] | None = None,
        achieved_milestones: list[str] | None = None,
        history: list[TransformationRecord] | None = None,
        custom_checks: dict[str, bool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentIdentity:
        """Create a new identity with specified changes applied.

        Only the fields you pass are changed; everything else is
        deep-copied from the current identity.
        """
        return AgentIdentity(
            name=self.name,
            state=state if state is not None else self.state,
            traits=traits if traits is not None else copy.deepcopy(self.traits),
            capabilities=(
                capabilities if capabilities is not None
                else list(self.capabilities)
            ),
            locked_traits=(
                locked_traits if locked_traits is not None
                else set(self.locked_traits)
            ),
            scores=scores if scores is not None else dict(self.scores),
            achieved_milestones=(
                achieved_milestones if achieved_milestones is not None
                else list(self.achieved_milestones)
            ),
            history=history if history is not None else list(self.history),
            custom_checks=(
                custom_checks if custom_checks is not None
                else dict(self.custom_checks)
            ),
            metadata=(
                metadata if metadata is not None
                else copy.deepcopy(self.metadata)
            ),
            created_at=self.created_at,
        )

    def lock_trait(self, key: str) -> AgentIdentity:
        """Lock a trait so it cannot be modified or removed."""
        new_locked = self.locked_traits | {key}
        return self.evolve(locked_traits=new_locked)

    def unlock_trait(self, key: str) -> AgentIdentity:
        """Unlock a previously locked trait."""
        new_locked = self.locked_traits - {key}
        return self.evolve(locked_traits=new_locked)

    def set_trait(self, key: str, value: Any) -> AgentIdentity:
        """Set a trait value. Raises ValueError if the trait is locked."""
        if key in self.locked_traits:
            raise ValueError(f"Cannot modify locked trait: '{key}'")
        new_traits = copy.deepcopy(self.traits)
        new_traits[key] = value
        return self.evolve(traits=new_traits)

    def add_capability(self, cap: str) -> AgentIdentity:
        """Add a single capability."""
        caps = set(self.capabilities) | {cap}
        return self.evolve(capabilities=sorted(caps))

    def remove_capability(self, cap: str) -> AgentIdentity:
        """Remove a single capability."""
        caps = set(self.capabilities) - {cap}
        return self.evolve(capabilities=sorted(caps))

    def set_score(self, metric: str, value: float) -> AgentIdentity:
        """Set a numeric score."""
        new_scores = dict(self.scores)
        new_scores[metric] = value
        return self.evolve(scores=new_scores)

    def achieve_milestone(self, name: str) -> AgentIdentity:
        """Record a milestone as achieved."""
        if name in self.achieved_milestones:
            return self
        return self.evolve(
            achieved_milestones=self.achieved_milestones + [name]
        )

    def transformation_count(self) -> int:
        """Number of transformations this identity has undergone."""
        return len(self.history)

    def summary(self) -> dict[str, Any]:
        """A concise summary of the identity's current state."""
        return {
            "name": self.name,
            "state": self.state,
            "traits": dict(self.traits),
            "capabilities": list(self.capabilities),
            "locked_traits": sorted(self.locked_traits),
            "scores": dict(self.scores),
            "milestones_achieved": len(self.achieved_milestones),
            "transformations": self.transformation_count(),
        }
