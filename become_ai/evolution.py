"""EvolutionEngine — orchestrates transformation rules and validation.

The engine manages a set of transformations and applies them to identities,
enforcing all requirements, locked traits, and ordering constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .identity import AgentIdentity
from .transformation import Transformation


@dataclass
class EvolutionResult:
    """Outcome of an evolution step.

    Attributes:
        success: Whether the transformation was applied.
        identity: The new identity (or the original on failure).
        transformation: The transformation that was attempted.
        errors: Blocking reasons if the transformation could not be applied.
    """

    success: bool
    identity: AgentIdentity
    transformation: Transformation | None
    errors: list[str] = field(default_factory=list)


class EvolutionEngine:
    """Manages transformation rules and validates/applies them to identities.

    The engine is the central coordinator: it holds the set of known
    transformations and provides methods to discover applicable ones,
    validate them, and apply them.

    Args:
        transformations: Initial set of available transformations.
        strict: If True, raise on failed transformations instead of returning
                a result with errors.
    """

    def __init__(
        self,
        transformations: list[Transformation] | None = None,
        strict: bool = False,
    ) -> None:
        self._transformations: dict[str, Transformation] = {}
        self.strict = strict
        if transformations:
            for t in transformations:
                self.register(t)

    def register(self, transformation: Transformation) -> None:
        """Register a transformation with the engine."""
        self._transformations[transformation.id] = transformation

    def unregister(self, transformation_id: str) -> None:
        """Remove a transformation by its ID."""
        self._transformations.pop(transformation_id, None)

    @property
    def transformations(self) -> list[Transformation]:
        """All registered transformations."""
        return list(self._transformations.values())

    def get(self, transformation_id: str) -> Transformation | None:
        """Look up a transformation by ID."""
        return self._transformations.get(transformation_id)

    def find_applicable(
        self,
        identity: AgentIdentity,
        context: dict[str, Any] | None = None,
    ) -> list[Transformation]:
        """Find all transformations that can currently be applied.

        Args:
            identity: The agent identity to check against.
            context: Optional context for trigger evaluation.

        Returns:
            List of transformations whose requirements are met.
        """
        results = []
        ctx = context or {}
        for t in self._transformations.values():
            can, _ = t.can_apply(identity)
            if can:
                results.append(t)
        return results

    def find_triggered(
        self,
        identity: AgentIdentity,
        context: dict[str, Any],
    ) -> list[Transformation]:
        """Find transformations whose triggers match the given context.

        Returns only transformations that are both triggered AND applicable.
        """
        results = []
        for t in self._transformations.values():
            can, _ = t.can_apply(identity)
            if not can:
                continue
            for trigger in t.triggers:
                if trigger.matches(context):
                    results.append(t)
                    break
        return results

    def evolve(
        self,
        identity: AgentIdentity,
        transformation: Transformation,
    ) -> EvolutionResult:
        """Apply a single transformation to an identity.

        Args:
            identity: The starting identity.
            transformation: The transformation to apply.

        Returns:
            An EvolutionResult with the new identity or error details.
        """
        can, reasons = transformation.can_apply(identity)
        if not can:
            if self.strict:
                raise ValueError(
                    f"Cannot apply '{transformation.name}': {'; '.join(reasons)}"
                )
            return EvolutionResult(
                success=False,
                identity=identity,
                transformation=transformation,
                errors=reasons,
            )

        new_identity = transformation.apply(identity)
        return EvolutionResult(
            success=True,
            identity=new_identity,
            transformation=transformation,
        )

    def evolve_by_id(
        self,
        identity: AgentIdentity,
        transformation_id: str,
    ) -> EvolutionResult:
        """Apply a transformation by its registered ID."""
        t = self.get(transformation_id)
        if t is None:
            msg = f"Unknown transformation: '{transformation_id}'"
            if self.strict:
                raise ValueError(msg)
            return EvolutionResult(
                success=False,
                identity=identity,
                transformation=None,
                errors=[msg],
            )
        return self.evolve(identity, t)

    def evolve_all_applicable(
        self,
        identity: AgentIdentity,
        context: dict[str, Any] | None = None,
    ) -> list[EvolutionResult]:
        """Apply all currently applicable transformations, in order.

        Each successful transformation may unlock further transformations,
        so the process repeats until no more apply.

        Returns:
            List of results for each transformation applied.
        """
        results: list[EvolutionResult] = []
        current = identity
        max_rounds = len(self._transformations) + 1
        for _ in range(max_rounds):
            applicable = self.find_applicable(current, context)
            if not applicable:
                break
            # Apply the first applicable transformation each round
            result = self.evolve(current, applicable[0])
            results.append(result)
            if result.success:
                current = result.identity
            else:
                break
        return results

    def evolve_overnight(
        self,
        identity: AgentIdentity,
        steps: int = 5,
        context: dict[str, Any] | None = None,
    ) -> tuple[AgentIdentity, list[EvolutionResult]]:
        """Run multiple evolution steps (the "overnight mode").

        Args:
            identity: Starting identity.
            steps: Maximum number of transformations to attempt.
            context: Context for trigger evaluation.

        Returns:
            Tuple of (final identity, list of results).
        """
        current = identity
        results: list[EvolutionResult] = []
        for _ in range(steps):
            triggered = self.find_triggered(current, context or {})
            if not triggered:
                applicable = self.find_applicable(current, context)
                if not applicable:
                    break
                target = applicable[0]
            else:
                target = triggered[0]

            result = self.evolve(current, target)
            results.append(result)
            if result.success:
                current = result.identity
        return current, results
