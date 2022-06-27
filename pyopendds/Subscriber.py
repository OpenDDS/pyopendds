from __future__ import annotations
from typing import TYPE_CHECKING, List

from .DataReader import DataReader
from .Topic import Topic

if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant

from _pyopendds import create_subscriber

class Subscriber:
    def __init__(self, participant: DomainParticipant, qos=None, listener=None):
        participant.subscribers.append(self)
        self.qos = qos
        self.listener = listener
        self.readers: List[DataReader] = []

        create_subscriber(self, participant)

    def create_datareader(
        self, topic: Topic, qos=None, listener=None, context=None
    ) -> DataReader:
        reader = DataReader(self, topic, qos, listener, context=context)
        self.readers.append(reader)
        return reader

    def clear(self):
        # remove references to callbacks
        self.listener = None
        for reader in self.readers:
            reader.clear()
        self.readers.clear()
