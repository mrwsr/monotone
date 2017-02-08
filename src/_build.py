"""
cffi bindings for clock_gettime(3)
"""
from cffi import FFI

import platform

ffibuilder = FFI()


if platform.system() == 'Linux':
    ffibuilder.set_source(
        "monotone._bindings",
        """
        #include <time.h>
        """,
        libraries=['rt'])

    ffibuilder.cdef("""
    typedef int... time_t;
    typedef int... clockid_t;

    const clockid_t CLOCK_MONOTONIC;

    struct timespec {
        time_t   tv_sec;        /* seconds */
        long     tv_nsec;       /* nanoseconds */
    };

    int clock_getres(clockid_t, struct timespec *);
    int clock_gettime(clockid_t, struct timespec *);
    """)
elif platform.system() == 'Darwin':
    ffibuilder.set_source(
        "monotone._bindings",
        """
        #include <mach/mach_time.h>
        """)

    ffibuilder.cdef("""
    typedef int... uint64_t;
    typedef int... uint32_t;

    typedef struct {
        uint32_t numer;
        uint32_t denom;
    } mach_timebase_info_data_t;

    int mach_timebase_info(mach_timebase_info_data_t *);
    uint64_t mach_absolute_time(void);
    """)
else:
    raise RuntimeError("Unsupported platform: {}".format(platform.system()))
