"""
The monotone API.
"""
from ._bindings import ffi, lib
import os

_clock_getres = lib.clock_getres
_clock_gettime = lib.clock_gettime


class _SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "namespace({})".format(", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def get_clock_info(name):
    """
    Get information on the specified clock as a namespace object.
    Supported clock names and the corresponding functions to read
    their value are:

        - C{monotonic}: L{monotonic}

    The result has the following attributes:

        - I{adjustable}: L{True} if the clock can be changed
          automatically (e.g. by a NTP daemon) or manually by the
          system administrator, L{False} otherwise

        - I{implementation}: The name of the underlying C function
          used to get the clock value

        - I{monotonic}: L{True} if the clock cannot go backward,
          L{False} otherwise resolution: The resolution of the clock
          in seconds (float)
    """
    if name != 'monotonic':
        raise ValueError("unknown clock")

    tm = ffi.new("struct timespec *")

    if _clock_getres(lib.CLOCK_MONOTONIC, tm) < 0:
        raise OSError(ffi.errno, os.strerror(ffi.errno))

    resolution = 1e-09 if tm.tv_nsec else 1.0

    return _SimpleNamespace(adjustable=False,
                            implementation="clock_gettime(MONOTONIC)",
                            monotonic=True,
                            resolution=resolution)


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

    if _clock_gettime(lib.CLOCK_MONOTONIC, tm) < 0:
        raise OSError(ffi.errno, os.strerror(ffi.errno))

    return tm.tv_sec + tm.tv_nsec * 1e-09
