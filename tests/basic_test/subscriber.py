import sys
import time
from datetime import timedelta

from pyopendds import \
    init_opendds, DomainParticipant, StatusKind, PyOpenDDS_Error
from pybasic.basic import Reading


class TestClass:
    def listener_func(self, sample: Reading):
        print("main callback !", file=sys.stderr)
        print(sample)
        # todo: investigate the need of this sleep
        time.sleep(1)


if __name__ == "__main__":
    try:
        listener = TestClass()
        # Initialize OpenDDS and Create DDS Entities
        init_opendds(opendds_debug_level=10)
        domain = DomainParticipant(34)
        topic = domain.create_topic('Readings', Reading)
        subscriber = domain.create_subscriber()
        reader = subscriber.create_datareader(topic=topic, listener=listener.listener_func)

        # Wait for Publisher to Connect
        print('Waiting for Publisher...')
        reader.wait_for(StatusKind.SUBSCRIPTION_MATCHED, timedelta(seconds=30))
        print('Found Publisher!')

        # Read and Print Sample
        # print(reader.take_next_sample())
        time.sleep(60)

        print('Done!')

    except Exception as e:
        sys.exit(e)
