"""
The monotone API.
"""
from ._bindings import ffi, lib
import os
import platform


class _SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "namespace({})".format(", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


if platform.system() == "Darwin":
    _mach_timebase_info = lib.mach_timebase_info
    _mach_absolute_time = lib.mach_absolute_time

    def get_clock_info(name):
        if name != 'monotonic':
            raise ValueError("unknown clock")

        return _SimpleNamespace(adjustable=False,
                                implementation="mach_absolute_time()",
                                monotonic=True,
                                resolution=1e-09)

    def monotonic():
        ti = ffi.new("mach_timebase_info_data_t *")

        # According to the Technical Q&A QA1398, mach_timebase_info()
        # cannot fail:
        # https://developer.apple.com/library/mac/#qa/qa1398/
        _mach_timebase_info(ti)

        time = _mach_absolute_time()
        time *= ti.numer
        time /= ti.denom

        return time * 1e-09
elif os.name == "posix":
    _clock_getres = lib.clock_getres
    _clock_gettime = lib.clock_gettime
    CLOCK_MONOTONIC = lib.CLOCK_MONOTONIC

    def get_clock_info(name):
        if name != 'monotonic':
            raise ValueError("unknown clock")

        tm = ffi.new("struct timespec *")

        if _clock_getres(CLOCK_MONOTONIC, tm) < 0:
            raise OSError(ffi.errno, os.strerror(ffi.errno))

        resolution = 1e-09 if tm.tv_nsec else 1.0

        return _SimpleNamespace(adjustable=False,
                                implementation="clock_gettime(MONOTONIC)",
                                monotonic=True,
                                resolution=resolution)

    def monotonic():
        tm = ffi.new("struct timespec *")

        if _clock_gettime(CLOCK_MONOTONIC, tm) < 0:
            raise OSError(ffi.errno, os.strerror(ffi.errno))

        return tm.tv_sec + tm.tv_nsec * 1e-09

else:
    raise RuntimeError("Unsupported platform: {}".format(platform.system()))


get_clock_info.__doc__ = """
Get information on the specified clock as a namespace object.
Supported clock names and the corresponding functions to read their
value are:

    - C{monotonic}: L{monotonic}

The result has the following attributes:

    - I{adjustable}: L{True} if the clock can be changed automatically
      (e.g. by a NTP daemon) or manually by the system administrator,
      L{False} otherwise

    - I{implementation}: The name of the underlying C function used to
      get the clock value

    - I{monotonic}: L{True} if the clock cannot go backward, L{False}
      otherwise resolution: The resolution of the clock in seconds
      (float)
"""

monotonic.__doc__ = """
Return fractional seconds from a monotonic clock.  The returned moment
is useful only in comparison to other identical moments.  Monotonic
clocks should never be subject to leap seconds or other clock skews.

@return: A comparable moment from a monotonic clock.
@rtype: L{float}
"""
