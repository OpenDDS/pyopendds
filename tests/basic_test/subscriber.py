import sys
import os

from pyopendds import *
import pybasic

if __name__ == "__main__":
  try:
    # Initialize OpenDDS
    init_opendds('-DCPSConfigFile', 'rtps.ini', '-DCPSDebugLevel', '10')

    # Create DDS Objects
    part = DomainParticipant(34)
    topic = part.create_topic('Readings', pybasic.basic.Reading)
    sub = part.create_subscriber()
    dr = sub.create_datareader(topic)

    pub = part.create_publisher()

    # Wait for Publisher to Connect
    dr.wait_for(StatusKind.SUBSCRIPTION_MATCHED, 10)

    # TODO: wait for message

    # TODO: take and print

    print('Done!')

  except PyOpenDDS_Error as e:
    sys.exit(e)
