from __future__ import annotations

from .Topic import Topic
from .constants import StatusKind
from .util import TimeDurationType, normalize_time_duration
from .Qos import DataReaderQos

from typing import TYPE_CHECKING, Callable, Optional, Any

if TYPE_CHECKING:
  from .Subscriber import Subscriber


class DataReader:
  def __init__(
      self,
      subscriber: Subscriber,
      topic: Topic,
      qos=DataReaderQos(),
      listener: Optional[Callable[..., None]] = None,
      context: Any = None,
  ):
    self.topic = topic
    self.listener = listener
    self.subscriber = subscriber
    self.qos = qos
    self.context = context
    subscriber.readers.append(self)

    from _pyopendds import create_datareader  # noqa

    # verify if callback is None
    if self.listener == None:
      create_datareader(self, subscriber, topic, None, self.qos)
    else:
      create_datareader(
        self, subscriber, topic, self.on_data_available_callback, self.qos
      )

  def wait_for(
      self,
      timeout: TimeDurationType,
      status: StatusKind = StatusKind.SUBSCRIPTION_MATCHED,
  ):
    from _pyopendds import datareader_wait_for  # noqa

    datareader_wait_for(self, status, *normalize_time_duration(timeout))

  def take_next_sample(self) -> Any:
    return self.topic.ts_package.take_next_sample(self)

  def on_data_available_callback(self):
    sample = self.take_next_sample()
    if sample is None:
      # print("on_data_available_callback error: sample is None")
      pass
    elif self.listener is not None:
      if self.context is None:
        self.listener(sample)
      else:
        self.listener(sample, self.context)
