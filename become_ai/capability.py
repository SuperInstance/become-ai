"""CapabilityTree — hierarchical capabilities with prerequisite chains.

A capability tree models the relationships between capabilities: which
ones require others, how they unlock, and how to find paths to acquire
a desired capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityNode:
    """A single capability in the tree.

    Attributes:
        name: Unique capability identifier.
        description: What this capability enables.
        prerequisites: Names of capabilities that must be held first.
        category: Grouping (e.g. "core", "combat", "social").
        tier: Difficulty/importance tier (0 = base, higher = more advanced).
        metadata: Extension data.
    """

    name: str
    description: str = ""
    prerequisites: list[str] = field(default_factory=list)
    category: str = ""
    tier: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_base(self) -> bool:
        """Whether this capability has no prerequisites."""
        return len(self.prerequisites) == 0


class CapabilityTree:
    """A directed acyclic graph of capabilities with prerequisite chains.

    The tree tracks which capabilities exist, what they require, and
    provides methods to determine unlock order and paths.

    Args:
        nodes: Initial set of capability nodes.
    """

    def __init__(self, nodes: list[CapabilityNode] | None = None) -> None:
        self._nodes: dict[str, CapabilityNode] = {}
        if nodes:
            for n in nodes:
                self.add(n)

    def add(self, node: CapabilityNode) -> None:
        """Register a capability node."""
        self._nodes[node.name] = node

    def remove(self, name: str) -> None:
        """Remove a capability node."""
        self._nodes.pop(name, None)

    def get(self, name: str) -> CapabilityNode | None:
        """Look up a capability by name."""
        return self._nodes.get(name)

    @property
    def nodes(self) -> list[CapabilityNode]:
        """All registered capability nodes."""
        return list(self._nodes.values())

    @property
    def size(self) -> int:
        """Number of registered capabilities."""
        return len(self._nodes)

    def prerequisites_of(self, name: str) -> list[str]:
        """Direct prerequisites for a capability."""
        node = self._nodes.get(name)
        return list(node.prerequisites) if node else []

    def all_prerequisites(self, name: str) -> list[str]:
        """Transitive (full) prerequisites for a capability, in order.

        Uses topological sort to return prerequisites such that each
        appears before any capability that requires it.
        """
        if name not in self._nodes:
            return []

        visited: set[str] = set()
        order: list[str] = []

        def dfs(cap: str) -> None:
            if cap in visited:
                return
            visited.add(cap)
            node = self._nodes.get(cap)
            if node:
                for pre in node.prerequisites:
                    dfs(pre)
            if cap != name:
                order.append(cap)

        dfs(name)
        return order

    def can_unlock(self, name: str, held: set[str]) -> tuple[bool, list[str]]:
        """Check if a capability can be unlocked given current capabilities.

        Returns:
            Tuple of (can_unlock, missing_prerequisites).
        """
        node = self._nodes.get(name)
        if node is None:
            return (False, [f"Unknown capability: '{name}'"])
        if name in held:
            return (False, [f"Already held: '{name}'"])

        missing = [p for p in node.prerequisites if p not in held]
        return (len(missing) == 0, missing)

    def unlock_order(self, desired: list[str], held: set[str] | None = None) -> list[str]:
        """Compute the order to acquire capabilities to reach the desired set.

        Args:
            desired: Capabilities the agent wants to acquire.
            held: Currently held capabilities.

        Returns:
            Ordered list of capabilities to acquire (not including already-held).
        """
        held = held or set()
        needed: set[str] = set()

        def collect(name: str) -> None:
            if name in held or name in needed:
                return
            needed.add(name)
            node = self._nodes.get(name)
            if node:
                for pre in node.prerequisites:
                    collect(pre)

        for cap in desired:
            collect(cap)

        # Topological sort of needed capabilities
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            node = self._nodes.get(name)
            if node:
                for pre in node.prerequisites:
                    if pre in needed:
                        visit(pre)
            order.append(name)

        for cap in needed:
            visit(cap)

        return order

    def available_to_unlock(self, held: set[str]) -> list[str]:
        """List capabilities that can be unlocked right now."""
        results = []
        for node in self._nodes.values():
            if node.name in held:
                continue
            if all(p in held for p in node.prerequisites):
                results.append(node.name)
        return results

    def by_category(self, category: str) -> list[CapabilityNode]:
        """Get all capabilities in a category."""
        return [n for n in self._nodes.values() if n.category == category]

    def by_tier(self, tier: int) -> list[CapabilityNode]:
        """Get all capabilities at a given tier."""
        return [n for n in self._nodes.values() if n.tier == tier]

    def validate(self) -> list[str]:
        """Check the tree for issues (missing prereqs, cycles).

        Returns:
            List of issues found (empty = valid).
        """
        issues: list[str] = []

        # Missing prerequisites
        for node in self._nodes.values():
            for pre in node.prerequisites:
                if pre not in self._nodes:
                    issues.append(
                        f"'{node.name}' requires unknown capability '{pre}'"
                    )

        # Cycle detection via DFS
        WHITE, GRAY, BLACK = 0, 1, 2
        colors: dict[str, int] = {name: WHITE for name in self._nodes}

        def has_cycle(name: str) -> bool:
            colors[name] = GRAY
            node = self._nodes[name]
            for pre in node.prerequisites:
                if pre not in colors:
                    continue
                if colors[pre] == GRAY:
                    return True
                if colors[pre] == WHITE and has_cycle(pre):
                    return True
            colors[name] = BLACK
            return False

        for name in list(self._nodes):
            if colors.get(name) == WHITE:
                if has_cycle(name):
                    issues.append(f"Cycle detected involving '{name}'")
                    break

        return issues

    def summary(self) -> dict[str, Any]:
        """A concise summary of the tree."""
        categories: dict[str, int] = {}
        tiers: dict[int, int] = {}
        for node in self._nodes.values():
            if node.category:
                categories[node.category] = categories.get(node.category, 0) + 1
            tiers[node.tier] = tiers.get(node.tier, 0) + 1
        return {
            "total_capabilities": self.size,
            "base_capabilities": sum(
                1 for n in self._nodes.values() if n.is_base()
            ),
            "categories": categories,
            "tiers": tiers,
        }
