from _pyopendds import create_topic

class Topic:

  def __init__(self,
    participant: 'DomainParticipant', name: str, typename: str,
    qos=None, listener=None
  ):
    self.name = name
    self.typename = typename
    self.qos = qos
    self.listener = listener

    create_topic(self, paricipant, name, typename)

