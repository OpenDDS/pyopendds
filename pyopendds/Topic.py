from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .DomainParticipant import DomainParticipant


class Topic:

    def __init__(self,
            participant: DomainParticipant, name: str, topic_type: type,
            qos=None, listener=None):
        participant.topics[name] = self
        self.name = name
        self.type = topic_type
        self.qos = qos
        self.listener = listener

        # Get OpenDDS Topic Type Name
        import importlib
        self._ts_package = \
            importlib.import_module(
                topic_type._pyopendds_typesupport_packge_name)
        if topic_type not in participant._registered_typesupport:
            self._ts_package.register_type(participant, topic_type)
        self.type_name = self._ts_package.type_name(topic_type)

        from _pyopendds import create_topic
        create_topic(self, participant, name, self.type_name)
