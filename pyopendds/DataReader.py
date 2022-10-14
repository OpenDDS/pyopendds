from __future__ import annotations

from .Topic import Topic
from .DataReaderListenerImpl import DataReaderListenerImpl
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration
from .Qos import DataReaderQos

from typing import TYPE_CHECKING, Callable, Optional, Any

if TYPE_CHECKING:
    from .Subscriber import Subscriber

from _pyopendds import datareader_wait_for
from _pyopendds import create_datareader


class DataReader:
    def __init__(
        self,
        subscriber: Subscriber,
        topic: Topic,
        qos=DataReaderQos(),
        listener: Optional[Callable[..., None]] = None,
        context: Any = None,
    ):
        if listener is None:
            datareaderlistenerimpl = None
        else:
            datareaderlistenerimpl = DataReaderListenerImpl(self.on_data_available_callback)

        self.listener = listener
        self.topic = topic
        self.datareaderlistenerimpl = datareaderlistenerimpl
        self.subscriber = subscriber
        self.qos = qos
        self.context = context
        subscriber.readers.append(self)

        
        create_datareader(self, subscriber, topic, datareaderlistenerimpl, self.qos)
        
    def wait_for(
        self,
        timeout: TimeDurationType,
        status: StatusKind = StatusKind.SUBSCRIPTION_MATCHED,
    ):

        datareader_wait_for(self, status, *normalize_time_duration(timeout))

    def take_next_sample(self) -> Any:
        try:
            return self.topic.ts_package.take_next_sample(self)
        except: # we inhibit Exceptions due to wrong sample received
            return None
            
    def on_data_available_callback(self):
        sample = self.take_next_sample()
        
        if sample is None:
            return
        
        if self.listener is None:
            return
        
        if self.context is None:
            self.listener(sample)
        else:
            self.listener(sample, self.context)

    def clear(self):
        if self.datareaderlistenerimpl is not None:
            self.datareaderlistenerimpl.clear()

        self.listener = None
        self.topic = None
        self.datareaderlistenerimpl = None
        self.subscriber = None
        self.qos = None
        self.context = None