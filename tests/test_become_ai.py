"""Comprehensive test suite for become_ai."""

import pytest
from datetime import datetime

from become_ai import (
    AgentIdentity,
    Transformation,
    TransformationRecord,
    Trigger,
    TriggerType,
    Requirement,
    RequirementType,
    EvolutionEngine,
    EvolutionResult,
    Milestone,
    MilestoneStatus,
    TransformationRegistry,
    RegistryEntry,
    TransformProtocol,
    StateRule,
    TransitionRule,
    CapabilityTree,
    CapabilityNode,
    AssessmentEngine,
    ReadinessReport,
    ProgressReport,
)


# ─── Identity Tests ───────────────────────────────────────────


class TestAgentIdentity:
    def test_create_default(self):
        agent = AgentIdentity(name="test")
        assert agent.name == "test"
        assert agent.state == "init"
        assert agent.traits == {}
        assert agent.capabilities == []
        assert agent.locked_traits == set()
        assert agent.history == []

    def test_evolve_state(self):
        agent = AgentIdentity(name="a")
        evolved = agent.evolve(state="bootcamp")
        assert evolved.state == "bootcamp"
        assert agent.state == "init"  # original unchanged

    def test_evolve_traits(self):
        agent = AgentIdentity(name="a", traits={"x": 1})
        evolved = agent.evolve(traits={"x": 2, "y": 3})
        assert evolved.traits == {"x": 2, "y": 3}

    def test_add_capability(self):
        agent = AgentIdentity(name="a")
        evolved = agent.add_capability("read_self")
        assert "read_self" in evolved.capabilities

    def test_add_capability_dedup(self):
        agent = AgentIdentity(name="a", capabilities=["read"])
        evolved = agent.add_capability("read")
        assert evolved.capabilities.count("read") == 1

    def test_remove_capability(self):
        agent = AgentIdentity(name="a", capabilities=["read", "write"])
        evolved = agent.remove_capability("read")
        assert "read" not in evolved.capabilities
        assert "write" in evolved.capabilities

    def test_set_trait(self):
        agent = AgentIdentity(name="a")
        evolved = agent.set_trait("mood", "curious")
        assert evolved.traits["mood"] == "curious"

    def test_set_trait_locked_raises(self):
        agent = AgentIdentity(name="a", locked_traits={"core_id"})
        with pytest.raises(ValueError, match="Cannot modify locked trait"):
            agent.set_trait("core_id", "new")

    def test_lock_unlock_trait(self):
        agent = AgentIdentity(name="a", traits={"x": 1})
        locked = agent.lock_trait("x")
        assert "x" in locked.locked_traits
        unlocked = locked.unlock_trait("x")
        assert "x" not in unlocked.locked_traits

    def test_set_score(self):
        agent = AgentIdentity(name="a")
        evolved = agent.set_score("quality", 0.9)
        assert evolved.scores["quality"] == 0.9

    def test_achieve_milestone(self):
        agent = AgentIdentity(name="a")
        evolved = agent.achieve_milestone("basics")
        assert "basics" in evolved.achieved_milestones
        # idempotent
        evolved2 = evolved.achieve_milestone("basics")
        assert evolved2.achieved_milestones.count("basics") == 1

    def test_transformation_count(self):
        agent = AgentIdentity(name="a")
        assert agent.transformation_count() == 0
        record = TransformationRecord(
            transformation_id="t1",
            transformation_name="bootcamp",
            from_state="init",
            to_state="bootcamp",
            timestamp=datetime.now(),
        )
        evolved = agent.evolve(history=[record])
        assert evolved.transformation_count() == 1

    def test_summary(self):
        agent = AgentIdentity(name="a", capabilities=["x"], traits={"k": "v"})
        s = agent.summary()
        assert s["name"] == "a"
        assert s["state"] == "init"
        assert "x" in s["capabilities"]


# ─── Transformation Tests ─────────────────────────────────────


