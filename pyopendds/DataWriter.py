from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Publisher import Publisher


class DataWriter(object):

    def __init__(self, publisher: Publisher, topic: Topic, qos=None, listener=None):
        self.topic = topic
        self.qos = qos
        self.listener = listener
        self.publisher = publisher
        publisher.writers.append(self)

        from _pyopendds import create_datawriter
        create_datawriter(self, publisher, topic)

    def wait_for(self, status: StatusKind, timeout: TimeDurationType):
        from _pyopendds import datareader_wait_for
        return datareader_wait_for(self, status, *normalize_time_duration(timeout))

    def write(self, sample):
        return self.topic._ts_package.write(self, sample)
