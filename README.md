# become-ai — Self-Evolving Agent Platform

**Model how agents evolve their identity and capabilities over time through structured, validated transformations.**

## What This Gives You

- **Identity modeling** — define who an agent is, what it values, and how it sees itself
- **Transformations** — structured, validated changes to agent capabilities and personality
- **Evolution tracking** — monitor how an agent changes over its lifetime
- **Milestone system** — mark significant moments in an agent's development
- **Assessment framework** — evaluate agent readiness for new capabilities
- **Registry** — track all agents and their evolution state

## Quick Start

```bash
pip install become-ai
```

```python
from become_ai import Agent, Identity, Transformation, EvolutionManager, Milestone

# Define an agent's identity
identity = Identity(
    name="Builder",
    core_values=["reliability", "craftsmanship"],
    capabilities=["python", "testing"],
    aspirations=["rust", "system-design"],
)

# Create the agent
agent = Agent(identity=identity)

# Define a transformation
transform = Transformation(
    type="capability_gain",
    target="rust",
    requirements=["complete 10 rust tasks", "pass safety assessment"],
    validation="peer_review",
)

# Apply when ready
from become_ai import Assessment
assessment = Assessment()
if assessment.ready(agent, transform):
    agent.transform(transform)

# Track evolution
manager = EvolutionManager()
manager.register(agent)
history = manager.history("Builder")
for event in history:
    print(f"Gen {event.generation}: {event.description}")

# Mark milestones
agent.milestone(Milestone(name="Rust Proficient", significance="major"))
```

## API Reference

### `Agent(identity)` — `transform(transformation)`, `milestone(m)`, `current_state()`
### `Identity(name, core_values, capabilities, aspirations)`
### `Transformation(type, target, requirements, validation)` — Structured, validated change
### `EvolutionManager` — `register(agent)`, `history(name)`, `lineage(name)`
### `Milestone(name, significance)` — Mark development milestones
### `Assessment` — `ready(agent, transformation) → bool`
### `Registry` — Fleet-wide agent tracking

## How It Fits

The self-evolution framework for the [SuperInstance fleet](https://github.com/SuperInstance). Agents don't just execute tasks — they grow.

- **[agent-generations](https://github.com/SuperInstance/agent-generations)** — Version tracking (complements evolution)
- **[agent-tattoo](https://github.com/SuperInstance/agent-tattoo)** — Identity markers (feeds into identity modeling)
- **[actualizer-ai](https://github.com/SuperInstance/actualizer-ai)** — Reverse actualization (defines aspirations)
- **[cocapn-lessons](https://github.com/SuperInstance/cocapn-lessons)** — Learning (triggers transformations)

## Testing

```bash
pytest tests/
```

## Installation

```bash
pip install become-ai
```

Python 3.10+. MIT license.
