from _pyopendds import create_datareader
from .Topic import Topic

class DataReader:

  def __init__(self, subscriber: 'Subscriber', topic: Topic, qos=None, listener=None):
    self.topic = topic
    self.qos = qos
    self.listener = listener
    self.subscriber = subscriber
    subscriber.readers.append(self)

    create_datareader(self, subscriber, topic)

