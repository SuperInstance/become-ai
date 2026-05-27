"""AssessmentEngine — evaluates readiness and progress for transformations.

The assessment engine measures how ready an agent is for transformation,
tracks progress toward goals, and generates improvement plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability import CapabilityTree
from .identity import AgentIdentity
from .milestone import Milestone, MilestoneStatus
from .protocol import TransformProtocol
from .transformation import Transformation


@dataclass
class ReadinessReport:
    """Assessment of an agent's readiness for a specific transformation.

    Attributes:
        transformation_name: The transformation assessed.
        ready: Whether the agent can proceed.
        score: 0.0–1.0 readiness score.
        met_requirements: Requirements that are satisfied.
        unmet_requirements: Requirements that are not satisfied.
        protocol_violations: Protocol-level issues.
        recommendations: Suggested actions to improve readiness.
    """

    transformation_name: str
    ready: bool
    score: float
    met_requirements: list[str]
    unmet_requirements: list[str]
    protocol_violations: list[str]
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ProgressReport:
    """Overall progress assessment for an agent.

    Attributes:
        identity_name: The agent's name.
        current_state: Current state.
        transformations_applied: Number of transformations applied.
        capabilities_held: Number of capabilities.
        milestones_achieved: Number of milestones.
        milestone_progress: Per-milestone progress.
        overall_score: 0.0–1.0 aggregate score.
        next_steps: Recommended transformations or actions.
    """

    identity_name: str
    current_state: str
    transformations_applied: int
    capabilities_held: int
    milestones_achieved: int
    milestone_progress: list[dict[str, Any]]
    overall_score: float
    next_steps: list[str] = field(default_factory=list)


class AssessmentEngine:
    """Evaluates agent readiness, progress, and generates improvement plans.

    Args:
        protocol: Optional protocol for validation.
        capability_tree: Optional capability tree for prerequisite analysis.
    """

    def __init__(
        self,
        protocol: TransformProtocol | None = None,
        capability_tree: CapabilityTree | None = None,
    ) -> None:
        self.protocol = protocol
        self.capability_tree = capability_tree

    def assess_readiness(
        self,
        identity: AgentIdentity,
        transformation: Transformation,
    ) -> ReadinessReport:
        """Evaluate how ready an agent is for a specific transformation.

        Checks transformation requirements and protocol constraints,
        then generates a readiness score and recommendations.
        """
        can_apply, reasons = transformation.can_apply(identity)
        met: list[str] = []
        unmet: list[str] = []

        # Classify each requirement
        from .transformation import Requirement
        for req in transformation.requirements:
            desc = req.description or f"{req.type.value}:{req.name}"
            if req.is_satisfied(identity):
                met.append(desc)
            else:
                unmet.append(desc)

        # Check protocol
        protocol_violations: list[str] = []
        if self.protocol:
            valid, violations = self.protocol.validate(identity, transformation)
            protocol_violations = violations

        # Compute score
        total = len(transformation.requirements)
        if total == 0:
            req_score = 1.0
        else:
            req_score = len(met) / total

        protocol_penalty = len(protocol_violations) * 0.2
        score = max(0.0, min(1.0, req_score - protocol_penalty))

        ready = can_apply and len(protocol_violations) == 0

        # Generate recommendations
        recommendations: list[str] = []
        for desc in unmet:
            recommendations.append(f"Fulfill requirement: {desc}")
        for v in protocol_violations:
            recommendations.append(f"Resolve protocol issue: {v}")

        # Capability tree suggestions
        if self.capability_tree:
            for cap in transformation.adds_capabilities:
                missing_info = self.capability_tree.all_prerequisites(cap)
                for pre in missing_info:
                    if pre not in identity.capabilities:
                        recommendations.append(
                            f"Acquire prerequisite capability: '{pre}'"
                        )

        return ReadinessReport(
            transformation_name=transformation.name,
            ready=ready,
            score=score,
            met_requirements=met,
            unmet_requirements=unmet,
            protocol_violations=protocol_violations,
            recommendations=recommendations,
        )

    def assess_progress(
        self,
        identity: AgentIdentity,
        milestones: list[Milestone] | None = None,
        transformations: list[Transformation] | None = None,
    ) -> ProgressReport:
        """Generate an overall progress report for an agent.

        Args:
            identity: The agent to assess.
            milestones: Known milestones (for progress tracking).
            transformations: Available transformations (for next-step suggestions).
        """
        milestones = milestones or []
        transformations = transformations or []

        # Milestone progress
        milestone_progress: list[dict[str, Any]] = []
        achieved_count = 0
        for m in milestones:
            if m.status == MilestoneStatus.ACHIEVED:
                achieved_count += 1
            milestone_progress.append(m.summary())

        # Overall score: weighted combination
        cap_score = min(len(identity.capabilities) / 10.0, 1.0)
        milestone_score = (
            achieved_count / len(milestones) if milestones else 1.0
        )
        history_score = min(identity.transformation_count() / 5.0, 1.0)
        overall = (
            cap_score * 0.3 + milestone_score * 0.4 + history_score * 0.3
        )

        # Next steps
        next_steps: list[str] = []
        for t in transformations:
            can, _ = t.can_apply(identity)
            if can:
                next_steps.append(f"Apply transformation: '{t.name}'")

        # Suggest available capabilities to unlock
        if self.capability_tree:
            available = self.capability_tree.available_to_unlock(
                set(identity.capabilities)
            )
            for cap in available[:3]:
                next_steps.append(f"Unlock capability: '{cap}'")

        return ProgressReport(
            identity_name=identity.name,
            current_state=identity.state,
            transformations_applied=identity.transformation_count(),
            capabilities_held=len(identity.capabilities),
            milestones_achieved=achieved_count,
            milestone_progress=milestone_progress,
            overall_score=round(overall, 3),
            next_steps=next_steps,
        )

    def improvement_plan(
        self,
        identity: AgentIdentity,
        target_transformation: Transformation,
    ) -> list[str]:
        """Generate a step-by-step plan to become ready for a transformation.

        Returns an ordered list of actions (as human-readable strings)
        to move from the current state to readiness.
        """
        report = self.assess_readiness(identity, target_transformation)
        if report.ready:
            return [f"Ready to apply '{target_transformation.name}'"]

        plan: list[str] = []
        plan.append(f"Goal: Apply transformation '{target_transformation.name}'")

        # State mismatch
        if target_transformation.from_state != "*":
            if identity.state != target_transformation.from_state:
                plan.append(
                    f"1. Move from state '{identity.state}' to "
                    f"'{target_transformation.from_state}'"
                )

        # Unmet requirements
        step = 2
        for unmet in report.unmet_requirements:
            plan.append(f"{step}. Fulfill: {unmet}")
            step += 1

        # Protocol violations
        for v in report.protocol_violations:
            plan.append(f"{step}. Resolve: {v}")
            step += 1

        return plan
