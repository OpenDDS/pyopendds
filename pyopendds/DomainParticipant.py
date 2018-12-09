from _pyopendds import create_participant, participant_cleanup
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

    create_participant(self, domain)

  def __del__(self):
    participant_cleanup(self)

  def create_topic(self, name: str, typename: str, qos=None, listener=None) -> Topic:
    return Topic(self, name, typename, qos, listener)

  def create_subscriber(self, qos=None, listener=None) -> Subscriber:
    return Subscriber(self, qos, listener)

  def create_publisher(self, qos=None, listener=None) -> Publisher:
    return Publisher(self, qos, listener)

