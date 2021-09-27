from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration
from .Qos import DataReaderQos

from typing import TYPE_CHECKING, Callable, Optional
if TYPE_CHECKING:
    from .Subscriber import Subscriber


class DataReader:

    def __init__(self, subscriber: Subscriber, topic: Topic, qos=None, listener: Optional[Callable[..., None]] = None):
        self.topic = topic
        self.listener = listener
        self.subscriber = subscriber
        self.qos = qos
        self.update_qos(qos)
        subscriber.readers.append(self)

        from _pyopendds import create_datareader # noqa
        create_datareader(self, subscriber, topic, self.on_data_available_callback)

    def update_qos(self, qos: DataReaderQos):
        # TODO: Call cpp binding to implement QoS
        # return update_reader_qos(self, qos)
        pass

    def wait_for(self, timeout: TimeDurationType, status: StatusKind = StatusKind.SUBSCRIPTION_MATCHED):
        from _pyopendds import datareader_wait_for # noqa
        datareader_wait_for(self, status, *normalize_time_duration(timeout))

    def take_next_sample(self):
        return self.topic.ts_package.take_next_sample(self)

    def on_data_available_callback(self):
        sample = self.take_next_sample()
        if sample is None:
            # print("on_data_available_callback error: sample is None")
            pass
        elif self.listener is not None:
            self.listener(sample)