class TestTransformation:
    def test_create(self):
        t = Transformation(name="bootcamp", from_state="init", to_state="ready")
        assert t.name == "bootcamp"
        assert t.from_state == "init"
        assert t.to_state == "ready"
        assert t.id  # auto-generated

    def test_can_apply_correct_state(self):
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="ready")
        can, reasons = t.can_apply(agent)
        assert can
        assert reasons == []

    def test_can_apply_wrong_state(self):
        agent = AgentIdentity(name="a", state="deployed")
        t = Transformation(name="t", from_state="init", to_state="ready")
        can, reasons = t.can_apply(agent)
        assert not can
        assert any("Wrong state" in r for r in reasons)

    def test_can_apply_wildcard(self):
        agent = AgentIdentity(name="a", state="anything")
        t = Transformation(name="t", from_state="*", to_state="ready")
        can, _ = t.can_apply(agent)
        assert can

    def test_apply(self):
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(
            name="bootcamp",
            from_state="init",
            to_state="bootcamp",
            adds_capabilities=["read_self"],
            adds_traits={"gen": 0},
        )
        result = t.apply(agent)
        assert result.state == "bootcamp"
        assert "read_self" in result.capabilities
        assert result.traits["gen"] == 0
        assert len(result.history) == 1

    def test_apply_invalid_raises(self):
        agent = AgentIdentity(name="a", state="wrong")
        t = Transformation(name="t", from_state="init", to_state="ready")
        with pytest.raises(ValueError, match="Cannot apply"):
            t.apply(agent)

    def test_apply_locked_trait_removal(self):
        agent = AgentIdentity(
            name="a", state="init", traits={"x": 1}, locked_traits={"x"}
        )
        t = Transformation(
            name="t", from_state="init", to_state="ready", removes_traits=["x"]
        )
        can, reasons = t.can_apply(agent)
        assert not can
        assert any("locked" in r for r in reasons)

    def test_apply_removes_capabilities(self):
        agent = AgentIdentity(
            name="a", state="init", capabilities=["old", "keep"]
        )
        t = Transformation(
            name="t",
            from_state="init",
            to_state="ready",
            adds_capabilities=["new"],
            removes_capabilities=["old"],
        )
        result = t.apply(agent)
        assert "new" in result.capabilities
        assert "old" not in result.capabilities
        assert "keep" in result.capabilities


# ─── Trigger Tests ────────────────────────────────────────────


class TestTrigger:
    def test_manual_trigger_match(self):
        trigger = Trigger(type=TriggerType.MANUAL, condition="force-level-up")
        assert trigger.matches({"manual_trigger": "force-level-up"})
        assert not trigger.matches({"manual_trigger": "other"})

    def test_score_threshold(self):
        trigger = Trigger(type=TriggerType.SCORE_THRESHOLD, condition="8")
        assert trigger.matches({"score": 9})
        assert trigger.matches({"score": 8})
        assert not trigger.matches({"score": 7})

    def test_milestone_trigger(self):
        trigger = Trigger(type=TriggerType.MILESTONE, condition="basics")
        assert trigger.matches({"achieved_milestones": ["basics", "advanced"]})
        assert not trigger.matches({"achieved_milestones": ["advanced"]})

    def test_external_event(self):
        trigger = Trigger(type=TriggerType.EXTERNAL_EVENT, condition="deploy")
        assert trigger.matches({"event": "deploy"})
        assert not trigger.matches({"event": "other"})

    def test_time_based(self):
        trigger = Trigger(type=TriggerType.TIME_BASED, condition="1h")
        assert trigger.matches({"time_elapsed": True})
        assert not trigger.matches({"time_elapsed": False})

    def test_self_initiated(self):
        trigger = Trigger(type=TriggerType.SELF_INITIATED, condition="auto")
        assert trigger.matches({"self_initiated": True})
        assert not trigger.matches({"self_initiated": False})


# ─── Requirement Tests ────────────────────────────────────────


