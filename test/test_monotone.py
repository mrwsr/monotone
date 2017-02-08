"""
Tests for L{monotone}.
"""
from hypothesis import given, strategies as st
import errno

from monotone import get_clock_info, monotonic
from monotone import _api, _bindings

import os

import platform

import pytest

needs_posix = pytest.mark.skipif(
    os.name == "posix" and platform.system() == "Darwin",
    reason="POSIX-only tests (clock_gettime(3))",
)
needs_macos = pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="macOS-only tests (mach_absolute_time(3))",
)


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
def apply_failing_clock_call(monkeypatch):
    """
    Return a callable that patches in a failing system call fake that
    fails and return a list of calls to that fake.
    """

    def _apply_failing_clock_call(name, errno_value):
        calls = []

        def _failing_clock_call(clock_id, timespec):
            calls.append((clock_id, timespec))
            monkeypatch.setattr(_api.ffi, "errno", errno.EINVAL)
            return -1

        monkeypatch.setattr(_api, name, _failing_clock_call)

        return calls

    return _apply_failing_clock_call


@pytest.fixture
def apply_timespec(monkeypatch):
    """
    Return a callable that patches in a fake over the specified clock
    call that sets the specified resolution and returns a list of
    calls to that fake.
    """

    def _apply_timespec(name, goal_timespec):
        calls = []

        def _fake_clock_call(clock_id, timespec):
            calls.append((clock_id, timespec))
            timespec[0] = goal_timespec[0]
            return 0

        monkeypatch.setattr(_api, name, _fake_clock_call)

        return calls

    return _apply_timespec


class TestSimpleNamespace(object):
    """
    Tests for L{_SimpleNamespace}.
    """

    def test_init(self):
        """
        The initializer updates the instance's C{__dict__} with its
        keyword arguments.
        """
        namespace = _api._SimpleNamespace(x=1)
        assert namespace.x == 1

    def test_repr(self):
        """
        The instance's repr reflects its C{__dict__}
        """
        namespace = _api._SimpleNamespace()
        namespace.y = 2
        assert repr(namespace) == "namespace(y=2)"

    def test_eq(self):
        """
        Two instances with equal C{__dict__}s are equal.
        """
        assert _api._SimpleNamespace(a=1) == _api._SimpleNamespace(a=1)


@needs_posix
class TestGetClockInfoPosix(object):

    """
    Tests for L{get_clock_info}.
    """

    def test_non_monotonic(self):
        """
        L{get_clock_info} only knows about the monotonic clock.
        """
        with pytest.raises(ValueError):
            get_clock_info("not monotonic")

    def test_failure(self, apply_failing_clock_call, errno_value, strerror):
        """
        A failure in C{clock_getres} results in an L{OSError} that
        presents the failure's errno.
        """
        calls = apply_failing_clock_call('_clock_getres', errno_value)

        with pytest.raises(OSError) as exc:
            get_clock_info("monotonic")

        assert len(calls) == 1
        assert calls[0][0] == _bindings.lib.CLOCK_MONOTONIC

        assert str(exc.value) == strerror

    @given(
        clock_getres_spec=st.fixed_dictionaries({
            "tv_sec": st.sampled_from([0, 1]),
            "tv_nsec": st.sampled_from([0, 1]),

        }),
    )
    def test_info(self, clock_getres_spec, apply_timespec):
        """
        The reported info always includes a nanosecond resolution when
        C{clock_getres} indicates nanosecond resolution.
        """
        calls = apply_timespec(
            "_clock_getres",
            _bindings.ffi.new("struct timespec *", clock_getres_spec),
        )

        expected_info = _api._SimpleNamespace(
            adjustable=False,
            implementation="clock_gettime(MONOTONIC)",
            monotonic=True,
            resolution=None,    # checked separately
        )

        if clock_getres_spec['tv_nsec']:
            expected_resolution = 1e-09
        else:
            expected_resolution = 1.0

        info = get_clock_info("monotonic")
        resolution, info.resolution = info.resolution, None

        assert info == expected_info
        assert resolution - expected_resolution == pytest.approx(0.0)

        assert len(calls) == 1
        assert calls[0][0] == _bindings.lib.CLOCK_MONOTONIC


@needs_macos
class TestGetClockInfoMacOS(object):
    """
    Tests for L{get_clock_info}.
    """

    def test_non_monotonic(self):
        """
        L{get_clock_info} only knows about the monotonic clock.
        """
        with pytest.raises(ValueError):
            get_clock_info("not monotonic")

    def test_info(self):
        """
        The reported info always includes a nanosecond resolution.
        """

        expected_info = _api._SimpleNamespace(
            adjustable=False,
            implementation="mach_absolute_time()",
            monotonic=True,
            resolution=None,    # checked separately
        )

        expected_resolution = 1e-09

        info = get_clock_info("monotonic")
        resolution, info.resolution = info.resolution, None

        assert info == expected_info
        assert resolution - expected_resolution == pytest.approx(0.0)


@needs_posix
def test_monotonic_fails_posix(apply_failing_clock_call,
                               errno_value,
                               strerror):
    """
    A failure in C{clock_gettime} results in an L{OSError} that
    presents the failure's errno.
    """
    calls = apply_failing_clock_call('_clock_gettime', errno_value)

    with pytest.raises(OSError) as exc:
        monotonic()

    assert len(calls) == 1
    assert calls[0][0] == _bindings.lib.CLOCK_MONOTONIC

    assert str(exc.value) == strerror


@needs_posix
@given(
    clock_gettime_spec=st.fixed_dictionaries({
        "tv_sec": st.integers(min_value=0, max_value=2 ** 32 - 1),
        "tv_nsec": st.integers(min_value=0, max_value=2 ** 32 - 1),

    }),
)
def test_clock(clock_gettime_spec, apply_timespec):
    """
    For any given time resolution, the monotonic time equals the
    sum of the seconds and nanoseconds.
    """
    clock_gettime_calls = apply_timespec(
        '_clock_gettime',
        _bindings.ffi.new("struct timespec *", clock_gettime_spec),
    )

    # we a float, representing the current seconds plus the
    # nanoseconds (offset by a billion) iff the resolution is accurate
    # to the nanosecond.
    expected = float(clock_gettime_spec['tv_sec']) + (
        clock_gettime_spec['tv_nsec'] * 1e-09)

    result = monotonic()

    assert result - expected == pytest.approx(0.0)

    assert clock_gettime_calls[0][0] == _bindings.lib.CLOCK_MONOTONIC


def test_clock_increases():
    """
    A monotonic moment is never greater than a succeeding monotonic
    moment.
    """
    assert monotonic() <= monotonic()
