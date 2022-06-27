from __future__ import annotations

from _pyopendds import create_datareaderlistenerimpl # noqa
from typing import Callable

class DataReaderListenerImpl:
    def __init__(
        self,
        callback: Callable[...]):
        self.callback = callback

        create_datareaderlistenerimpl(self, callback)

    def __del__(self):
        print("DELETE", self)

    def clear(self):
        print("clear",self)
        self.callback = None