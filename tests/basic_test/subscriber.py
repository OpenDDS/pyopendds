import sys
import os

from pyopendds import *
import pybasic

DOMAIN = 34
TOPIC_NAME = 'Readings'

if __name__ == "__main__":
  try:
    # Initialize OpenDDS
    init_opendds('-DCPSConfigFile', 'rtps.ini', '-DCPSDebugLevel', '10')

    # Create DDS Objects
    part = DomainParticipant(DOMAIN)
    topic = part.create_topic(pybasic.basic.Reading, TOPIC_NAME)
    sub = part.create_subscriber()
    dr = sub.create_datareader(topic)

    pub = part.create_publisher()

    # Wait for Publisher to Connect
    dr.wait_for(StatusKind.PUBLICATION_MATCHED, 15)

    # TODO: wait for message

    # TODO: take and print

    print('Done!')

  except PyOpenDDS_Error as e:
    sys.exit(e)
