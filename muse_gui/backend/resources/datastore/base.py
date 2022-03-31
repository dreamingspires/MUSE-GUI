from typing import TYPE_CHECKING, Dict, Generic, List, TypeVar

from muse_gui.backend.data.abstract import Data
from muse_gui.backend.resources.datastore.exceptions import (
    KeyAlreadyExists,
    KeyNotFound,
)

if TYPE_CHECKING:
    from . import Datastore


def combine_dicts(model_store: List[Dict[str, List[str]]]) -> Dict[str, List[str]]:
    new_dict = {}
    for item in model_store:
        for attr_name, values in item.items():
            if attr_name in new_dict:
                existing_attrs = new_dict[attr_name]
                unique_attrs = list(set(existing_attrs + values))
                new_dict[attr_name] = unique_attrs
            else:
                new_dict[attr_name] = values
    return new_dict


ModelType = TypeVar("ModelType", bound=Data)


class BaseDatastore(Generic[ModelType]):
    _parent: "Datastore"
    _data: Dict[str, ModelType]
    _key_attr_name: str

    def __init__(
        self, parent: "Datastore", key_attr_name: str, data: List[ModelType] = []
    ) -> None:
        self._parent = parent
        self._key_attr_name = key_attr_name
        self._data = {}
        for item in data:
            self.create(item)

    def create(self, model: ModelType) -> ModelType:
        key = str(getattr(model, self._key_attr_name))
        if key in self._data:
            raise KeyAlreadyExists(key, self)
        else:
            self.back_dependents(model)
            self._data[key] = model
            return model

    def read(self, key: str) -> ModelType:
        if key not in self._data:
            raise KeyNotFound(key, self)
        else:
            return self._data[key]

    def update(self, existing_key: str, model: ModelType) -> ModelType:
        new_key = str(getattr(model, self._key_attr_name))
        if existing_key not in self._data:
            raise KeyNotFound(existing_key, self)
        else:
            existing = self.read(existing_key)
            self.back_dependents(existing)
            self.back_dependents(model)
            if existing_key == new_key:
                self._data[existing_key] = model
            else:
                self.create(model)
                self.delete(existing_key)
            return model

    def delete(self, key: str) -> None:
        existing = self.read(key)
        forward_deps = self.forward_dependents(existing)
        for attribute, keys in forward_deps.items():
            for k in keys:
                try:
                    relevant_method = getattr(self._parent, attribute)
                    relevant_method.delete(k)
                except KeyNotFound:
                    pass
        self._data.pop(key)
        return None

    def list(self) -> List[str]:
        return list(self._data.keys())

    def back_dependents(self, model: ModelType) -> Dict[str, List[str]]:
        return {}

    def forward_dependents(self, model: ModelType) -> Dict[str, List[str]]:
        return {}

    def back_dependents_recursive(self, model: ModelType) -> Dict[str, List[str]]:
        model_store = []

        def get_model_back_deps(rel_object, item) -> None:
            backs_dict = rel_object.back_dependents(item)
            if len(backs_dict) == 0:
                return None
            else:
                model_store.append(backs_dict)
                for k, v in backs_dict.items():
                    rel_method = getattr(self._parent, k)
                    for i in v:
                        rel_item = rel_method.read(i)
                        get_model_back_deps(rel_method, rel_item)
                return None

        get_model_back_deps(self, model)
        combined = combine_dicts(model_store)
        return combined

    def forward_dependents_recursive(self, model: ModelType) -> Dict[str, List[str]]:
        model_store = []

        def get_model_forward_deps(rel_object, item) -> None:
            backs_dict = rel_object.forward_dependents(item)
            if len(backs_dict) == 0:
                return None
            else:
                model_store.append(backs_dict)
                for k, v in backs_dict.items():
                    rel_method = getattr(self._parent, k)
                    for i in v:
                        rel_item = rel_method.read(i)
                        get_model_forward_deps(rel_method, rel_item)
                return None

        get_model_forward_deps(self, model)
        combined = combine_dicts(model_store)
        return combined
