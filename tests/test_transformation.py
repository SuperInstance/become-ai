"""Tests for Transformation, Trigger, and Requirement."""

from become_ai.transformation import (
    Transformation,
    Trigger,
    TriggerType,
    Requirement,
    RequirementType,
)
from become_ai.identity import AgentIdentity


class TestTrigger:
    def test_manual_trigger_matches(self):
        t = Trigger(type=TriggerType.MANUAL, condition="go")
        assert t.matches({"manual_trigger": "go"})
        assert not t.matches({"manual_trigger": "stop"})

    def test_milestone_trigger(self):
        t = Trigger(type=TriggerType.MILESTONE, condition="boot-camp")
        assert t.matches({"achieved_milestones": ["boot-camp", "other"]})
        assert not t.matches({"achieved_milestones": []})

    def test_score_threshold_trigger(self):
        t = Trigger(type=TriggerType.SCORE_THRESHOLD, condition="7")
        assert t.matches({"score": 8})
        assert t.matches({"score": 7})
        assert not t.matches({"score": 6})

    def test_time_based_trigger(self):
        t = Trigger(type=TriggerType.TIME_BASED, condition="any")
        assert t.matches({"time_elapsed": True})
        assert not t.matches({"time_elapsed": False})

    def test_external_event_trigger(self):
        t = Trigger(type=TriggerType.EXTERNAL_EVENT, condition="webhook")
        assert t.matches({"event": "webhook"})
        assert not t.matches({"event": "other"})

    def test_self_initiated_trigger(self):
        t = Trigger(type=TriggerType.SELF_INITIATED, condition="auto")
        assert t.matches({"self_initiated": True})
        assert not t.matches({})


class TestRequirement:
    def test_trait_requirement_satisfied(self):
        r = Requirement(type=RequirementType.TRAIT, name="role", value="helper")
        identity = AgentIdentity(name="a", traits={"role": "helper"})
        assert r.is_satisfied(identity)

    def test_trait_requirement_unsatisfied(self):
        r = Requirement(type=RequirementType.TRAIT, name="role", value="helper")
        identity = AgentIdentity(name="a", traits={"role": "guard"})
        assert not r.is_satisfied(identity)

    def test_trait_requirement_missing(self):
        r = Requirement(type=RequirementType.TRAIT, name="role", value="helper")
        identity = AgentIdentity(name="a")
        assert not r.is_satisfied(identity)

    def test_capability_requirement(self):
        r = Requirement(type=RequirementType.CAPABILITY, name="chat")
        assert r.is_satisfied(AgentIdentity(name="a", capabilities=["chat"]))
        assert not r.is_satisfied(AgentIdentity(name="a"))

    def test_score_requirement(self):
        r = Requirement(type=RequirementType.SCORE, name="quality", value=7.0)
        assert r.is_satisfied(
            AgentIdentity(name="a", scores={"quality": 8.0})
        )
        assert not r.is_satisfied(
            AgentIdentity(name="a", scores={"quality": 5.0})
        )

    def test_milestone_requirement(self):
        r = Requirement(type=RequirementType.MILESTONE, name="bootcamp")
        assert r.is_satisfied(
            AgentIdentity(name="a", achieved_milestones=["bootcamp"])
        )
        assert not r.is_satisfied(AgentIdentity(name="a"))

    def test_custom_requirement(self):
        r = Requirement(type=RequirementType.CUSTOM, name="verified")
        assert r.is_satisfied(
            AgentIdentity(name="a", custom_checks={"verified": True})
        )
        assert not r.is_satisfied(
            AgentIdentity(name="a", custom_checks={"verified": False})
        )


class TestTransformation:
    def test_can_apply_correct_state(self):
        t = Transformation(name="go", from_state="init", to_state="ready")
        identity = AgentIdentity(name="a", state="init")
        can, reasons = t.can_apply(identity)
        assert can
        assert reasons == []

    def test_can_apply_wrong_state(self):
        t = Transformation(name="go", from_state="init", to_state="ready")
        identity = AgentIdentity(name="a", state="running")
        can, reasons = t.can_apply(identity)
        assert not can
        assert any("state" in r.lower() for r in reasons)

    def test_can_apply_wildcard_state(self):
        t = Transformation(name="go", from_state="*", to_state="ready")
        identity = AgentIdentity(name="a", state="anything")
        can, _ = t.can_apply(identity)
        assert can

    def test_apply_transformation(self):
        t = Transformation(
            name="evolve",
            from_state="init",
            to_state="bootcamp",
            adds_traits={"level": 1},
            adds_capabilities=["chat"],
        )
        identity = AgentIdentity(name="a", state="init")
        evolved = t.apply(identity)
        assert evolved.state == "bootcamp"
        assert evolved.traits["level"] == 1
        assert "chat" in evolved.capabilities
        assert evolved.transformation_count() == 1
        assert identity.state == "init"  # original unchanged

    def test_apply_with_requirements(self):
        t = Transformation(
            name="advanced",
            from_state="init",
            to_state="pro",
            requirements=[
                Requirement(type=RequirementType.CAPABILITY, name="chat")
            ],
        )
        identity = AgentIdentity(name="a", state="init", capabilities=["chat"])
        can, _ = t.can_apply(identity)
        assert can

        identity2 = AgentIdentity(name="a", state="init")
        can2, reasons2 = t.can_apply(identity2)
        assert not can2

    def test_apply_locked_trait_protection(self):
        t = Transformation(
            name="reset",
            from_state="*",
            to_state="clean",
            removes_traits=["core_id"],
        )
        identity = AgentIdentity(
            name="a", traits={"core_id": "abc"}, locked_traits={"core_id"}
        )
        can, reasons = t.can_apply(identity)
        assert not can
        assert any("locked" in r.lower() for r in reasons)

    def test_apply_raises_on_failure(self):
        t = Transformation(name="bad", from_state="x", to_state="y")
        identity = AgentIdentity(name="a", state="z")
        try:
            t.apply(identity)
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_removes_capabilities(self):
        t = Transformation(
            name="slim",
            from_state="*",
            to_state="lite",
            removes_capabilities=["experimental"],
        )
        identity = AgentIdentity(
            name="a", capabilities=["chat", "experimental"]
        )
        evolved = t.apply(identity)
        assert "experimental" not in evolved.capabilities
        assert "chat" in evolved.capabilities