class TestRequirement:
    def test_capability_req(self):
        agent = AgentIdentity(name="a", capabilities=["read"])
        req = Requirement(type=RequirementType.CAPABILITY, name="read")
        assert req.is_satisfied(agent)

        req2 = Requirement(type=RequirementType.CAPABILITY, name="write")
        assert not req2.is_satisfied(agent)

    def test_trait_req(self):
        agent = AgentIdentity(name="a", traits={"role": "admin"})
        req = Requirement(type=RequirementType.TRAIT, name="role", value="admin")
        assert req.is_satisfied(agent)

        req2 = Requirement(type=RequirementType.TRAIT, name="role", value="user")
        assert not req2.is_satisfied(agent)

    def test_score_req(self):
        agent = AgentIdentity(name="a", scores={"quality": 8.5})
        req = Requirement(type=RequirementType.SCORE, name="quality", value=7.0)
        assert req.is_satisfied(agent)

    def test_milestone_req(self):
        agent = AgentIdentity(name="a", achieved_milestones=["basics"])
        req = Requirement(type=RequirementType.MILESTONE, name="basics")
        assert req.is_satisfied(agent)

    def test_custom_req(self):
        agent = AgentIdentity(name="a", custom_checks={"verified": True})
        req = Requirement(type=RequirementType.CUSTOM, name="verified")
        assert req.is_satisfied(agent)

        agent2 = AgentIdentity(name="a")
        assert not req.is_satisfied(agent2)


# ─── EvolutionEngine Tests ────────────────────────────────────


