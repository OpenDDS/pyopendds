from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration
from .Qos import DataWriterQos

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Publisher import Publisher


class DataWriter:

    def __init__(self, publisher: Publisher, topic: Topic, qos=None):
        self.topic = topic
        self.publisher = publisher
        self.qos = qos
        self.update_qos(qos)
        publisher.writers.append(self)

        from _pyopendds import create_datawriter # noqa
        create_datawriter(self, publisher, topic)

    def update_qos(self, qos: DataWriterQos):
        # TODO: Call cpp binding to implement QoS
        # return update_writer_qos(self, qos)
        pass

    def wait_for(self, timeout: TimeDurationType, status: StatusKind = StatusKind.PUBLICATION_MATCHED):
        from _pyopendds import datawriter_wait_for # noqa
        datawriter_wait_for(self, status, *normalize_time_duration(timeout))

    def write(self, sample) -> int:
        return self.topic.ts_package.write(self, sample)
