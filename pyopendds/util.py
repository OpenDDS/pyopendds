from typing import Union, Tuple, List
from datetime import timedelta
from ctypes import c_ubyte, c_byte

DDS_Duration_t = Tuple[int, int]
TimeDurationType = Union[timedelta, DDS_Duration_t, int]


def normalize_time_duration(duration: TimeDurationType):
    if isinstance(duration, timedelta):
        seconds = duration // timedelta(seconds=1)
        nanoseconds = (
            (duration - timedelta(seconds=seconds)) // timedelta(microseconds=1)
        ) * 1000
    elif isinstance(duration, int):
        seconds = int(duration)
        nanoseconds = 0
    elif isinstance(duration, tuple):
        seconds = int(duration[0])
        nanoseconds = int(duration[1])
    else:
        raise TypeError("Could not extract time from " + repr(duration))

    return seconds, nanoseconds


class _BitwiseImpl:
    value: ...

    def __init__(self, x):
        ...

    def __int__(self) -> int:
        ...

    def __or__(self, other):
        self.value = self.value | other.value
        return self

    def __and__(self, other):
        self.value = self.value & other.value
        return self

    def __xor__(self, other):
        self.value = self.value ^ other.value
        return self

    def __ior__(self, other):
        self.value |= other.value
        return self

    def __iand__(self, other):
        self.value &= other.value
        return self

    def __ixor__(self, other):
        self.value ^= other.value
        return self

    def __invert__(self):
        self.value = ~self.value
        return self


