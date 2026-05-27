"""Tests for Milestone."""

from become_ai.milestone import Milestone, MilestoneStatus


def test_create_milestone():
    m = Milestone(name="first-feature", description="Build the first feature")
    assert m.name == "first-feature"
    assert m.status == MilestoneStatus.PENDING
    assert m.progress() == 0.0


def test_start_milestone():
    m = Milestone(name="m1")
    started = m.start()
    assert started.status == MilestoneStatus.IN_PROGRESS


def test_start_non_pending_raises():
    m = Milestone(name="m1", status=MilestoneStatus.ACHIEVED)
    try:
        m.start()
        assert False, "Should have raised"
    except ValueError:
        pass


def test_achieve_milestone():
    m = Milestone(name="m1", status=MilestoneStatus.IN_PROGRESS, score=0.5)
    achieved = m.achieve(score=1.0)
    assert achieved.status == MilestoneStatus.ACHIEVED
    assert achieved.score == 1.0
    assert achieved.achieved_at is not None
    assert achieved.progress() == 1.0
    assert achieved.is_complete()


def test_achieve_idempotent():
    m = Milestone(name="m1", status=MilestoneStatus.ACHIEVED)
    achieved = m.achieve()
    assert achieved.status == MilestoneStatus.ACHIEVED


def test_fail_milestone():
    m = Milestone(name="m1")
    failed = m.fail("tests didn't pass")
    assert failed.status == MilestoneStatus.FAILED
    assert failed.metadata.get("failure_reason") == "tests didn't pass"
    assert failed.is_complete()
    assert failed.progress() == 0.0


def test_skip_milestone():
    m = Milestone(name="m1")
    skipped = m.skip("not needed")
    assert skipped.status == MilestoneStatus.SKIPPED
    assert skipped.is_complete()


def test_prerequisites():
    m = Milestone(name="advanced", prerequisites=["basics"])
    assert not m.can_start([])
    assert m.can_start(["basics"])
    assert not m.can_start(["other"])


def test_can_start_only_when_pending():
    m = Milestone(name="m1", status=MilestoneStatus.IN_PROGRESS)
    assert not m.can_start([])


def test_progress_in_progress():
    m = Milestone(name="m1", status=MilestoneStatus.IN_PROGRESS, score=0.6)
    assert m.progress() == 0.6


def test_progress_clamped():
    m = Milestone(name="m1", status=MilestoneStatus.IN_PROGRESS, score=1.5)
    assert m.progress() == 1.0


def test_summary():
    m = Milestone(name="m1", description="test", status=MilestoneStatus.ACHIEVED)
    s = m.summary()
    assert s["name"] == "m1"
    assert s["status"] == "achieved"
    assert s["progress"] == 1.0
