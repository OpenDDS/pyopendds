import sys

from pyopendds import Config, DomainParticipant, StatusKind, PyOpenDDS_Error
import pybasic

debug = False

if __name__ == "__main__":
    try:
        # Initialize OpenDDS and Create DDS Objects
        with Config() as cfg:
            cfg.opendds_debug_level(1)
        part = DomainParticipant(34)
        topic = part.create_topic('Readings', pybasic.basic.Reading)
        sub = part.create_subscriber()
        dr = sub.create_datareader(topic)

        # Wait for Publisher to Connect
        print('Waiting for Publisher...')
        dr.wait_for(StatusKind.SUBSCRIPTION_MATCHED, 15)
        print('Found Publisher!')

        # Read and Print Sample
        print(dr.read())

        print('Done!')

    except PyOpenDDS_Error as e:
        sys.exit(e)
