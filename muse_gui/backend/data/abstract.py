from pydantic import BaseModel


class Data(BaseModel):
    class Config:
        use_enum_values = True
