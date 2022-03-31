from abc import abstractmethod
from typing import List, Optional, Tuple

from PySimpleGUI import Element


def is_subset(tuple_a, tuple_b):
    return all(k in tuple_b for k in tuple_a)


class BaseWidget:
    def __init__(self, key: Optional[str] = None):
        self.key = key
        self._layout = None
        self._prefix = tuple()

    def _prefixf(self, k: Optional[str] = None):
        return self._prefix + ((k,) if k else tuple())

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, _prefix: Tuple):
        self._prefix = _prefix + ((self.key,) if self.key else tuple())

    @abstractmethod
    def layout(self, prefix, **kwargs) -> List[List[Element]]:
        raise NotImplementedError()

    @abstractmethod
    def bind_handlers(self):
        # Function to call after window gets finalized
        raise NotImplementedError()

    def should_handle_event(self, event):
        address = event[0] if event[0] and isinstance(event[0], tuple) else event
        return is_subset(self._prefixf(), address)

    def __call__(self, window, event, values):
        print(f"Unhandled event - Widget {self._prefixf()}, event {event}")
