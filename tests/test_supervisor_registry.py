"""Tests for SupervisorRegistry."""

from unittest.mock import MagicMock

import pytest

from procwatch.supervisor_registry import SupervisorRegistry


def _make_supervisor(name: str) -> MagicMock:
    sv = MagicMock()
    sv.name = name
    return sv


class TestSupervisorRegistryRegister:
    def test_register_adds_supervisor(self):
        reg = SupervisorRegistry()
        sv = _make_supervisor("web")
        reg.register(sv)
        assert reg.get("web") is sv

    def test_register_duplicate_raises(self):
        reg = SupervisorRegistry()
        reg.register(_make_supervisor("web"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_make_supervisor("web"))

    def test_register_different_names(self):
        reg = SupervisorRegistry()
        reg.register(_make_supervisor("web"))
        reg.register(_make_supervisor("worker"))
        assert len(reg) == 2


class TestSupervisorRegistryUnregister:
    def test_unregister_removes_supervisor(self):
        reg = SupervisorRegistry()
        reg.register(_make_supervisor("web"))
        reg.unregister("web")
        assert reg.get("web") is None

    def test_unregister_missing_is_noop(self):
        reg = SupervisorRegistry()
        reg.unregister("nonexistent")  # should not raise


class TestSupervisorRegistryQuery:
    def test_get_returns_none_for_missing(self):
        reg = SupervisorRegistry()
        assert reg.get("missing") is None

    def test_all_returns_snapshot(self):
        reg = SupervisorRegistry()
        sv1 = _make_supervisor("a")
        sv2 = _make_supervisor("b")
        reg.register(sv1)
        reg.register(sv2)
        result = reg.all()
        assert set(result) == {sv1, sv2}

    def test_names_returns_all_names(self):
        reg = SupervisorRegistry()
        reg.register(_make_supervisor("x"))
        reg.register(_make_supervisor("y"))
        assert set(reg.names()) == {"x", "y"}

    def test_len_reflects_count(self):
        reg = SupervisorRegistry()
        assert len(reg) == 0
        reg.register(_make_supervisor("a"))
        assert len(reg) == 1

    def test_iter_yields_all_supervisors(self):
        reg = SupervisorRegistry()
        sv = _make_supervisor("svc")
        reg.register(sv)
        assert list(reg) == [sv]

    def test_clear_removes_all(self):
        reg = SupervisorRegistry()
        reg.register(_make_supervisor("a"))
        reg.register(_make_supervisor("b"))
        reg.clear()
        assert len(reg) == 0
