"""Tests for AgentIdentity."""

from become_ai.identity import AgentIdentity
from become_ai.transformation import TransformationRecord


def test_create_identity():
    identity = AgentIdentity(name="test-agent")
    assert identity.name == "test-agent"
    assert identity.state == "init"
    assert identity.traits == {}
    assert identity.capabilities == []
    assert identity.locked_traits == set()


def test_evolve_state():
    identity = AgentIdentity(name="agent")
    evolved = identity.evolve(state="bootcamp")
    assert evolved.state == "bootcamp"
    assert identity.state == "init"  # original unchanged


def test_set_trait():
    identity = AgentIdentity(name="agent", traits={"color": "blue"})
    evolved = identity.set_trait("color", "red")
    assert evolved.traits["color"] == "red"
    assert identity.traits["color"] == "blue"


def test_set_trait_locked_raises():
    identity = AgentIdentity(
        name="agent", traits={"core": "value"}, locked_traits={"core"}
    )
    try:
        identity.set_trait("core", "new")
        assert False, "Should have raised"
    except ValueError as e:
        assert "locked" in str(e).lower()


def test_lock_unlock_trait():
    identity = AgentIdentity(name="agent", traits={"x": 1})
    locked = identity.lock_trait("x")
    assert "x" in locked.locked_traits
    unlocked = locked.unlock_trait("x")
    assert "x" not in unlocked.locked_traits


def test_add_remove_capability():
    identity = AgentIdentity(name="agent")
    with_cap = identity.add_capability("chat")
    assert "chat" in with_cap.capabilities
    without = with_cap.remove_capability("chat")
    assert "chat" not in without.capabilities


def test_achieve_milestone():
    identity = AgentIdentity(name="agent")
    evolved = identity.achieve_milestone("first-feature")
    assert "first-feature" in evolved.achieved_milestones
    # Duplicate is a no-op
    evolved2 = evolved.achieve_milestone("first-feature")
    assert evolved2.achieved_milestones.count("first-feature") == 1


def test_transformation_count():
    identity = AgentIdentity(name="agent")
    assert identity.transformation_count() == 0
    record = TransformationRecord(
        transformation_id="t1",
        transformation_name="test",
        from_state="init",
        to_state="ready",
        timestamp=identity.created_at,
    )
    evolved = identity.evolve(history=[record])
    assert evolved.transformation_count() == 1


def test_summary():
    identity = AgentIdentity(
        name="agent", state="running", capabilities=["chat", "search"]
    )
    s = identity.summary()
    assert s["name"] == "agent"
    assert s["state"] == "running"
    assert "chat" in s["capabilities"]


def test_scores():
    identity = AgentIdentity(name="agent")
    evolved = identity.set_score("quality", 8.5)
    assert evolved.scores["quality"] == 8.5


def test_custom_checks():
    identity = AgentIdentity(name="agent", custom_checks={"verified": True})
    assert identity.custom_checks["verified"] is True
