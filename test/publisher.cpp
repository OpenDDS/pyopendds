#include <iostream>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DdsDcpsPublicationC.h>
#include <dds/DCPS/Marked_Default_Qos.h>
#include <dds/DCPS/Service_Participant.h>

#include <dds/DCPS/WaitSet.h>

#include "build/ReadingTypeSupportImpl.h"

int main(int argc, char* argv[]) {

  try {

    // Init OpenDDS
    DDS::DomainParticipantFactory_var opendds = TheParticipantFactoryWithArgs(argc, argv);

    DDS::DomainParticipantQos part_qos;
    opendds->get_default_participant_qos(part_qos);
    DDS::DomainParticipant_var participant = opendds->create_participant(
      34, part_qos, DDS::DomainParticipantListener::_nil(),
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!participant.in()) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    Test::ReadingTypeSupport_var ts = new Test::ReadingTypeSupportImpl();
    if (ts->register_type(participant.in(), "") != DDS::RETCODE_OK) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    CORBA::String_var type_name = ts->get_type_name();
    DDS::Topic_var topic = participant->create_topic(
      "Readings", type_name.in(), TOPIC_QOS_DEFAULT, 0,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK
    );

    if (!topic.in()) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    DDS::Publisher_var publisher = participant->create_publisher(
      PUBLISHER_QOS_DEFAULT, 0,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK
    );

    if (!publisher.in()) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    DDS::DataWriterQos qos;
    publisher->get_default_datawriter_qos(qos);
    DDS::DataWriter_var writer = publisher->create_datawriter(
      topic.in(), qos, 0,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK
    );

    if (!writer.in()) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    std::cout << "Wating for Subscriber..." << std::endl;
    DDS::StatusCondition_var sc = writer->get_statuscondition();
    sc->set_enabled_statuses(DDS::PUBLICATION_MATCHED_STATUS);
    DDS::WaitSet_var ws = new DDS::WaitSet;
    ws->attach_condition(sc);
    DDS::Duration_t infinite = {DDS::DURATION_INFINITE_SEC, DDS::DURATION_INFINITE_NSEC};
    DDS::PublicationMatchedStatus status;
    while (
      writer->get_publication_matched_status(status) == DDS::RETCODE_OK
    ) {
      DDS::ConditionSeq active;
      if (ws->wait(active, infinite) != DDS::RETCODE_OK) {
        std::cerr << "Failed" << std::endl;
        return 1;
      }
    }
    ws->detach_condition(sc);

    Test::ReadingDataWriter_var reading_writer = Test::ReadingDataWriter::_narrow(writer);
    Test::Reading reading;
    reading.value = -200;
    reading.location = Test::B;
    if (reading_writer->write(reading, DDS::HANDLE_NIL) != DDS::RETCODE_OK) {
      std::cerr << "Failed" << std::endl;
      return 1;
    }

    participant->delete_contained_entities();
    opendds->delete_participant(participant.in());
    TheServiceParticipant->shutdown();

  } catch (const CORBA::Exception& e) {
    e._tao_print_exception("Exception caught in main():");
    return 1;
  }

  return 0;
}
