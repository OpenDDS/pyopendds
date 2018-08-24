class Topic:

  def __init__(self, name: str, typename: str, qos=None, listener=None):
    self.name = name
    self.typename = typename
    self.qos = qos
    self.listener = listener

