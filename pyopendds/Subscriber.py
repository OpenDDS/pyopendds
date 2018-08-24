from .DataReader import DataReader
from .Topic import Topic

class Subscriber:

  def __init__(self, qos=None, listener=None):
    self.qos = qos
    self.listener = listener
    self.readers = []

  def create_datareader(self, topic: Topic, qos=None, listener=None):
    reader = DataReader(topic, qos, listener)
    self.readers.append(reader)
    return reader
