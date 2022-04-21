from __future__ import annotations
from typing import TYPE_CHECKING, List

from .DataWriter import DataWriter
from .Topic import Topic

if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant


class Publisher:
    def __init__(self, participant: DomainParticipant, qos=None):
        participant.publishers.append(self)
        self.qos = qos
        self.writers: List[DataWriter] = []

        from _pyopendds import create_publisher

        create_publisher(self, participant)

    def create_datawriter(self, topic: Topic, qos=None) -> DataWriter:
        writer = DataWriter(self, topic, qos)
        self.writers.append(writer)
        return writer
