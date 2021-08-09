#include <basicTypeSupportImpl.h>

#include <dds/DdsDcpsInfrastructureC.h>
#include <dds/DdsDcpsSubscriptionC.h>
#include <dds/DCPS/Marked_Default_Qos.h>
#include <dds/DCPS/Service_Participant.h>
#include <dds/DCPS/WaitSet.h>
#include <dds/DCPS/DCPS_Utils.h>

#include "DataReaderListenerImpl.h"
#include "basicTypeSupportImpl.h"

#include <iostream>

using OpenDDS::DCPS::retcode_to_string;

int main(int argc, char* argv[]) {

  try {
    // Init OpenDDS
    TheServiceParticipant->default_configuration_file("rtps.ini");
    DDS::DomainParticipantFactory_var opendds =
      TheParticipantFactoryWithArgs(argc, argv);

    DDS::DomainParticipantQos part_qos;
    opendds->get_default_participant_qos(part_qos);
    DDS::DomainParticipant_var participant = opendds->create_participant(
      34, part_qos, 0, OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!participant) {
      std::cerr << "Error: Failed to create participant" << std::endl;
      return 1;
    }

    basic::ReadingTypeSupport_var ts = new basic::ReadingTypeSupportImpl();
    DDS::ReturnCode_t rc = ts->register_type(participant.in(), "");
    if (rc != DDS::RETCODE_OK) {
      std::cerr
        << "Error: Failed to register type: "
        << retcode_to_string(rc) << std::endl;
      return 1;
    }

    CORBA::String_var type_name = ts->get_type_name();
    DDS::Topic_var topic = participant->create_topic(
      "Readings", type_name.in(), TOPIC_QOS_DEFAULT, 0,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!topic) {
      std::cerr << "Error: Failed to create topic" << std::endl;
      return 1;
    }

    DDS::Subscriber_var subscriber = participant->create_subscriber(
      SUBSCRIBER_QOS_DEFAULT, 0,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!subscriber) {
      std::cerr << "Error: Failed to create subscriber" << std::endl;
      return 1;
    }

    DDS::DataReaderListener_var listener(new DataReaderListenerImpl);
    DDS::DataReaderQos qos;
    subscriber->get_default_datareader_qos(qos);
    DDS::DataReader_var reader = subscriber->create_datareader(
      topic.in(), qos, listener,
      OpenDDS::DCPS::DEFAULT_STATUS_MASK);
    if (!reader) {
      std::cerr << "Error: Failed to create reader" << std::endl;
      return 1;
    }
    basic::ReadingDataReader_var reader_i =
      basic::ReadingDataReader::_narrow(reader);

    if (!reader_i) {
      ACE_ERROR_RETURN((LM_ERROR,
                        ACE_TEXT("ERROR: %N:%l: main() -")
                        ACE_TEXT(" _narrow failed!\n")),
                       1);
    }

    // Wait for Subscriber
    std::cout << "Wating for Subscriber..." << std::endl;
    DDS::StatusCondition_var sc = reader->get_statuscondition();
    sc->set_enabled_statuses(DDS::SUBSCRIPTION_MATCHED_STATUS);
    DDS::WaitSet_var ws = new DDS::WaitSet;
    ws->attach_condition(sc);
    const DDS::Duration_t max_wait = {10, 0};
    DDS::SubscriptionMatchedStatus status = {0, 0, 0, 0, 0};
    while (status.current_count < 1) {
      DDS::ConditionSeq active;
      if (ws->wait(active, max_wait) != DDS::RETCODE_OK) {
        std::cerr << "Error: Timedout waiting for subscriber" << std::endl;
        return 1;
      }
      if (reader->get_subscription_matched_status(status) != DDS::RETCODE_OK) {
        std::cerr << "Error: Failed to get pub matched status" << std::endl;
        return 1;
      }
    }
    ws->detach_condition(sc);
    std::cout << "Found Publisher..." << std::endl;

    DDS::SubscriptionMatchedStatus matches;
    if (reader->get_subscription_matched_status(matches) != DDS::RETCODE_OK) {
    ACE_ERROR_RETURN((LM_ERROR,
                      ACE_TEXT("ERROR: %N:%l: main() -")
                      ACE_TEXT(" get_subscription_matched_status failed!\n")),
                     1);
    }

    DDS::ConditionSeq conditions;
    DDS::Duration_t timeout = { 60, 0 };
    if (ws->wait(conditions, timeout) != DDS::RETCODE_OK) {
    ACE_ERROR_RETURN((LM_ERROR,
                      ACE_TEXT("ERROR: %N:%l: main() -")
                      ACE_TEXT(" wait failed!\n")),
                     1);
    }

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
