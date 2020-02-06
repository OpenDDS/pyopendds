import sys
from datetime import timedelta

from pyopendds import \
    init_opendds, DomainParticipant, StatusKind, PyOpenDDS_Error
from pybasic.basic import Reading

if __name__ == "__main__":
    try:
        # Initialize OpenDDS and Create DDS Entities
        init_opendds(opendds_debug_level=1)
        domain = DomainParticipant(34)
        topic = domain.create_topic('Readings', Reading)
        subscriber = domain.create_subscriber()
        reader = subscriber.create_datareader(topic)

        # Wait for Publisher to Connect
        print('Waiting for Publisher...')
        reader.wait_for(StatusKind.SUBSCRIPTION_MATCHED, timedelta(seconds=5))
        print('Found Publisher!')

        # Read and Print Sample
        print(reader.take_next_sample())

        print('Done!')

    except PyOpenDDS_Error as e:
        sys.exit(e)
