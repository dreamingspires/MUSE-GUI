from typing import List

from pydantic.main import BaseModel
from muse_gui.data_defs.agent import Agent
from muse_gui.data_defs.process import Process

from muse_gui.data_defs.sector import Sector
from muse_gui.data_defs.timeslice import AvailableYear, LevelName, Timeslice
from .process import ProcessDatastore
from .timeslice import TimesliceDatastore
from .commodity import CommodityDatastore
from .level_name import LevelNameDatastore
from .available_year import AvailableYearDatastore
from .sector import SectorDatastore
from .region import RegionDatastore
from .agent import AgentDatastore

from muse_gui.data_defs.region import Region
from muse_gui.data_defs.commodity import Commodity, CommodityPrice
import toml
from pathlib import Path
import json
import re
import csv
import pandas as pd
class SettingsModel(BaseModel):
    class Inputs(BaseModel):
        projections: str
        global_commodities: str
    global_input_files: Inputs

class Datastore:
    _region_datastore: RegionDatastore
    _sector_datastore: SectorDatastore
    _level_name_datastore: LevelNameDatastore
    _available_years_datastore: AvailableYearDatastore
    _timeslice_datastore: TimesliceDatastore
    _commodity_datastore: CommodityDatastore
    _process_datastore: ProcessDatastore
    _agent_datastore : AgentDatastore

    def __init__(
        self, 
        regions: List[Region] = [],
        sectors: List[Sector] = [],
        level_names: List[LevelName] = [],
        available_years: List[AvailableYear] = [],
        timeslices: List[Timeslice] = [],
        commodities: List[Commodity] = [],
        processes: List[Process] = [],
        agents: List[Agent] = []
    ) -> None:
        self._region_datastore = RegionDatastore(self, regions)
        self._sector_datastore = SectorDatastore(self, sectors)
        self._level_name_datastore = LevelNameDatastore(self, level_names)
        self._available_years_datastore = AvailableYearDatastore(self, available_years)
        self._timeslice_datastore = TimesliceDatastore(self, timeslices)
        self._commodity_datastore = CommodityDatastore(self, commodities)
        self._process_datastore = ProcessDatastore(self, processes)
        self._agent_datastore = AgentDatastore(self, agents)


    @property
    def region(self):
        return self._region_datastore
    
    @property
    def sector(self):
        return self._sector_datastore

    @property
    def level_name(self):
        return self._level_name_datastore

    @property
    def available_year(self):
        return self._available_years_datastore

    @property
    def timeslice(self):
        return self._timeslice_datastore
    
    @property
    def commodity(self):
        return self._commodity_datastore

    @property
    def process(self):
        return self._process_datastore
    
    @property
    def agent(self):
        return self._agent_datastore
    
    @classmethod
    def from_settings(cls, settings_path: str):
        def replace_path(folder_path:str, current_path_string: str) -> str:
            return re.sub(r"{path}", folder_path, current_path_string)

        toml_out = toml.load(settings_path)
        path = Path(settings_path)
        folder = path.parents[0].absolute()
        output_model =  SettingsModel.parse_obj(toml_out)

        global_commodities_path = replace_path(str(folder), output_model.global_input_files.global_commodities)
        global_commodities_data = pd.read_csv(global_commodities_path)
        projections_path = replace_path(str(folder), output_model.global_input_files.projections)
        projections_data = pd.read_csv(projections_path)
        regions = projections_data.drop(0)['RegionName'].unique()

        region_models = [Region(name=name) for name in regions]
        commodity_models = []
        for i, name in enumerate(global_commodities_data["Commodity"]):
            commodity = global_commodities_data.iloc[i]
            unit = projections_data[commodity['CommodityName']].iloc[0]
            rel_price_data = pd.DataFrame(projections_data.drop(0), columns=[commodity['CommodityName'], 'RegionName', 'Time'])
            commodity_prices = []
            for j, row in rel_price_data.iterrows():
                commodity_prices.append(CommodityPrice(region_name = row['RegionName'], time = row['Time'], value = row[commodity['CommodityName']]))
            com = Commodity(
                commodity=commodity['Commodity'],
                commodity_type = commodity['CommodityType'].lower(),
                commodity_name = commodity['CommodityName'],
                c_emission_factor_co2 = commodity['CommodityEmissionFactor_CO2'],
                heat_rate = commodity['HeatRate'],
                unit = commodity['Unit'],
                commodity_prices= commodity_prices,
                price_unit=unit
            )
            commodity_models.append(com)
        return cls(regions = region_models, commodities=commodity_models)
    
    def export_to_folder(self, folder_path: str):
        raise NotImplementedError
