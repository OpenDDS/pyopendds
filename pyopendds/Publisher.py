from __future__ import annotations
from typing import TYPE_CHECKING

from .Topic import Topic
if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant
    from .DataWriter import DataWriter


class Publisher:

    def __init__(self, participant: DomainParticipant, qos=None, listener=None):
        participant.publishers.append(self)
        self.qos = qos
        self.listener = listener
        self.writers: list[DataWriter] = []

        from _pyopendds import create_publisher
        create_publisher(self, participant)

    def create_datawriter(self, topic: Topic, qos=None, listener=None):
        pass
