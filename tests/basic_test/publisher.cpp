#include <basicTypeSupportImpl.h>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DdsDcpsPublicationC.h>
#include <dds/DCPS/Marked_Default_Qos.h>
#include <dds/DCPS/Service_Participant.h>
#include <dds/DCPS/WaitSet.h>
#include <dds/DCPS/DCPS_Utils.h>

#include <iostream>

using OpenDDS::DCPS::retcode_to_string;

int main(int argc, char* argv[])
{
  try {
    // Init OpenDDS
    TheServiceParticipant->default_configuration_file("rtps.ini");
    DDS::DomainParticipantFactory_var opendds = TheParticipantFactoryWithArgs(argc, argv);

    DDS::DomainParticipantQos part_qos;
    opendds->get_default_participant_qos(part_qos);
    DDS::DomainParticipant_var participant =
      opendds->create_participant(34, part_qos, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!participant) {
      std::cerr << "Error: Failed to create participant" << std::endl;
      return 1;
    }

    basic::ReadingTypeSupport_var ts = new basic::ReadingTypeSupportImpl();
    DDS::ReturnCode_t rc = ts->register_type(participant.in(), "");
    if (rc != DDS::RETCODE_OK) {
      std::cerr << "Error: Failed to register type: " << retcode_to_string(rc) << std::endl;
      return 1;
    }

    CORBA::String_var type_name = ts->get_type_name();
    DDS::Topic_var topic = participant->create_topic(
      "Readings", type_name.in(), TOPIC_QOS_DEFAULT, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!topic) {
      std::cerr << "Error: Failed to create topic" << std::endl;
      return 1;
    }

    DDS::Publisher_var publisher =
      participant->create_publisher(PUBLISHER_QOS_DEFAULT, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!publisher) {
      std::cerr << "Error: Failed to create publisher" << std::endl;
      return 1;
    }

    DDS::DataWriterQos qos;
    publisher->get_default_datawriter_qos(qos);
    DDS::DataWriter_var writer =
      publisher->create_datawriter(topic.in(), qos, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!writer) {
      std::cerr << "Error: Failed to create writer" << std::endl;
      return 1;
    }

    // Wait for Subscriber
    std::cout << "Wating for Subscriber..." << std::endl;
    DDS::StatusCondition_var sc = writer->get_statuscondition();
    sc->set_enabled_statuses(DDS::PUBLICATION_MATCHED_STATUS);
    DDS::WaitSet_var ws = new DDS::WaitSet;
    ws->attach_condition(sc);
    const DDS::Duration_t max_wait = {10, 0};
    DDS::PublicationMatchedStatus status = {0, 0, 0, 0, 0};
    while (status.current_count < 1) {
      DDS::ConditionSeq active;
      if (ws->wait(active, max_wait) != DDS::RETCODE_OK) {
        std::cerr << "Error: Timedout waiting for subscriber" << std::endl;
        return 1;
      }
      if (writer->get_publication_matched_status(status) != DDS::RETCODE_OK) {
        std::cerr << "Error: Failed to get pub matched status" << std::endl;
        return 1;
      }
    }
    ws->detach_condition(sc);
    std::cout << "Found Subscriber..." << std::endl;

    ACE_OS::sleep(1);

    // Write Sample
    basic::ReadingDataWriter_var reading_writer = basic::ReadingDataWriter::_narrow(writer);
    basic::Reading reading;
    reading.kind
#ifdef CPP11_IDL
      () = basic::ReadingKind::speed;
#else
      = basic::speed;
#endif
    reading.value
#ifdef CPP11_IDL
      ()
#endif
      = -200;
    reading.where
#ifdef CPP11_IDL
      ()
#endif
      = "Somewhere";
    rc = reading_writer->write(reading, DDS::HANDLE_NIL);
    if (rc != DDS::RETCODE_OK) {
      std::cerr << "Error: Failed to write: " << retcode_to_string(rc) << std::endl;
      return 1;
    }

    ACE_OS::sleep(1);

    // Cleanup
    participant->delete_contained_entities();
    opendds->delete_participant(participant.in());
    TheServiceParticipant->shutdown();

  } catch (const CORBA::Exception& e) {
    e._tao_print_exception("Exception caught in main():");
    return 1;
  }

  return 0;
}
