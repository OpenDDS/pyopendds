from typing import Dict, Any, List

from .Topic import Topic
from .Subscriber import Subscriber
from .Publisher import Publisher
from enum import IntEnum

from _pyopendds import create_participant, participant_cleanup


class DomainParticipant:
    def __init__(self, domain: int, qos=None, listener=None, isRtpstransport=True):
        self.domain = int(domain)
        self.qos = qos
        self.listener = listener
        self.topics: Dict[str, Topic] = {}
        self.subscribers: List[Subscriber] = []
        self.publishers: List[Publisher] = []
        self._registered_typesupport: List[Any] = []

        create_participant(self, domain, isRtpstransport)

    def stop(self):
        participant_cleanup(self)

    def clear(self):
        for topic in self.topics.values():
            topic.clear()
        self.topics.clear()
        
        for pub in self.publishers:
            pub.clear()
        self.publishers.clear()

        for sub in self.subscribers:
            sub.clear()
        self.subscribers.clear()
        
        self.listener = None
        
    def create_topic(
        self, name: str, topic_type: type, qos=None, listener=None
    ) -> Topic:
        return Topic(self, name, topic_type, qos, listener)

    def create_subscriber(self, qos=None, listener=None) -> Subscriber:
        return Subscriber(self, qos, listener)

    def create_publisher(self, qos=None) -> Publisher:
        return Publisher(self, qos)
