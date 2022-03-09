import sys
import time
from datetime import timedelta
from pyopendds.Qos import DataReaderQos

from pyopendds import (
    opendds_version_dict,
    init_opendds,
    DomainParticipant,
    StatusKind,
    PyOpenDDS_Error,
)
from pybasic.basic import Reading


class TestClass:
    def listener_func(self, sample: Reading):
        print("main callback !", file=sys.stderr)
        print(sample)
        # todo: investigate the need of this sleep
        time.sleep(1)


if __name__ == "__main__":
    print('OpenDDS Version is:', opendds_version_dict())
    try:
        listener = TestClass()
        # Initialize OpenDDS and Create DDS Entities
        init_opendds(opendds_debug_level=10)
        domain = DomainParticipant(34)
        topic = domain.create_topic('Readings', Reading)
        subscriber = domain.create_subscriber()
        # Change qos testing
        datareaderqos = DataReaderQos()
        datareaderqos.history.depth = 2
        print("test subscriber")
        print(datareaderqos)
        print(datareaderqos.durability.kind)
        reader = subscriber.create_datareader(topic=topic, qos =datareaderqos, listener=listener.listener_func)

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
