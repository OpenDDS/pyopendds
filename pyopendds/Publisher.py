from __future__ import annotations

from .Topic import Topic

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant


class Publisher:

    def __init__(self, participant: DomainParticipant, qos=None, listener=None):
        participant.publishers.append(self)
        self.qos = qos
        self.listener = listener
        self.writers = []

        from _pyopendds import create_publisher
        create_publisher(self, participant)

    def create_datawriter(self, topic: Topic, qos=None, listener=None):
        pass
