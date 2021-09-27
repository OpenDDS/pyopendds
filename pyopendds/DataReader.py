from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration

from typing import TYPE_CHECKING, Callable, Optional
if TYPE_CHECKING:
    from .Subscriber import Subscriber


class DataReader:

    def __init__(self, subscriber: Subscriber, topic: Topic, qos=None, listener: Optional[Callable[..., None]] = None):
        self.topic = topic
        self.listener = listener
        self.subscriber = subscriber
        subscriber.readers.append(self)

        from _pyopendds import create_datareader
        create_datareader(self, subscriber, topic, self.on_data_available_callback)
        self.update_qos(qos)

    def update_qos(self, qos: DataReaderQos):
        # from _pyopendds import update_reader_qos
        # return update_reader_qos(self, qos)
        print("DataReader.update_qos() not implemented")
        pass

    def wait_for(self, timeout: TimeDurationType, status: StatusKind = StatusKind.SUBSCRIPTION_MATCHED):
        from _pyopendds import datareader_wait_for
        datareader_wait_for(self, status, *normalize_time_duration(timeout))

    def take_next_sample(self):
        return self.topic._ts_package.take_next_sample(self)

    def on_data_available_callback(self):
        sample = self.take_next_sample()
        if sample is None:
            print("on_data_available_callback error: sample is None")
        elif self.listener is not None:
            self.listener(sample)
