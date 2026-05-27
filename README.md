# Become AI — The Transformation Protocol

A Python library for modeling how agents evolve their identity and capabilities over time through structured, validated transformations.

Part of the [Superinstance](https://github.com/SuperInstance/become-ai) project.

## Installation

```bash
pip install become-ai
```

Or from source:

```bash
git clone https://github.com/SuperInstance/become-ai.git
cd become-ai
pip install -e .
```

## Quick Start

```python
from become_ai import (
    AgentIdentity,
    Transformation,
    Trigger,
    TriggerType,
    Requirement,
    RequirementType,
    EvolutionEngine,
    Milestone,
    TransformationRegistry,
)

# Create an agent identity
agent = AgentIdentity(name="my-agent", state="init")

# Define a transformation
bootcamp = Transformation(
    name="bootcamp",
    from_state="init",
    to_state="bootcamp",
    adds_traits={"generation": 0},
    adds_capabilities=["read_self", "mutate"],
    description="Agent enters bootcamp and gains self-awareness",
)

# Use the evolution engine
engine = EvolutionEngine(transformations=[bootcamp])
result = engine.evolve(agent, bootcamp)

print(result.identity.state)        # "bootcamp"
print(result.identity.capabilities) # ["mutate", "read_self"]
print(result.success)               # True
```

## Chaining Transformations

```python
# Define a full evolution chain
transforms = [
    Transformation(
        name="bootcamp",
        from_state="init",
        to_state="bootcamp",
        adds_capabilities=["read_self"],
    ),
    Transformation(
        name="first-feature",
        from_state="bootcamp",
        to_state="capable",
        adds_capabilities=["chat"],
        requirements=[
            Requirement(type=RequirementType.CAPABILITY, name="read_self")
        ],
    ),
    Transformation(
        name="deploy",
        from_state="capable",
        to_state="deployed",
        adds_traits={"quality": "production"},
    ),
]

engine = EvolutionEngine(transforms)
agent = AgentIdentity(name="my-agent", state="init")

# Apply all applicable transformations in sequence
results = engine.evolve_all_applicable(agent)
print(results[-1].identity.state)  # "deployed"
```

## Overnight Mode

```python
# Run multiple evolution steps unattended
final, results = engine.evolve_overnight(agent, steps=10)
print(f"Applied {len(results)} transformations")
print(f"Final state: {final.state}")
```

## Triggers

```python
# Transformations can be triggered by events
auto_evolve = Transformation(
    name="auto-level-up",
    from_state="bootcamp",
    to_state="capable",
    triggers=[
        Trigger(type=TriggerType.SCORE_THRESHOLD, condition="8"),
        Trigger(type=TriggerType.MANUAL, condition="force-level-up"),
    ],
)

engine.register(auto_evolve)

# Find transformations triggered by a score context
triggered = engine.find_triggered(agent, {"score": 9})
```

## Locked Traits

```python
# Protect core identity traits
agent = AgentIdentity(
    name="agent",
    traits={"core_id": "abc-123", "personality": "curious"},
    locked_traits={"core_id"},  # cannot be modified or removed
)

# This works
agent = agent.set_trait("personality", "bold")

# This raises ValueError
try:
    agent.set_trait("core_id", "new-id")
except ValueError as e:
    print(e)  # "Cannot modify locked trait: 'core_id'"
```

## Milestones

```python
m1 = Milestone(name="basics", description="Learn the fundamentals")
m2 = Milestone(
    name="advanced",
    description="Master advanced topics",
    prerequisites=["basics"],
)

# Start and achieve milestones
m1 = m1.start()
m1 = m1.achieve(score=1.0)

# Check if m2 can start
assert m2.can_start(["basics"])  # True
```

## Transformation Registry

```python
registry = TransformationRegistry()

# Register with metadata
registry.add_transformation(
    bootcamp_transform,
    tags=["core", "bootcamp"],
    category="initialization",
    priority=1,
)

# Search by various criteria
registry.find_by_tag("bootcamp")
registry.find_by_category("initialization")
registry.find_by_state("init", "bootcamp")

# Find a path between states
path = registry.find_path("init", "deployed")
print(f"Path: {[t.name for t in path]}")
```

## Core Concepts

### Identity
An agent's identity is the sum of its state, traits, capabilities, locked properties, and transformation history. Identities are immutable — use `evolve()` to create new versions.

### Transformation
A state transition with triggers and requirements. Transformations validate that an agent is in the right state and meets all prerequisites before applying.

### Evolution Engine
Orchestrates transformations: discovers applicable ones, validates them, applies them in sequence, and supports overnight batch evolution.

### Milestone
A checkpoint an agent must reach. Milestones track progress, have prerequisites, and can be used as requirements for transformations.

### Registry
A catalog of available transformations with search, filtering, and path-finding between states.

## Architecture

```
become_ai/
├── __init__.py          # Public API
├── identity.py          # AgentIdentity — who an agent is
├── transformation.py    # Transformation, Trigger, Requirement
├── evolution.py         # EvolutionEngine — orchestrates change
├── milestone.py         # Milestone tracking
└── registry.py          # TransformationRegistry — catalog & search
```

Zero external dependencies beyond Python 3.10+ and pytest for testing.

## License

MIT — use it, break it, fork it.

---

*Superinstance & Lucineer (DiGennaro et al.)*
