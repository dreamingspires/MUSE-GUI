from muse_gui.backend.data.region import Region
from muse_gui.backend.data.timeslice import LevelName, Timeslice
from muse_gui.backend.resources import Datastore

data_store = Datastore.from_settings("./example_data2/settings.toml")
data_store.export_to_folder("./Output/Test")
# data_store = Datastore.from_settings('./Output/Test/settings.toml')
# data_store.export_to_folder('./Output/Test')
# data_store = Datastore.from_settings('./Output/Test/settings.toml')
# print(data_store.run_settings)
data_store.run_muse()
