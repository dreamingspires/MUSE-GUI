from typing import Generic, TypeVar

from pydantic.main import BaseModel

from muse_gui.data_defs.abstract import Data

class BaseBackDependents:
    pass

class BaseForwardDependents:
    pass

ModelType = TypeVar("ModelType", bound =Data)
BackDependents = TypeVar("BackDependents", bound = BaseBackDependents)
ForwardDependents = TypeVar("ForwardDependents", bound = BaseForwardDependents)
class BaseDatastore(Generic[ModelType, BackDependents, ForwardDependents]):
    def create(self, model: ModelType) -> ModelType:
        raise NotImplementedError

    def update(self, key: str, model: ModelType) -> ModelType:
        raise NotImplementedError

    def read(self, key: str) -> ModelType:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def back_dependents(self, key: str) -> BackDependents:
        raise NotImplementedError

    def forward_dependents(self, key: str) -> ForwardDependents:
        raise NotImplementedError