class TestEvolutionEngine:
    def _make_chain(self):
        return [
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

    def test_register_and_get(self):
        engine = EvolutionEngine()
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine.register(t)
        assert engine.get(t.id) == t

    def test_unregister(self):
        engine = EvolutionEngine()
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine.register(t)
        engine.unregister(t.id)
        assert engine.get(t.id) is None

    def test_evolve_success(self):
        t = Transformation(
            name="bootcamp", from_state="init", to_state="bootcamp"
        )
        engine = EvolutionEngine([t])
        agent = AgentIdentity(name="a", state="init")
        result = engine.evolve(agent, t)
        assert result.success
        assert result.identity.state == "bootcamp"

    def test_evolve_failure(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = EvolutionEngine()
        agent = AgentIdentity(name="a", state="wrong")
        result = engine.evolve(agent, t)
        assert not result.success
        assert result.identity.state == "wrong"

    def test_evolve_strict_raises(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = EvolutionEngine(strict=True)
        agent = AgentIdentity(name="a", state="wrong")
        with pytest.raises(ValueError):
            engine.evolve(agent, t)

    def test_evolve_by_id(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = EvolutionEngine([t])
        agent = AgentIdentity(name="a", state="init")
        result = engine.evolve_by_id(agent, t.id)
        assert result.success

    def test_evolve_by_id_unknown(self):
        engine = EvolutionEngine()
        agent = AgentIdentity(name="a")
        result = engine.evolve_by_id(agent, "nonexistent")
        assert not result.success
        assert "Unknown transformation" in result.errors[0]

    def test_evolve_all_applicable(self):
        chain = self._make_chain()
        engine = EvolutionEngine(chain)
        agent = AgentIdentity(name="a", state="init")
        results = engine.evolve_all_applicable(agent)
        assert len(results) == 3
        assert results[-1].identity.state == "deployed"

    def test_evolve_overnight(self):
        chain = self._make_chain()
        engine = EvolutionEngine(chain)
        agent = AgentIdentity(name="a", state="init")
        final, results = engine.evolve_overnight(agent, steps=5)
        assert final.state == "deployed"
        assert len(results) == 3

    def test_find_applicable(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = EvolutionEngine([t])
        agent = AgentIdentity(name="a", state="init")
        applicable = engine.find_applicable(agent)
        assert len(applicable) == 1

    def test_find_triggered(self):
        t = Transformation(
            name="auto-level",
            from_state="init",
            to_state="ready",
            triggers=[
                Trigger(type=TriggerType.SCORE_THRESHOLD, condition="8")
            ],
        )
        engine = EvolutionEngine([t])
        agent = AgentIdentity(name="a", state="init")
        triggered = engine.find_triggered(agent, {"score": 9})
        assert len(triggered) == 1
        not_triggered = engine.find_triggered(agent, {"score": 5})
        assert len(not_triggered) == 0


# ─── Milestone Tests ─────────────────────────────────────────


class TestMilestone:
    def test_lifecycle(self):
        m = Milestone(name="basics", description="Learn fundamentals")
        assert m.status == MilestoneStatus.PENDING

        started = m.start()
        assert started.status == MilestoneStatus.IN_PROGRESS

        achieved = started.achieve(score=1.0)
        assert achieved.status == MilestoneStatus.ACHIEVED
        assert achieved.score == 1.0
        assert achieved.achieved_at is not None

    def test_cannot_start_achieved(self):
        m = Milestone(name="m", status=MilestoneStatus.ACHIEVED)
        with pytest.raises(ValueError, match="Cannot start"):
            m.start()

    def test_fail(self):
        m = Milestone(name="m")
        failed = m.fail("timeout")
        assert failed.status == MilestoneStatus.FAILED
        assert failed.metadata["failure_reason"] == "timeout"

    def test_skip(self):
        m = Milestone(name="m")
        skipped = m.skip("not needed")
        assert skipped.status == MilestoneStatus.SKIPPED

    def test_is_complete(self):
        assert Milestone(name="m", status=MilestoneStatus.ACHIEVED).is_complete()
        assert Milestone(name="m", status=MilestoneStatus.FAILED).is_complete()
        assert not Milestone(name="m", status=MilestoneStatus.PENDING).is_complete()

    def test_progress(self):
        assert Milestone(name="m", status=MilestoneStatus.ACHIEVED).progress() == 1.0
        assert Milestone(name="m", status=MilestoneStatus.FAILED).progress() == 0.0
        m = Milestone(name="m", score=0.6, status=MilestoneStatus.IN_PROGRESS)
        assert m.progress() == pytest.approx(0.6)

    def test_prerequisites(self):
        m = Milestone(name="advanced", prerequisites=["basics"])
        assert m.can_start(["basics"])
        assert not m.can_start([])
        assert not m.can_start(["basics"]) if m.status != MilestoneStatus.PENDING else True

    def test_can_start_wrong_status(self):
        m = Milestone(name="m", status=MilestoneStatus.IN_PROGRESS)
        assert not m.can_start([])

    def test_achieve_idempotent(self):
        m = Milestone(name="m", status=MilestoneStatus.ACHIEVED)
        result = m.achieve()
        assert result is m

    def test_summary(self):
        m = Milestone(name="m", description="test", status=MilestoneStatus.PENDING)
        s = m.summary()
        assert s["name"] == "m"
        assert s["status"] == "pending"


# ─── Registry Tests ──────────────────────────────────────────


class TestTransformationRegistry:
    def _make_transforms(self):
        t1 = Transformation(name="bootcamp", from_state="init", to_state="bootcamp")
        t2 = Transformation(
            name="skill-up", from_state="bootcamp", to_state="capable"
        )
        t3 = Transformation(name="deploy", from_state="capable", to_state="deployed")
        return t1, t2, t3

    def test_add_and_get(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        reg.add_transformation(t, tags=["core"], category="init")
        entry = reg.get(t.id)
        assert entry is not None
        assert entry.tags == ["core"]

    def test_find_by_tag(self):
        t1, t2, t3 = self._make_transforms()
        reg = TransformationRegistry()
        reg.add_transformation(t1, tags=["core"])
        reg.add_transformation(t2, tags=["skill"])
        reg.add_transformation(t3, tags=["core"])
        results = reg.find_by_tag("core")
        assert len(results) == 2

    def test_find_by_category(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        reg.add_transformation(t, category="init")
        results = reg.find_by_category("init")
        assert len(results) == 1

    def test_find_by_state(self):
        t1, t2, t3 = self._make_transforms()
        reg = TransformationRegistry()
        for t in [t1, t2, t3]:
            reg.add_transformation(t)
        results = reg.find_by_state("init", "bootcamp")
        assert len(results) == 1

    def test_find_path(self):
        t1, t2, t3 = self._make_transforms()
        reg = TransformationRegistry()
        for t in [t1, t2, t3]:
            reg.add_transformation(t)
        path = reg.find_path("init", "deployed")
        assert len(path) == 3
        assert path[0].name == "bootcamp"
        assert path[2].name == "deploy"

    def test_find_path_same_state(self):
        reg = TransformationRegistry()
        assert reg.find_path("init", "init") == []

    def test_find_path_no_path(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        reg.add_transformation(t)
        assert reg.find_path("ready", "deployed") == []

    def test_find_applicable(self):
        t1, t2, _ = self._make_transforms()
        reg = TransformationRegistry()
        reg.add_transformation(t1)
        reg.add_transformation(t2)
        agent = AgentIdentity(name="a", state="init")
        results = reg.find_applicable(agent)
        assert len(results) == 1

    def test_deprecated_excluded(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        entry = RegistryEntry(transformation=t, deprecated=True)
        reg.add(entry)
        agent = AgentIdentity(name="a", state="init")
        results = reg.find_applicable(agent)
        assert len(results) == 0

    def test_remove(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        reg.add_transformation(t)
        reg.remove(t.id)
        assert reg.size == 0

    def test_summary(self):
        t = Transformation(name="t", from_state="init", to_state="ready")
        reg = TransformationRegistry()
        reg.add_transformation(t, tags=["core"], category="init")
        s = reg.summary()
        assert s["total_transformations"] == 1
        assert s["categories"]["init"] == 1
        assert s["tags"]["core"] == 1


# ─── Protocol Tests ───────────────────────────────────────────


class TestTransformProtocol:
    def test_validate_allowed(self):
        proto = TransformProtocol()
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="ready")
        valid, violations = proto.validate(agent, t)
        assert valid
        assert violations == []

    def test_forbidden_state(self):
        proto = TransformProtocol(forbidden_states={"jail"})
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="jail")
        valid, violations = proto.validate(agent, t)
        assert not valid
        assert any("forbidden" in v for v in violations)

    def test_terminal_state(self):
        proto = TransformProtocol(
            state_rules=[StateRule(state="dead", terminal=True)]
        )
        agent = AgentIdentity(name="a", state="dead")
        t = Transformation(name="t", from_state="dead", to_state="alive")
        valid, violations = proto.validate(agent, t)
        assert not valid
        assert any("terminal" in v for v in violations)

    def test_transition_not_allowed(self):
        proto = TransformProtocol(
            transition_rules=[
                TransitionRule(from_state="init", to_state="jail", allowed=False)
            ]
        )
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="jail")
        valid, violations = proto.validate(agent, t)
        assert not valid

    def test_max_uses(self):
        record = TransformationRecord(
            transformation_id="t1",
            transformation_name="t",
            from_state="init",
            to_state="ready",
            timestamp=datetime.now(),
        )
        proto = TransformProtocol(
            transition_rules=[
                TransitionRule(from_state="init", to_state="ready", max_uses=1)
            ]
        )
        agent = AgentIdentity(name="a", state="init", history=[record])
        t = Transformation(name="t", from_state="init", to_state="ready")
        valid, _ = proto.validate(agent, t)
        assert not valid

    def test_state_required_capabilities(self):
        proto = TransformProtocol(
            state_rules=[
                StateRule(state="advanced", required_capabilities=["core_skill"])
            ]
        )
        agent = AgentIdentity(name="a", state="init", capabilities=[])
        t = Transformation(name="t", from_state="init", to_state="advanced")
        valid, violations = proto.validate(agent, t)
        assert not valid
        assert any("Missing capabilities" in v for v in violations)

    def test_max_total_transformations(self):
        record = TransformationRecord(
            transformation_id="t1",
            transformation_name="t",
            from_state="init",
            to_state="ready",
            timestamp=datetime.now(),
        )
        proto = TransformProtocol(max_total_transformations=1)
        agent = AgentIdentity(name="a", state="init", history=[record])
        t = Transformation(name="t2", from_state="ready", to_state="done")
        valid, _ = proto.validate(agent, t)
        assert not valid

    def test_sequential_mode(self):
        record = TransformationRecord(
            transformation_id="t1",
            transformation_name="t",
            from_state="init",
            to_state="ready",
            timestamp=datetime.now(),
        )
        proto = TransformProtocol(require_sequential=True)
        agent = AgentIdentity(name="a", state="ready", history=[record])
        t = Transformation(name="t2", from_state="init", to_state="done")
        valid, _ = proto.validate(agent, t)
        assert not valid

    def test_is_terminal(self):
        proto = TransformProtocol(
            state_rules=[StateRule(state="dead", terminal=True)]
        )
        assert proto.is_terminal("dead")
        assert not proto.is_terminal("alive")

    def test_allowed_transitions(self):
        proto = TransformProtocol(
            transition_rules=[
                TransitionRule(from_state="init", to_state="ready", allowed=True),
                TransitionRule(from_state="init", to_state="bootcamp", allowed=True),
                TransitionRule(from_state="init", to_state="jail", allowed=False),
            ]
        )
        allowed = proto.allowed_transitions("init")
        assert "ready" in allowed
        assert "bootcamp" in allowed
        assert "jail" not in allowed


# ─── CapabilityTree Tests ─────────────────────────────────────


class TestCapabilityTree:
    def _make_tree(self):
        return CapabilityTree([
            CapabilityNode(name="read", tier=0, category="core"),
            CapabilityNode(name="write", tier=1, prerequisites=["read"]),
            CapabilityNode(
                name="deploy", tier=2, prerequisites=["write", "read"]
            ),
            CapabilityNode(name="chat", tier=0, category="social"),
        ])

    def test_add_and_get(self):
        tree = CapabilityTree()
        tree.add(CapabilityNode(name="fly"))
        assert tree.get("fly") is not None
        assert tree.get("swim") is None

    def test_prerequisites_of(self):
        tree = self._make_tree()
        assert tree.prerequisites_of("deploy") == ["write", "read"]
        assert tree.prerequisites_of("read") == []

    def test_all_prerequisites(self):
        tree = self._make_tree()
        prereqs = tree.all_prerequisites("deploy")
        assert "read" in prereqs
        assert "write" in prereqs
        # read should come before write
        assert prereqs.index("read") < prereqs.index("write")

    def test_can_unlock(self):
        tree = self._make_tree()
        can, missing = tree.can_unlock("read", set())
        assert can
        can, missing = tree.can_unlock("write", set())
        assert not can
        assert "read" in missing
        can, missing = tree.can_unlock("write", {"read"})
        assert can

    def test_can_unlock_unknown(self):
        tree = CapabilityTree()
        can, missing = tree.can_unlock("unknown", set())
        assert not can

    def test_can_unlock_already_held(self):
        tree = CapabilityTree([CapabilityNode(name="fly")])
        can, _ = tree.can_unlock("fly", {"fly"})
        assert not can

    def test_unlock_order(self):
        tree = self._make_tree()
        order = tree.unlock_order(["deploy"], set())
        assert order.index("read") < order.index("write")
        assert order.index("write") < order.index("deploy")

    def test_unlock_order_with_held(self):
        tree = self._make_tree()
        order = tree.unlock_order(["deploy"], {"read"})
        assert "read" not in order
        assert "write" in order
        assert "deploy" in order

    def test_available_to_unlock(self):
        tree = self._make_tree()
        avail = tree.available_to_unlock(set())
        assert "read" in avail
        assert "chat" in avail
        assert "write" not in avail

    def test_by_category(self):
        tree = self._make_tree()
        core = tree.by_category("core")
        assert len(core) == 1  # only 'read' has category='core'

    def test_by_tier(self):
        tree = self._make_tree()
        tier0 = tree.by_tier(0)
        assert len(tier0) == 2  # read, chat

    def test_validate_clean(self):
        tree = self._make_tree()
        issues = tree.validate()
        assert issues == []

    def test_validate_missing_prereq(self):
        tree = CapabilityTree([
            CapabilityNode(name="fly", prerequisites=["wings"])
        ])
        issues = tree.validate()
        assert any("unknown capability" in i for i in issues)

    def test_validate_cycle(self):
        tree = CapabilityTree([
            CapabilityNode(name="a", prerequisites=["b"]),
            CapabilityNode(name="b", prerequisites=["a"]),
        ])
        issues = tree.validate()
        assert any("Cycle" in i for i in issues)

    def test_summary(self):
        tree = self._make_tree()
        s = tree.summary()
        assert s["total_capabilities"] == 4
        assert s["base_capabilities"] == 2  # read, chat

    def test_remove(self):
        tree = CapabilityTree([CapabilityNode(name="fly")])
        tree.remove("fly")
        assert tree.size == 0


# ─── AssessmentEngine Tests ───────────────────────────────────


class TestAssessmentEngine:
    def test_assess_readiness_ready(self):
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = AssessmentEngine()
        report = engine.assess_readiness(agent, t)
        assert report.ready
        assert report.score == 1.0

    def test_assess_readiness_not_ready(self):
        agent = AgentIdentity(name="a", state="wrong")
        t = Transformation(
            name="t",
            from_state="init",
            to_state="ready",
            requirements=[
                Requirement(type=RequirementType.CAPABILITY, name="read")
            ],
        )
        engine = AssessmentEngine()
        report = engine.assess_readiness(agent, t)
        assert not report.ready
        assert report.score < 1.0
        assert len(report.unmet_requirements) > 0
        assert len(report.recommendations) > 0

    def test_assess_readiness_with_protocol(self):
        proto = TransformProtocol(forbidden_states={"jail"})
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="jail")
        engine = AssessmentEngine(protocol=proto)
        report = engine.assess_readiness(agent, t)
        assert not report.ready
        assert len(report.protocol_violations) > 0

    def test_assess_progress(self):
        agent = AgentIdentity(
            name="a",
            state="capable",
            capabilities=["read", "write"],
            achieved_milestones=["basics"],
        )
        m = Milestone(name="basics", status=MilestoneStatus.ACHIEVED)
        engine = AssessmentEngine()
        report = engine.assess_progress(agent, milestones=[m])
        assert report.identity_name == "a"
        assert report.current_state == "capable"
        assert report.capabilities_held == 2
        assert report.milestones_achieved == 1
        assert 0.0 <= report.overall_score <= 1.0

    def test_assess_progress_next_steps(self):
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="bootcamp", from_state="init", to_state="bootcamp")
        engine = AssessmentEngine()
        report = engine.assess_progress(agent, transformations=[t])
        assert any("bootcamp" in s for s in report.next_steps)

    def test_improvement_plan_ready(self):
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(name="t", from_state="init", to_state="ready")
        engine = AssessmentEngine()
        plan = engine.improvement_plan(agent, t)
        assert any("Ready" in p for p in plan)

    def test_improvement_plan_not_ready(self):
        agent = AgentIdentity(name="a", state="wrong")
        t = Transformation(
            name="t",
            from_state="init",
            to_state="ready",
            requirements=[
                Requirement(type=RequirementType.CAPABILITY, name="read")
            ],
        )
        engine = AssessmentEngine()
        plan = engine.improvement_plan(agent, t)
        assert len(plan) > 1
        assert plan[0].startswith("Goal:")

    def test_assess_with_capability_tree(self):
        tree = CapabilityTree([
            CapabilityNode(name="read", tier=0),
            CapabilityNode(name="write", tier=1, prerequisites=["read"]),
        ])
        agent = AgentIdentity(name="a", state="init")
        t = Transformation(
            name="t",
            from_state="init",
            to_state="ready",
            adds_capabilities=["write"],
        )
        engine = AssessmentEngine(capability_tree=tree)
        report = engine.assess_readiness(agent, t)
        # Should suggest acquiring 'read' as prereq for 'write'
        assert any("read" in r for r in report.recommendations)


# ─── Integration Tests ────────────────────────────────────────


class TestIntegration:
    def test_full_lifecycle(self):
        """End-to-end: create agent, define chain, evolve through all stages."""
        agent = AgentIdentity(name="lifecycle-bot", state="init")

        transforms = [
            Transformation(
                name="bootcamp",
                from_state="init",
                to_state="bootcamp",
                adds_capabilities=["read_self"],
                adds_traits={"generation": 0},
            ),
            Transformation(
                name="skill-up",
                from_state="bootcamp",
                to_state="capable",
                adds_capabilities=["chat", "learn"],
                requirements=[
                    Requirement(
                        type=RequirementType.CAPABILITY,
                        name="read_self",
                        description="Must have self-awareness",
                    )
                ],
            ),
            Transformation(
                name="deploy",
                from_state="capable",
                to_state="deployed",
                adds_traits={"quality": "production"},
                requirements=[
                    Requirement(type=RequirementType.CAPABILITY, name="chat"),
                ],
            ),
        ]

        engine = EvolutionEngine(transforms)
        results = engine.evolve_all_applicable(agent)

        assert len(results) == 3
        final = results[-1].identity
        assert final.state == "deployed"
        assert "chat" in final.capabilities
        assert "learn" in final.capabilities
        assert final.traits["quality"] == "production"
        assert final.transformation_count() == 3

    def test_registry_path_finding(self):
        """Registry can find a path through complex transformation graphs."""
        transforms = [
            Transformation(name="a->b", from_state="a", to_state="b"),
            Transformation(name="b->c", from_state="b", to_state="c"),
            Transformation(name="c->d", from_state="c", to_state="d"),
            Transformation(name="a->d", from_state="a", to_state="d"),
        ]
        reg = TransformationRegistry()
        for t in transforms:
            reg.add_transformation(t)

        path = reg.find_path("a", "d")
        assert len(path) == 1  # direct path a->d
        assert path[0].name == "a->d"

    def test_protocol_with_engine(self):
        """Protocol can block transformations that the engine would allow."""
        proto = TransformProtocol(forbidden_states={"quarantine"})

        t = Transformation(
            name="infect",
            from_state="healthy",
            to_state="quarantine",
        )
        agent = AgentIdentity(name="a", state="healthy")

        # Transformation itself would allow it
        can, _ = t.can_apply(agent)
        assert can

        # Protocol blocks it
        valid, violations = proto.validate(agent, t)
        assert not valid

    def test_capability_tree_unlock_sequence(self):
        """Capability tree can plan unlock sequences."""
        tree = CapabilityTree([
            CapabilityNode(name="basics", tier=0),
            CapabilityNode(name="intermediate", tier=1, prerequisites=["basics"]),
            CapabilityNode(name="advanced", tier=2, prerequisites=["intermediate"]),
        ])

        order = tree.unlock_order(["advanced"], set())
        assert order == ["basics", "intermediate", "advanced"]

        # Partial progress
        order2 = tree.unlock_order(["advanced"], {"basics"})
        assert "basics" not in order2
        assert order2 == ["intermediate", "advanced"]

    def test_assessment_with_full_stack(self):
        """Assessment engine integrates with all components."""
        tree = CapabilityTree([
            CapabilityNode(name="read", tier=0),
            CapabilityNode(name="write", tier=1, prerequisites=["read"]),
        ])
        proto = TransformProtocol()
        engine = AssessmentEngine(protocol=proto, capability_tree=tree)

        agent = AgentIdentity(name="a", state="init")
        t = Transformation(
            name="level-up",
            from_state="init",
            to_state="capable",
            adds_capabilities=["write"],
        )

        report = engine.assess_readiness(agent, t)
        assert report.ready  # no requirements on the transform itself
        # but recommendations should suggest acquiring 'read' prereq
        assert any("read" in r for r in report.recommendations)
