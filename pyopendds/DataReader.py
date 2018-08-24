from .Topic import Topic

class DataReader:

  def __init__(self, topic: Topic, qos=None, listener=None):
    self.topic = topic
    self.qos = qos
    self.listener = listener

