"""Transformation — a state transition an agent can undergo.

A transformation defines how an agent moves from one state to another,
what triggers it, and what requirements must be met before it can proceed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TriggerType(Enum):
    """What causes a transformation to initiate."""

    MANUAL = "manual"
    MILESTONE = "milestone"
    SCORE_THRESHOLD = "score_threshold"
    TIME_BASED = "time_based"
    EXTERNAL_EVENT = "external_event"
    SELF_INITIATED = "self_initiated"


@dataclass(frozen=True)
class Trigger:
    """A trigger that can initiate a transformation.

    Attributes:
        type: The category of trigger.
        condition: A description or expression of when this fires.
        metadata: Additional context for evaluation.
    """

    type: TriggerType
    condition: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def matches(self, context: dict[str, Any]) -> bool:
        """Check if this trigger fires given the current context.

        Simple evaluation: if condition is a key in context, check equality.
        Otherwise treat condition as a descriptive tag and check presence.
        """
        if self.type == TriggerType.MANUAL:
            return context.get("manual_trigger") == self.condition

        if self.type == TriggerType.MILESTONE:
            achieved = context.get("achieved_milestones", [])
            return self.condition in achieved

        if self.type == TriggerType.SCORE_THRESHOLD:
            score = context.get("score", 0)
            try:
                threshold = float(self.condition)
            except ValueError:
                return False
            return score >= threshold

        if self.type == TriggerType.TIME_BASED:
            return context.get("time_elapsed", False) is True

        if self.type == TriggerType.EXTERNAL_EVENT:
            return context.get("event") == self.condition

        if self.type == TriggerType.SELF_INITIATED:
            return context.get("self_initiated", False) is True

        return False


class RequirementType(Enum):
    """What kind of requirement must be satisfied."""

    TRAIT = "trait"
    CAPABILITY = "capability"
    SCORE = "score"
    MILESTONE = "milestone"
    CUSTOM = "custom"


@dataclass(frozen=True)
class Requirement:
    """A prerequisite that must be met before a transformation can proceed.

    Attributes:
        type: The category of requirement.
        name: What is required (trait name, capability key, etc.).
        value: The expected value or threshold.
        description: Human-readable explanation.
    """

    type: RequirementType
    name: str
    value: Any = None
    description: str = ""

    def is_satisfied(self, identity: "AgentIdentity") -> bool:  # type: ignore[name-defined]
        """Check whether an identity satisfies this requirement."""
        from .identity import AgentIdentity

        if self.type == RequirementType.TRAIT:
            val = identity.traits.get(self.name)
            if val is None:
                return False
            return val == self.value if self.value is not None else True

        if self.type == RequirementType.CAPABILITY:
            return self.name in identity.capabilities

        if self.type == RequirementType.SCORE:
            actual = identity.scores.get(self.name, 0)
            try:
                threshold = float(self.value)
            except (TypeError, ValueError):
                return False
            return actual >= threshold

        if self.type == RequirementType.MILESTONE:
            return self.name in identity.achieved_milestones

        if self.type == RequirementType.CUSTOM:
            custom = identity.custom_checks.get(self.name)
            return bool(custom) if custom is not None else False

        return False


@dataclass
class Transformation:
    """A state transition an agent can undergo.

    Defines the move from one identity state to another, including
    what triggers it, what requirements must be met, and what changes
    it applies to the agent's identity.

    Attributes:
        name: Human-readable name of the transformation.
        from_state: The source state identifier (use '*' for any state).
        to_state: The target state identifier.
        triggers: What can initiate this transformation.
        requirements: Prerequisites that must be satisfied.
        adds_traits: Traits to add or update during transformation.
        removes_traits: Trait keys to remove during transformation.
        adds_capabilities: Capabilities to grant.
        removes_capabilities: Capabilities to revoke.
        locked: If True, this transformation cannot be reversed.
        description: Human-readable explanation of what changes and why.
        metadata: Extra data for extensions.
    """

    name: str
    from_state: str
    to_state: str
    triggers: list[Trigger] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    adds_traits: dict[str, Any] = field(default_factory=dict)
    removes_traits: list[str] = field(default_factory=list)
    adds_capabilities: list[str] = field(default_factory=list)
    removes_capabilities: list[str] = field(default_factory=list)
    locked: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.now)

    def can_apply(self, identity: "AgentIdentity") -> tuple[bool, list[str]]:  # type: ignore[name-defined]
        """Check whether this transformation can be applied to the given identity.

        Returns:
            A tuple of (can_apply, list_of_blocking_reasons).
        """
        reasons: list[str] = []

        # Check current state
        if self.from_state != "*" and identity.state != self.from_state:
            reasons.append(
                f"Wrong state: need '{self.from_state}', currently '{identity.state}'"
            )

        # Check requirements
        for req in self.requirements:
            if not req.is_satisfied(identity):
                reasons.append(
                    f"Unmet requirement: {req.description or f'{req.type.value}:{req.name}'}"
                )

        # Check locked traits — can't remove them
        for trait_key in self.removes_traits:
            if trait_key in identity.locked_traits:
                reasons.append(f"Cannot remove locked trait: '{trait_key}'")

        return (len(reasons) == 0, reasons)

    def apply(self, identity: "AgentIdentity") -> "AgentIdentity":  # type: ignore[name-defined]
        """Apply this transformation to an identity, returning a new identity.

        Raises ValueError if the transformation cannot be applied.
        """
        can, reasons = self.can_apply(identity)
        if not can:
            raise ValueError(
                f"Cannot apply transformation '{self.name}': {'; '.join(reasons)}"
            )

        record = TransformationRecord(
            transformation_id=self.id,
            transformation_name=self.name,
            from_state=self.from_state if self.from_state != "*" else identity.state,
            to_state=self.to_state,
            timestamp=datetime.now(),
            metadata=self.metadata.copy(),
        )

        # Apply changes
        new_traits = {**identity.traits}
        for k, v in self.adds_traits.items():
            new_traits[k] = v
        for k in self.removes_traits:
            if k not in identity.locked_traits:
                new_traits.pop(k, None)

        new_capabilities = set(identity.capabilities)
        new_capabilities.update(self.adds_capabilities)
        new_capabilities -= set(self.removes_capabilities)

        new_history = identity.history + [record]

        return identity.evolve(
            state=self.to_state,
            traits=new_traits,
            capabilities=sorted(new_capabilities),
            history=new_history,
        )


@dataclass
class TransformationRecord:
    """A record of a transformation that was applied.

    Stored in an agent's history to provide a full audit trail.
    """

    transformation_id: str
    transformation_name: str
    from_state: str
    to_state: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
