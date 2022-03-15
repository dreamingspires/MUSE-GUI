from typing import Type
from .base import BaseDatastore


class KeyAlreadyExists(ValueError):
    def __init__(self, key:str, datastore: BaseDatastore) -> None:
        super().__init__(f"{key} already exists in {datastore.__class__.__name__}")

class KeyNotFound(ValueError):
    def __init__(self, key:str, datastore: BaseDatastore) -> None:
        super().__init__(f"{key} not found in {datastore.__class__.__name__}")

class DependentNotFound(ValueError):
    def __init__(self, parent_model, dependent_key, dependent_datastore: BaseDatastore) -> None:
        pass