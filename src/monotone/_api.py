"""
The monotone API.
"""
from ._bindings import ffi, lib
import os

_clock_getres = lib.clock_getres
_clock_gettime = lib.clock_gettime


def monotonic():
    """
    Return fractional seconds from a monotonic clock.  The returned
    moment is useful only in comparison to other identical moments.
    Monotonic clocks should never be subject to leap seconds or other
    clock skews.

    @return: A comparable moment from a monotonic clock.
    @rtype: L{float}
    """
    tm = ffi.new("struct timespec *")

    if _clock_getres(lib.CLOCK_MONOTONIC, tm) < 0:
        raise OSError(ffi.errno, os.strerror(ffi.errno))

    has_tv_nsec = tm.tv_nsec

    if _clock_gettime(lib.CLOCK_MONOTONIC, tm) < 0:
        raise OSError(ffi.errno, os.strerror(ffi.errno))

    seconds = tm.tv_sec

    if has_tv_nsec:
        seconds += (tm.tv_nsec * 1e-09)
    else:
        seconds = float(seconds)

    return seconds
