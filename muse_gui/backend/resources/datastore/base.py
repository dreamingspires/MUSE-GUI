from typing import Dict, Generic, List, TypeVar

from pydantic.main import BaseModel

from muse_gui.data_defs.abstract import Data
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class BaseBackDependents(BaseModel):
    pass

class BaseForwardDependents(BaseModel):
    pass

def combine_dicts(model_store: List[Dict[str,List[str]]]) -> Dict[str,List[str]]:
    new_dict = {}
    for item in model_store:
        for attr_name, values in item.items():
            if attr_name in new_dict:
                existing_attrs = new_dict[attr_name]
                unique_attrs = list(set(existing_attrs+values))
                new_dict[attr_name] = unique_attrs
            else:
                new_dict[attr_name] = values
    return new_dict


ModelType = TypeVar("ModelType", bound =Data)
BackDependents = TypeVar("BackDependents", bound = BaseBackDependents)
ForwardDependents = TypeVar("ForwardDependents", bound = BaseForwardDependents)
class BaseDatastore(Generic[ModelType, BackDependents, ForwardDependents]):
    _parent: "Datastore"
    def create(self, model: ModelType) -> ModelType:
        raise NotImplementedError

    def update(self, key: str, model: ModelType) -> ModelType:
        raise NotImplementedError

    def read(self, key: str) -> ModelType:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def list(self) -> List[str]:
        raise NotImplementedError

    def back_dependents(self, model: ModelType) -> BackDependents:
        raise NotImplementedError

    def forward_dependents(self, model: ModelType) -> ForwardDependents:
        raise NotImplementedError
    
    def back_dependents_recursive(self, model: ModelType) -> Dict[str,List[str]]:
        model_store = []
        def get_model_back_deps(rel_object, item) -> None:
            backs = rel_object.back_dependents(item)
            backs_dict = backs.dict()

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