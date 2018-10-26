import sys
import os

from pyopendds import *

DOMAIN = 34
TOPIC_NAME = 'Readings'
TOPIC_TYPE = 'Test::Reading'

if __name__ == "__main__":
  try:
    init_opendds('-DCPSConfigFile', 'rtps.ini', '-DCPSDebugLevel', '10')

    part = DomainParticipant(DOMAIN)
    topic = part.create_topic(TOPIC_NAME, TOPIC_TYPE)
    sub = part.create_subscriber()
    dr = sub.create_datareader(topic)

    # TODO: wait for publication

    # TODO: wait for message

    # TODO: take and print

  except PyOpenDDS_Error as e:
    sys.exit(e)
