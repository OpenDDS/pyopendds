from .Topic import Topic
from .Subscriber import Subscriber
from .Publisher import Publisher


class DomainParticipant:

    def __init__(self, domain: int, qos=None, listener=None):
        self.domain = int(domain)
        self.qos = qos
        self.listener = listener
        self.topics = {}
        self.subscribers = []
        self.publishers = []
        self._registered_typesupport = []

        from _pyopendds import create_participant
        create_participant(self, domain)

    def __del__(self):
        from _pyopendds import participant_cleanup
        participant_cleanup(self)

    def create_topic(self,
            name: str, topic_type: type, qos=None, listener=None) -> Topic:
        return Topic(self, name, topic_type, qos, listener)

    def create_subscriber(self, qos=None, listener=None) -> Subscriber:
        return Subscriber(self, qos, listener)

    def create_publisher(self, qos=None, listener=None) -> Publisher:
        return Publisher(self, qos, listener)
