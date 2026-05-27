"""Tests for EvolutionEngine."""

from become_ai.evolution import EvolutionEngine, EvolutionResult
from become_ai.identity import AgentIdentity
from become_ai.transformation import (
    Transformation,
    Trigger,
    TriggerType,
    Requirement,
    RequirementType,
)


def _make_transformations():
    t1 = Transformation(
        name="bootcamp",
        from_state="init",
        to_state="bootcamp",
        adds_traits={"generation": 0},
        adds_capabilities=["read_self"],
    )
    t2 = Transformation(
        name="first-feature",
        from_state="bootcamp",
        to_state="capable",
        adds_traits={"features": 1},
        adds_capabilities=["chat"],
        requirements=[
            Requirement(type=RequirementType.CAPABILITY, name="read_self")
        ],
    )
    t3 = Transformation(
        name="polish",
        from_state="capable",
        to_state="deployed",
        adds_traits={"quality": "high"},
    )
    return [t1, t2, t3]


def test_register_and_get():
    engine = EvolutionEngine()
    t = Transformation(name="t", from_state="*", to_state="done")
    engine.register(t)
    assert engine.get(t.id) is not None
    assert len(engine.transformations) == 1


def test_unregister():
    engine = EvolutionEngine()
    t = Transformation(name="t", from_state="*", to_state="done")
    engine.register(t)
    engine.unregister(t.id)
    assert engine.get(t.id) is None


def test_find_applicable():
    transforms = _make_transformations()
    engine = EvolutionEngine(transforms)
    identity = AgentIdentity(name="a", state="init")
    applicable = engine.find_applicable(identity)
    assert len(applicable) == 1
    assert applicable[0].name == "bootcamp"


def test_evolve_success():
    transforms = _make_transformations()
    engine = EvolutionEngine(transforms)
    identity = AgentIdentity(name="a", state="init")
    result = engine.evolve(identity, transforms[0])
    assert result.success
    assert result.identity.state == "bootcamp"
    assert "read_self" in result.identity.capabilities


def test_evolve_failure_returns_result():
    engine = EvolutionEngine()
    identity = AgentIdentity(name="a", state="wrong")
    t = Transformation(name="t", from_state="init", to_state="done")
    result = engine.evolve(identity, t)
    assert not result.success
    assert len(result.errors) > 0


def test_evolve_strict_raises():
    engine = EvolutionEngine(strict=True)
    identity = AgentIdentity(name="a", state="wrong")
    t = Transformation(name="t", from_state="init", to_state="done")
    try:
        engine.evolve(identity, t)
        assert False, "Should have raised"
    except ValueError:
        pass


def test_evolve_by_id():
    transforms = _make_transformations()
    engine = EvolutionEngine(transforms)
    identity = AgentIdentity(name="a", state="init")
    result = engine.evolve_by_id(identity, transforms[0].id)
    assert result.success

    result2 = engine.evolve_by_id(identity, "nonexistent")
    assert not result2.success


def test_evolve_all_applicable():
    transforms = _make_transformations()
    engine = EvolutionEngine(transforms)
    identity = AgentIdentity(name="a", state="init")
    results = engine.evolve_all_applicable(identity)
    # Should chain: init -> bootcamp -> capable -> deployed
    assert len(results) == 3
    assert all(r.success for r in results)
    assert results[-1].identity.state == "deployed"


def test_evolve_overnight():
    transforms = _make_transformations()
    engine = EvolutionEngine(transforms)
    identity = AgentIdentity(name="a", state="init")
    final, results = engine.evolve_overnight(identity, steps=10)
    assert len(results) == 3
    assert final.state == "deployed"


def test_find_triggered():
    t = Transformation(
        name="auto-go",
        from_state="init",
        to_state="ready",
        triggers=[Trigger(type=TriggerType.SELF_INITIATED, condition="auto")],
    )
    engine = EvolutionEngine([t])
    identity = AgentIdentity(name="a", state="init")
    triggered = engine.find_triggered(identity, {"self_initiated": True})
    assert len(triggered) == 1
    triggered2 = engine.find_triggered(identity, {})
    assert len(triggered2) == 0
