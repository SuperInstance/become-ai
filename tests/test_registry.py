"""Tests for TransformationRegistry."""

from become_ai.registry import TransformationRegistry, RegistryEntry
from become_ai.identity import AgentIdentity
from become_ai.transformation import Transformation


def _make_chain():
    t1 = Transformation(name="boot", from_state="init", to_state="ready")
    t2 = Transformation(name="train", from_state="ready", to_state="trained")
    t3 = Transformation(name="deploy", from_state="trained", to_state="deployed")
    return t1, t2, t3


def test_add_and_get():
    reg = TransformationRegistry()
    t = Transformation(name="t", from_state="*", to_state="done")
    reg.add_transformation(t, tags=["core"], category="basic")
    entry = reg.get(t.id)
    assert entry is not None
    assert entry.category == "basic"


def test_remove():
    reg = TransformationRegistry()
    t = Transformation(name="t", from_state="*", to_state="done")
    reg.add_transformation(t)
    reg.remove(t.id)
    assert reg.get(t.id) is None


def test_get_by_name():
    reg = TransformationRegistry()
    t = Transformation(name="my-transform", from_state="*", to_state="done")
    reg.add_transformation(t)
    entries = reg.get_by_name("my-transform")
    assert len(entries) == 1
    assert entries[0].transformation is t


def test_find_by_state():
    reg = TransformationRegistry()
    t1, t2, t3 = _make_chain()
    for t in (t1, t2, t3):
        reg.add_transformation(t)
    results = reg.find_by_state("init", "ready")
    assert len(results) == 1
    assert results[0].transformation is t1


def test_find_by_tag():
    reg = TransformationRegistry()
    reg.add_transformation(
        Transformation(name="a", from_state="*", to_state="x"),
        tags=["experimental"],
    )
    reg.add_transformation(
        Transformation(name="b", from_state="*", to_state="y"),
        tags=["stable"],
    )
    results = reg.find_by_tag("experimental")
    assert len(results) == 1


def test_find_by_category():
    reg = TransformationRegistry()
    reg.add_transformation(
        Transformation(name="a", from_state="*", to_state="x"),
        category="bootcamp",
    )
    results = reg.find_by_category("bootcamp")
    assert len(results) == 1


def test_find_applicable():
    reg = TransformationRegistry()
    t1, t2, t3 = _make_chain()
    for t in (t1, t2, t3):
        reg.add_transformation(t)
    identity = AgentIdentity(name="a", state="ready")
    applicable = reg.find_applicable(identity)
    assert len(applicable) == 1
    assert applicable[0].transformation.name == "train"


def test_deprecated_excluded():
    reg = TransformationRegistry()
    entry = RegistryEntry(
        transformation=Transformation(name="old", from_state="*", to_state="x"),
        deprecated=True,
    )
    reg.add(entry)
    identity = AgentIdentity(name="a", state="anything")
    assert reg.find_applicable(identity) == []


def test_find_path():
    reg = TransformationRegistry()
    t1, t2, t3 = _make_chain()
    for t in (t1, t2, t3):
        reg.add_transformation(t)
    path = reg.find_path("init", "deployed")
    assert len(path) == 3
    assert path[0] is t1
    assert path[1] is t2
    assert path[2] is t3


def test_find_path_same_state():
    reg = TransformationRegistry()
    path = reg.find_path("init", "init")
    assert path == []


def test_find_path_no_path():
    reg = TransformationRegistry()
    t = Transformation(name="t", from_state="init", to_state="ready")
    reg.add_transformation(t)
    path = reg.find_path("init", "deployed")
    assert path == []


def test_size():
    reg = TransformationRegistry()
    t1, t2 = _make_chain()[:2]
    reg.add_transformation(t1)
    reg.add_transformation(t2)
    assert reg.size == 2


def test_summary():
    reg = TransformationRegistry()
    reg.add_transformation(
        Transformation(name="a", from_state="*", to_state="x"),
        tags=["core"], category="bootcamp",
    )
    s = reg.summary()
    assert s["total_transformations"] == 1
    assert s["categories"]["bootcamp"] == 1
    assert s["tags"]["core"] == 1
