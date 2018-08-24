import sys
import os

from pyopendds import *

if __name__ == "__main__":
  try:
    init_opendds('-DCPSDebugLevel', '10')

    participant = DomainParticipant(4)
    topic = participant.create_topic(
      'Movie Discussion List', 'Messenger::Message')
    sub = participant.create_subscriber()
    dr = sub.create_datareader(topic)

    # TODO: wait for publication

    # TODO: wait for message

    # TODO: take and print

  except PyOpenDDS_Error as e:
    sys.exit(e)
