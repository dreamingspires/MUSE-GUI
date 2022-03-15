from typing import Generic, TypeVar

from pydantic.main import BaseModel

ModelType = TypeVar("ModelType", bound =BaseModel)
class BaseDatastore(Generic[ModelType]):
    def create(self, model: ModelType) -> ModelType:
        raise NotImplementedError

    def update(self, key: str, model: ModelType) -> ModelType:
        raise NotImplementedError

    def read(self, key: str) -> ModelType:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def dependents(self, key: str):
        raise NotImplementedError
