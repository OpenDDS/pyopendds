from .Topic import Topic
from .Subscriber import Subscriber
from .Publisher import Publisher
from _pyopendds import participant_cleanup, create_participant


class DomainParticipant:

    def __init__(self, domain: int, qos=None, listener=None):
        self.domain = int(domain)
        self.qos = qos
        self.listener = listener
        self.topics = {}
        self.subscribers = []
        self.publishers = []
        self._registered_typesupport = []

        create_participant(self, domain)

    def __del__(self):
        participant_cleanup(self)

    def create_topic(self,
                     name: str, topic_type: type, qos=None, listener=None) -> Topic:
        return Topic(self, name, topic_type, qos, listener)

    def create_subscriber(self, qos=None, listener=None) -> Subscriber:
        return Subscriber(self, qos, listener)

    def create_publisher(self, qos=None) -> Publisher:
        return Publisher(self, qos)
