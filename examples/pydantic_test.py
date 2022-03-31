import json

import toml

from muse_gui.backend.settings import SettingsModel

toml_struct = toml.load("example.toml")
print(json.dumps(toml_struct, indent=2))
pydantic_struct = SettingsModel.parse_obj(toml_struct)
print("#############")
# print(json.dumps(pydantic_struct.dict(), indent=2))
output_dict = pydantic_struct.dict()
print(output_dict)
print(toml.dump(output_dict, open("output.toml", "w+")))
