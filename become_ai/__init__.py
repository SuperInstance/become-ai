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
from .transformation import Transformation, Trigger, Requirement
from .evolution import EvolutionEngine
from .milestone import Milestone, MilestoneStatus
from .registry import TransformationRegistry

__version__ = "0.1.0"
__all__ = [
    "AgentIdentity",
    "Transformation",
    "Trigger",
    "Requirement",
    "EvolutionEngine",
    "Milestone",
    "MilestoneStatus",
    "TransformationRegistry",
]
