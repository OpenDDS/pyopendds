from __future__ import annotations

from .DataReader import DataReader
from .Topic import Topic

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant


class Subscriber:

    def __init__(self, participant: DomainParticipant, qos=None, listener=None):
        participant.subscribers.append(self)
        self.qos = qos
        self.listener = listener
        self.readers = []

        from _pyopendds import create_subscriber
        create_subscriber(self, participant)

    def create_datareader(self, topic: Topic, qos=None, listener=None):
        return DataReader(self, topic, qos, listener)
