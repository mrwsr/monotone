"""
Tests for L{monotone}.
"""
from hypothesis import given, strategies as st
import errno

from monotone import monotonic
from monotone import _api, _bindings

import pytest


@pytest.fixture
def errno_value():
    """
    A particular errno.
    """
    return errno.EINVAL


@pytest.fixture
def strerror(errno_value):
    """
    The string representation of a particular errno
    """
    return "[Errno {}] Invalid argument".format(errno_value)


@pytest.fixture
def apply_failing_clock_call(monkeypatch, errno_value):
    """
    Return a callable that patches in a failing system call fake that
    fails and return a list of calls to that fake.
    """

    def _apply_failing_clock_call(name):
        calls = []

        def _failing_clock_call(clock_id, timespec):
            calls.append((clock_id, timespec))
            monkeypatch.setattr(_api.ffi, "errno", errno.EINVAL)
            return -1

        monkeypatch.setattr(_api, name, _failing_clock_call)

        return calls

    return _apply_failing_clock_call


@pytest.mark.parametrize("name", ["_clock_getres", "_clock_gettime"])
def test_clock_call_fails(apply_failing_clock_call, name, strerror):
    """
    A failure in a clock-related system call results in an L{OSError}
    that presents the failure's errno.
    """
    calls = apply_failing_clock_call(name)

    with pytest.raises(OSError) as exc:
        monotonic()

    assert len(calls) == 1
    assert calls[0][0] == _bindings.lib.CLOCK_MONOTONIC

    assert str(exc.value) == strerror


@pytest.fixture
def apply_timespec(monkeypatch):
    """
    Return a callable that patches in a fake over the specified clock
    call that sets the specified resolution and returns a list of
    calls to that fake.
    """

    def _apply_timespec(name, target_timespec):
        calls = []

        def _fake_clock_call(clock_id, timespec):
            calls.append((clock_id, timespec))
            timespec[0] = target_timespec[0]
            return 0

        monkeypatch.setattr(_api, name, _fake_clock_call)

        return calls

    return _apply_timespec


@given(
    clock_getres_spec=st.fixed_dictionaries({
        "tv_sec": st.sampled_from([0, 1]),
        "tv_nsec": st.sampled_from([0, 1]),

    }),
    clock_gettime_spec=st.fixed_dictionaries({
        "tv_sec": st.integers(min_value=0, max_value=2 ** 32 - 1),
        "tv_nsec": st.integers(min_value=0, max_value=2 ** 32 - 1),

    }),
)
def test_clock(clock_getres_spec, clock_gettime_spec, apply_timespec):
    """
    For any given time resolution, the monotonic time equals the
    sum of the seconds and nanoseconds.
    """
    clock_getres_calls = apply_timespec(
        '_clock_getres',
        _bindings.ffi.new("struct timespec *", clock_getres_spec),
    )
    clock_gettime_calls = apply_timespec(
        '_clock_gettime',
        _bindings.ffi.new("struct timespec *", clock_gettime_spec),
    )

    # we a float, representing the current seconds plus the
    # nanoseconds (offset by a billion) iff the resolution is accurate
    # to the nanosecond.
    expected = float(clock_gettime_spec['tv_sec']) + (
        (clock_gettime_spec['tv_nsec'] * 1e-09)
        if clock_getres_spec['tv_nsec'] else
        0)

    result = monotonic()

    assert result - expected == pytest.approx(0.0)

    assert len(clock_getres_calls) == 1
    assert len(clock_gettime_calls) == 1
    assert clock_getres_calls[0][0] == _bindings.lib.CLOCK_MONOTONIC
    assert clock_gettime_calls[0][0] == _bindings.lib.CLOCK_MONOTONIC


def test_clock_increases():
    """
    A monotonic moment is never greater than a succeeding monotonic
    moment.
    """
    assert monotonic() <= monotonic()
