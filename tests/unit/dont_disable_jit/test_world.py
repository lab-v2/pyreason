import numba
from pyreason.scripts.components.world import World
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def test_init_empty_world_and_str():
    w = World([])
    assert list(w.world.keys()) == []
    assert w.get_world() == w.world
    assert str(w) == ""


def test_make_world_and_bounds():
    l = label.Label("A")
    world_dict = numba.typed.Dict.empty(
        key_type=label.label_type, value_type=interval.interval_type
    )
    world_dict[l] = interval.closed(0.4, 0.6)
    w = World.make_world([l], world_dict)
    assert w.world is world_dict
    b = w.get_bound(l)
    assert b.lower == 0.4 and b.upper == 0.6


def test_is_satisfied_and_update_and_str():
    l = label.Label("B")
    w = World([l])
    assert w.is_satisfied(l, interval.closed(0.0, 1.0))
    assert not w.is_satisfied(l, interval.closed(0.0, 0.5))
    w.update(l, interval.closed(0.2, 0.4))
    b = w.get_bound(l)
    assert b.lower == 0.2 and b.upper == 0.4
    assert "B,[0.2,0.4]" in str(w)
