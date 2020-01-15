from typing import Union, Tuple
from datetime import timedelta

DDS_Duration_t = Tuple[int, int]
TimeDurationType = Union[timedelta, DDS_Duration_t, int]


def normalize_time_duration(duration: TimeDurationType):
    if isinstance(duration, timedelta):
        seconds = duration // timedelta(seconds=1)
        nanoseconds = ((duration - timedelta(seconds=seconds)) // timedelta(microseconds=1)) * 1000
    else:
        try:
            seconds = int(duration[0])
            nanoseconds = int(duration[1])
        except Exception:
            try:
                seconds = int(duration)
                nanoseconds = 0
            except Exception:
                raise TypeError('Could not extract time from value')

    return (seconds, nanoseconds)
