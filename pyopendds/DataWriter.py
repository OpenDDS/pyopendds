from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Publisher import Publisher


class DataWriter:

    def __init__(self, publisher: Publisher, topic: Topic, qos=None):
        self.topic = topic
        self.publisher = publisher
        publisher.writers.append(self)

        from _pyopendds import create_datawriter
        create_datawriter(self, publisher, topic)
        self.update_qos(qos)

    def update_qos(self, qos: DataWriterQos):
        # from _pyopendds import update_writer_qos
        # return update_writer_qos(self, qos)
        print("DataWriterr.update_qos() not implemented")
        pass

    def wait_for(self, timeout: TimeDurationType, status: StatusKind = StatusKind.PUBLICATION_MATCHED):
        from _pyopendds import datawriter_wait_for
        datawriter_wait_for(self, status, *normalize_time_duration(timeout))

    def write(self, sample):
        return self.topic._ts_package.write(self, sample)
