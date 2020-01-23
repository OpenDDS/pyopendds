from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Subscriber import Subscriber


class DataReader:

    def __init__(self, subscriber: Subscriber, topic: Topic, qos=None, listener=None):
        self.topic = topic
        self.qos = qos
        self.listener = listener
        self.subscriber = subscriber
        subscriber.readers.append(self)

        from _pyopendds import create_datareader
        create_datareader(self, subscriber, topic)

    def wait_for(self, status: StatusKind, timeout: TimeDurationType):
        from _pyopendds import datareader_wait_for
        return datareader_wait_for(self, status, *normalize_time_duration(timeout))

    def take_next_sample(self):
        return self.topic._ts_package.take_next_sample(self)
