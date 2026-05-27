"""Become AI — The Transformation Protocol.

A library for modeling how agents evolve their identity and capabilities
over time through structured, validated transformations.

Core concepts:
- AgentIdentity: who an agent is (mutable properties, locked traits, history)
- Transformation: a state transition with triggers and requirements
- EvolutionEngine: orchestrates transformation rules and validation
- Milestone: tracks progress toward a transformation goal
- TransformationRegistry: catalog of available transformations
"""

from .identity import AgentIdentity
from .transformation import (
    Transformation,
    TransformationRecord,
    Trigger,
    TriggerType,
    Requirement,
    RequirementType,
)
from .evolution import EvolutionEngine, EvolutionResult
from .milestone import Milestone, MilestoneStatus
from .registry import TransformationRegistry, RegistryEntry
from .protocol import TransformProtocol, StateRule, TransitionRule
from .capability import CapabilityTree, CapabilityNode
from .assessment import AssessmentEngine, ReadinessReport, ProgressReport

__version__ = "0.2.0"
__all__ = [
    "AgentIdentity",
    "Transformation",
    "TransformationRecord",
    "Trigger",
    "TriggerType",
    "Requirement",
    "RequirementType",
    "EvolutionEngine",
    "EvolutionResult",
    "Milestone",
    "MilestoneStatus",
    "TransformationRegistry",
    "RegistryEntry",
    "TransformProtocol",
    "StateRule",
    "TransitionRule",
    "CapabilityTree",
    "CapabilityNode",
    "AssessmentEngine",
    "ReadinessReport",
    "ProgressReport",
]
