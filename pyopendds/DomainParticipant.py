from typing import Dict, Any, List

from .Topic import Topic
from .Subscriber import Subscriber
from .Publisher import Publisher
from enum import IntEnum

try:
    from _pyopendds import participant_cleanup  # noqa
except ImportError as e:

    def participant_cleanup(*args):
        pass

    pass


class DomainParticipant:
    def __init__(self, domain: int, qos=None, listener=None, isRtpstransport=True):
        self.domain = int(domain)
        self.qos = qos
        self.listener = listener
        self.topics: Dict[str, Topic] = {}
        self.subscribers: List[Subscriber] = []
        self.publishers: List[Publisher] = []
        self._registered_typesupport: List[Any] = []

        from _pyopendds import create_participant

        create_participant(self, domain, isRtpstransport)

    def __del__(self):
        from _pyopendds import participant_cleanup

        participant_cleanup(self)

    def create_topic(
        self, name: str, topic_type: type, qos=None, listener=None
    ) -> Topic:
        return Topic(self, name, topic_type, qos, listener)

    def create_subscriber(self, qos=None, listener=None) -> Subscriber:
        return Subscriber(self, qos, listener)

    def create_publisher(self, qos=None) -> Publisher:
        return Publisher(self, qos)
