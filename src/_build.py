"""
cffi bindings for clock_gettime(3)
"""
from cffi import FFI

ffibuilder = FFI()


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
