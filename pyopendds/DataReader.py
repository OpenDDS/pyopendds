from _pyopendds import create_datareader, datareader_wait_for
from .Topic import Topic
from .constants import StatusKind

class DataReader:

  def __init__(self, subscriber: 'Subscriber', topic: Topic, qos=None, listener=None):
    self.topic = topic
    self.qos = qos
    self.listener = listener
    self.subscriber = subscriber
    subscriber.readers.append(self)

    create_datareader(self, subscriber, topic)

  def wait_for(self, status: StatusKind, timeout):
    return datareader_wait_for(self, status, timeout)
