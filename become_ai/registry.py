"""TransformationRegistry — catalog of available transformations.

A registry manages named transformations, supports lookup by name or
state transition, and tracks prerequisites between transformations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .identity import AgentIdentity
from .transformation import Transformation


@dataclass
class RegistryEntry:
    """A transformation plus registry metadata.

    Attributes:
        transformation: The registered transformation.
        tags: Free-form tags for filtering.
        category: Optional grouping (e.g. "bootcamp", "equipment", "skill").
        priority: Sort priority (lower = higher priority).
        deprecated: Whether this transformation is deprecated.
    """

    transformation: Transformation
    tags: list[str] = field(default_factory=list)
    category: str = ""
    priority: int = 0
    deprecated: bool = False


class TransformationRegistry:
    """Catalog of available transformations with search and filtering.

    The registry is the "archetype catalog" from the bootcamp architecture —
    it knows what transformations exist, what they require, and how they
    relate to each other.

    Args:
        entries: Initial set of registry entries.
    """

    def __init__(self, entries: list[RegistryEntry] | None = None) -> None:
        self._entries: dict[str, RegistryEntry] = {}
        if entries:
            for e in entries:
                self.add(e)

    def add(self, entry: RegistryEntry) -> None:
        """Register a transformation entry."""
        tid = entry.transformation.id
        self._entries[tid] = entry

    def add_transformation(
        self,
        transformation: Transformation,
        tags: list[str] | None = None,
        category: str = "",
        priority: int = 0,
    ) -> None:
        """Convenience: register a bare transformation with optional metadata."""
        self.add(RegistryEntry(
            transformation=transformation,
            tags=tags or [],
            category=category,
            priority=priority,
        ))

    def remove(self, transformation_id: str) -> None:
        """Remove a transformation by ID."""
        self._entries.pop(transformation_id, None)

    def get(self, transformation_id: str) -> RegistryEntry | None:
        """Look up an entry by transformation ID."""
        return self._entries.get(transformation_id)

    def get_by_name(self, name: str) -> list[RegistryEntry]:
        """Find all entries whose transformation name matches."""
        return [
            e for e in self._entries.values()
            if e.transformation.name == name
        ]

    def find_by_state(self, from_state: str, to_state: str) -> list[RegistryEntry]:
        """Find transformations matching a specific state transition."""
        results = []
        for e in self._entries.values():
            t = e.transformation
            if t.from_state in ("*", from_state) and t.to_state == to_state:
                results.append(e)
        return sorted(results, key=lambda e: e.priority)

    def find_by_tag(self, tag: str) -> list[RegistryEntry]:
        """Find all entries with a given tag."""
        return [
            e for e in self._entries.values()
            if tag in e.tags
        ]

    def find_by_category(self, category: str) -> list[RegistryEntry]:
        """Find all entries in a given category."""
        return [
            e for e in self._entries.values()
            if e.category == category
        ]

    def find_applicable(
        self, identity: AgentIdentity
    ) -> list[RegistryEntry]:
        """Find all non-deprecated entries whose transformations can apply."""
        results = []
        for e in self._entries.values():
            if e.deprecated:
                continue
            can, _ = e.transformation.can_apply(identity)
            if can:
                results.append(e)
        return sorted(results, key=lambda e: e.priority)

    def find_path(
        self,
        from_state: str,
        to_state: str,
    ) -> list[Transformation]:
        """BFS to find a shortest path of transformations between states.

        Returns an ordered list of transformations that, applied sequentially,
        move an agent from ``from_state`` to ``to_state``. Returns an empty
        list if no path exists.
        """
        if from_state == to_state:
            return []

        # Build adjacency: state -> list of (target_state, transformation)
        adj: dict[str, list[tuple[str, Transformation]]] = {}
        for e in self._entries.values():
            t = e.transformation
            src = t.from_state if t.from_state != "*" else None
            if src is None:
                # Wildcard — connects from any state
                for state in adj:
                    adj[state].append((t.to_state, t))
                # Also add for from_state and to_state as potential sources
                adj.setdefault(from_state, []).append((t.to_state, t))
                adj.setdefault(t.to_state, []).append((t.to_state, t))
            else:
                adj.setdefault(src, []).append((t.to_state, t))

        # BFS
        from collections import deque

        visited: set[str] = {from_state}
        queue: deque[tuple[str, list[Transformation]]] = deque()
        queue.append((from_state, []))

        while queue:
            current, path = queue.popleft()
            for next_state, t in adj.get(current, []):
                if next_state == to_state:
                    return path + [t]
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [t]))

        return []

    @property
    def all_entries(self) -> list[RegistryEntry]:
        """All registered entries."""
        return list(self._entries.values())

    @property
    def size(self) -> int:
        """Number of registered transformations."""
        return len(self._entries)

    def summary(self) -> dict[str, Any]:
        """A concise summary of the registry."""
        categories: dict[str, int] = {}
        tags: dict[str, int] = {}
        for e in self._entries.values():
            if e.category:
                categories[e.category] = categories.get(e.category, 0) + 1
            for tag in e.tags:
                tags[tag] = tags.get(tag, 0) + 1
        return {
            "total_transformations": self.size,
            "categories": categories,
            "tags": tags,
        }
