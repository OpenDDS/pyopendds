from _pyopendds import create_publisher
from .Topic import Topic

class Publisher:

  def __init__(self, participant: 'DomainParticipant', qos=None, listener=None):
    participant.publishers.append(self)
    self.qos = qos
    self.listener = listener
    self.writers = []

    create_publisher(self, participant)

  def create_datawriter(self, topic: Topic, qos=None, listener=None):
    pass
