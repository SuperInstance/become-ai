"""Milestone — tracks progress toward a transformation goal.

Milestones represent checkpoints an agent must reach as part of
its evolution. They can be used as requirements for transformations
and as a way to measure overall progress.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MilestoneStatus(Enum):
    """Lifecycle states for a milestone."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Milestone:
    """A checkpoint in an agent's evolution.

    Attributes:
        name: Unique identifier for this milestone.
        description: Human-readable description.
        criteria: Description of what "done" looks like.
        status: Current status.
        score: Optional numeric progress (0.0–1.0 or raw value).
        prerequisites: Names of milestones that must be achieved first.
        rewards: Traits or capabilities granted upon achievement.
        created_at: When this milestone was defined.
        achieved_at: When this milestone was achieved (if ever).
        metadata: Extension data.
    """

    name: str
    description: str = ""
    criteria: str = ""
    status: MilestoneStatus = MilestoneStatus.PENDING
    score: float = 0.0
    prerequisites: list[str] = field(default_factory=list)
    rewards: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    achieved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> Milestone:
        """Mark this milestone as in progress."""
        if self.status not in (MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS):
            raise ValueError(
                f"Cannot start milestone '{self.name}': status is {self.status.value}"
            )
        return Milestone(
            name=self.name,
            description=self.description,
            criteria=self.criteria,
            status=MilestoneStatus.IN_PROGRESS,
            score=self.score,
            prerequisites=self.prerequisites,
            rewards=self.rewards,
            created_at=self.created_at,
            achieved_at=self.achieved_at,
            metadata=self.metadata,
        )

    def achieve(self, score: float | None = None) -> Milestone:
        """Mark this milestone as achieved."""
        if self.status == MilestoneStatus.ACHIEVED:
            return self
        return Milestone(
            name=self.name,
            description=self.description,
            criteria=self.criteria,
            status=MilestoneStatus.ACHIEVED,
            score=score if score is not None else self.score,
            prerequisites=self.prerequisites,
            rewards=self.rewards,
            created_at=self.created_at,
            achieved_at=datetime.now(),
            metadata=self.metadata,
        )

    def fail(self, reason: str = "") -> Milestone:
        """Mark this milestone as failed."""
        return Milestone(
            name=self.name,
            description=self.description,
            criteria=self.criteria,
            status=MilestoneStatus.FAILED,
            score=self.score,
            prerequisites=self.prerequisites,
            rewards=self.rewards,
            created_at=self.created_at,
            achieved_at=self.achieved_at,
            metadata={**self.metadata, "failure_reason": reason},
        )

    def skip(self, reason: str = "") -> Milestone:
        """Skip this milestone."""
        return Milestone(
            name=self.name,
            description=self.description,
            criteria=self.criteria,
            status=MilestoneStatus.SKIPPED,
            score=self.score,
            prerequisites=self.prerequisites,
            rewards=self.rewards,
            created_at=self.created_at,
            achieved_at=self.achieved_at,
            metadata={**self.metadata, "skip_reason": reason},
        )

    def is_complete(self) -> bool:
        """Whether this milestone is in a terminal state."""
        return self.status in (
            MilestoneStatus.ACHIEVED,
            MilestoneStatus.FAILED,
            MilestoneStatus.SKIPPED,
        )

    def progress(self) -> float:
        """Return a 0.0–1.0 progress indicator."""
        if self.status == MilestoneStatus.ACHIEVED:
            return 1.0
        if self.status in (MilestoneStatus.FAILED, MilestoneStatus.SKIPPED):
            return 0.0
        return min(max(self.score, 0.0), 1.0)

    def can_start(self, achieved_milestones: list[str]) -> bool:
        """Check if prerequisites are met to begin work on this milestone."""
        if self.status != MilestoneStatus.PENDING:
            return False
        return all(p in achieved_milestones for p in self.prerequisites)

    def summary(self) -> dict[str, Any]:
        """A concise summary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress(),
            "description": self.description,
        }
