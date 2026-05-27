"""TransformProtocol — rules and constraints governing transformations.

A protocol defines the legal transformation space: which state transitions
are allowed, what constraints they must satisfy, and how they compose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .identity import AgentIdentity
from .transformation import Transformation


@dataclass(frozen=True)
class StateRule:
    """A rule about a specific state.

    Attributes:
        state: The state this rule governs.
        max_entries: Maximum times an agent can enter this state (0 = unlimited).
        required_capabilities: Capabilities required to be in this state.
        terminal: If True, no transformations can leave this state.
    """

    state: str
    max_entries: int = 0
    required_capabilities: list[str] = field(default_factory=list)
    terminal: bool = False


@dataclass(frozen=True)
class TransitionRule:
    """A constraint on a specific state transition.

    Attributes:
        from_state: Source state (or '*' for any).
        to_state: Target state.
        allowed: Whether this transition is permitted.
        cooldown: Minimum number of other transformations between retries.
        max_uses: Maximum times this transition can fire (0 = unlimited).
    """

    from_state: str
    to_state: str
    allowed: bool = True
    cooldown: int = 0
    max_uses: int = 0


class TransformProtocol:
    """Defines the rules governing how transformations can proceed.

    A protocol acts as a validator layer above individual transformations:
    even if a transformation's own requirements are met, the protocol can
    block it if it violates global constraints.

    Args:
        state_rules: Rules about specific states.
        transition_rules: Constraints on transitions.
        forbidden_states: States that cannot be entered.
        max_total_transformations: Global cap on transformations (0 = unlimited).
        require_sequential: If True, only one transformation per state is allowed.
    """

    def __init__(
        self,
        state_rules: list[StateRule] | None = None,
        transition_rules: list[TransitionRule] | None = None,
        forbidden_states: set[str] | None = None,
        max_total_transformations: int = 0,
        require_sequential: bool = False,
    ) -> None:
        self._state_rules: dict[str, StateRule] = {
            r.state: r for r in (state_rules or [])
        }
        self._transition_rules: dict[tuple[str, str], TransitionRule] = {
            (r.from_state, r.to_state): r for r in (transition_rules or [])
        }
        self.forbidden_states: set[str] = forbidden_states or set()
        self.max_total_transformations = max_total_transformations
        self.require_sequential = require_sequential

    def validate(
        self,
        identity: AgentIdentity,
        transformation: Transformation,
    ) -> tuple[bool, list[str]]:
        """Check whether a transformation is allowed under this protocol.

        Returns:
            Tuple of (is_valid, list_of_violations).
        """
        violations: list[str] = []
        to_state = transformation.to_state
        from_state = transformation.from_state

        # Check forbidden states
        if to_state in self.forbidden_states:
            violations.append(f"State '{to_state}' is forbidden")

        # Check terminal state — can't leave it
        current_rule = self._state_rules.get(identity.state)
        if current_rule and current_rule.terminal:
            violations.append(
                f"State '{identity.state}' is terminal — no transitions out"
            )

        # Check transition rules
        key = (from_state, to_state)
        specific_rule = self._transition_rules.get(key)
        wildcard_rule = self._transition_rules.get(("*", to_state))

        rule = specific_rule or wildcard_rule
        if rule and not rule.allowed:
            violations.append(
                f"Transition '{from_state}' -> '{to_state}' is not allowed"
            )

        # Check cooldown
        if rule and rule.cooldown > 0:
            recent = identity.history[-rule.cooldown:]
            for rec in recent:
                if rec.from_state == from_state and rec.to_state == to_state:
                    violations.append(
                        f"Transition '{from_state}' -> '{to_state}' is on cooldown"
                    )
                    break

        # Check max uses
        if rule and rule.max_uses > 0:
            uses = sum(
                1 for rec in identity.history
                if rec.from_state == from_state and rec.to_state == to_state
            )
            if uses >= rule.max_uses:
                violations.append(
                    f"Transition '{from_state}' -> '{to_state}' has reached "
                    f"max uses ({rule.max_uses})"
                )

        # Check state entry limits
        target_rule = self._state_rules.get(to_state)
        if target_rule and target_rule.max_entries > 0:
            entries = sum(
                1 for rec in identity.history
                if rec.to_state == to_state
            )
            if entries >= target_rule.max_entries:
                violations.append(
                    f"State '{to_state}' has been entered {entries} times "
                    f"(max: {target_rule.max_entries})"
                )

        # Check required capabilities for target state
        if target_rule and target_rule.required_capabilities:
            missing = [
                cap for cap in target_rule.required_capabilities
                if cap not in identity.capabilities
            ]
            if missing:
                violations.append(
                    f"Missing capabilities for state '{to_state}': {missing}"
                )

        # Check global max transformations
        if self.max_total_transformations > 0:
            if identity.transformation_count() >= self.max_total_transformations:
                violations.append(
                    f"Maximum transformations reached ({self.max_total_transformations})"
                )

        # Check sequential requirement
        if self.require_sequential:
            if identity.history:
                last_to = identity.history[-1].to_state
                if from_state != "*" and from_state != last_to:
                    violations.append(
                        f"Sequential mode: expected from_state '{last_to}', "
                        f"got '{from_state}'"
                    )

        return (len(violations) == 0, violations)

    def is_terminal(self, state: str) -> bool:
        """Check if a state is terminal (no exits)."""
        rule = self._state_rules.get(state)
        return rule.terminal if rule else False

    def allowed_transitions(self, from_state: str) -> list[str]:
        """List all states that can be reached from the given state."""
        targets: list[str] = []
        for (src, dst), rule in self._transition_rules.items():
            if not rule.allowed:
                continue
            if src == from_state or src == "*":
                targets.append(dst)
        return targets
