from .Topic import Topic
from .Subscriber import Subscriber

class DomainParticipant:

  def __init__(self, domain: int, qos=None, listener=None):
    self.domain = int(domain)
    self.qos = qos
    self.listener = listener
    self.topics = {}
    self.subscribers = []

  def create_topic(self, name: str, typename: str, qos=None, listener=None) -> Topic:
    topic = Topic(name, typename, qos, listener)
    self.topics[name] = topic
    return topic

  def create_subscriber(self, qos=None, listener=None) -> Subscriber:
    subscriber = Subscriber(qos, listener)
    self.subscribers.append(subscriber)
    return subscriber
