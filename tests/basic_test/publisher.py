import sys
import time
from datetime import timedelta

from pyopendds import \
    init_opendds, DomainParticipant, StatusKind, PyOpenDDS_Error
from pybasic.basic import Reading, ReadingKind

if __name__ == "__main__":
    try:
        # Initialize OpenDDS and Create DDS Entities
        init_opendds(opendds_debug_level=1)
        time.sleep(1)
        domain = DomainParticipant(34)
        time.sleep(1)
        topic = domain.create_topic('Readings', Reading)
        time.sleep(1)
        publisher = domain.create_publisher()
        time.sleep(1)
        writer = publisher.create_datawriter(topic)
        time.sleep(1)

        # Wait for Subscriber to Connect
        print('Waiting for Subscriber...')
        writer.wait_for(StatusKind.PUBLICATION_MATCHED, timedelta(seconds=60))
        print('Found subscriber!')

        write_sample_speed = Reading()
        write_sample_accel = Reading()
        write_sample_dist = Reading()
        while True:
            time.sleep(1)
            write_sample_speed.kind = ReadingKind.speed
            write_sample_speed.value = 123
            write_sample_speed.where = "somewhere"
            # Read and Print Sample
            rc = writer.write(write_sample_speed)
            print(rc)

            time.sleep(1)
            write_sample_accel.kind = ReadingKind.acceleration
            write_sample_accel.value = 2
            write_sample_accel.where = "everywhere"
            # Read and Print Sample
            rc = writer.write(write_sample_accel)
            print(rc)

            time.sleep(1)
            write_sample_dist.kind = ReadingKind.distance
            write_sample_dist.value = 543
            write_sample_dist.where = "anywhere"
            # Read and Print Sample
            rc = writer.write(write_sample_dist)
            print(rc)
            print('Done!')

    except PyOpenDDS_Error as e:
        sys.exit(e)
