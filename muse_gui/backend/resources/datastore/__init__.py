from typing import List, Union

from pydantic.main import BaseModel
from muse_gui.backend.data.agent import Agent
from muse_gui.backend.data.process import Process

from muse_gui.backend.data.sector import InterpolationType, Production, StandardSector, PresetSector, Sector
from muse_gui.backend.data.timeslice import AvailableYear, LevelName, Timeslice
from muse_gui.backend.utils import unpack_timeslice
from .process import ProcessDatastore
from .timeslice import TimesliceDatastore
from .commodity import CommodityDatastore
from .level_name import LevelNameDatastore
from .available_year import AvailableYearDatastore
from .sector import SectorDatastore
from .region import RegionDatastore
from .agent import AgentDatastore

from muse_gui.backend.data.region import Region
from muse_gui.backend.data.commodity import Commodity, CommodityPrice
import toml
from pathlib import Path
import json
import re
import csv
import pandas as pd
from muse_gui.backend.settings import SettingsModel
import os

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
        sectors: Union[List[StandardSector], List[PresetSector], List[Sector]] = [],
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
        settings_model =  SettingsModel.parse_obj(toml_out)

        global_commodities_path = replace_path(str(folder), settings_model.global_input_files.global_commodities)
        global_commodities_data = pd.read_csv(global_commodities_path)
        projections_path = replace_path(str(folder), settings_model.global_input_files.projections)
        projections_data = pd.read_csv(projections_path)
        projections_data_without_unit = projections_data.drop(0)
        regions = projections_data_without_unit['RegionName'].unique()

        region_models = [Region(name=name) for name in regions]
        commodity_models = []
        for i, name in enumerate(global_commodities_data["Commodity"]):
            commodity = global_commodities_data.iloc[i]
            unit = projections_data[commodity['CommodityName']].iloc[0]
            rel_price_data = pd.DataFrame(projections_data_without_unit, columns=[commodity['CommodityName'], 'RegionName', 'Time'])
            commodity_prices = []
            for j, row in rel_price_data.iterrows():
                commodity_prices.append(CommodityPrice(region_name = row['RegionName'], time = row['Time'], value = row[commodity['CommodityName']]))
            com = Commodity(
                commodity=commodity['Commodity'],
                commodity_type = commodity['CommodityType'].title(),
                commodity_name = commodity['CommodityName'],
                c_emission_factor_co2 = commodity['CommodityEmissionFactor_CO2'],
                heat_rate = commodity['HeatRate'],
                unit = commodity['Unit'],
                commodity_prices= commodity_prices,
                price_unit=unit
            )
            commodity_models.append(com)
        
        
        year_models = [AvailableYear(year=i) for i in projections_data_without_unit['Time']]

        sectors = settings_model.sectors
        assert sectors is not None
        
        sector_models = []
        for sector_name, sector  in sectors.items():
            if sector.type == 'default':
                new_sector = StandardSector(
                    name = sector_name,
                    priority= sector.priority,
                    interpolation= InterpolationType(sector.interpolation),
                    dispatch_production = Production(sector.dispatch_production),
                    investment_production = Production(sector.investment_production)
                )
            else:
                new_sector = PresetSector(
                    name = sector_name,
                    priority = sector.priority
                )
            sector_models.append(new_sector)
        timeslice_info = unpack_timeslice(settings_model.timeslices)
        level_name_models = [LevelName(level=i) for i in timeslice_info.level_names]
        timeslice_models = [Timeslice(name = k, value = v) for k, v in timeslice_info.timeslices.items()]
        #agent_models = Agent()



        return cls(
            regions = region_models, 
            available_years=year_models, 
            commodities=commodity_models,
            sectors = sector_models,
            level_names=level_name_models,
            timeslices = timeslice_models,
            agents = [],
            processes = []
        )
    
    def export_to_folder(self, folder_path: str):
        folder_path_obj = Path(folder_path)
        if not folder_path_obj.exists():
            folder_path_obj.mkdir(parents=True)
        input_folder = Path(f'{folder_path}{os.sep}input')
        if not input_folder.exists():
            input_folder.mkdir(parents=True)
        technodata_folder = Path(f'{folder_path}{os.sep}technodata')
        if not technodata_folder.exists():
            technodata_folder.mkdir(parents=True)
        commodities_path = f'{str(input_folder)}{os.sep}GlobalCommodities.csv'
        projections_path = f'{str(input_folder)}{os.sep}Projections.csv'

        #print(self._commodity_datastore._data)
        commodity_data = self._commodity_datastore._data
        commodities = [commodity.dict() for _, commodity in commodity_data.items()]
        # Export GlobalCommodities
        commodity_dataframe = pd.DataFrame.from_records(
            data=commodities, 
            columns=[
                'commodity', 
                'commodity_type', 
                'commodity_name',
                'c_emission_factor_co2',
                'heat_rate',
                'unit'
            ]
        )
        new_commodity_dataframe = commodity_dataframe.rename(
            columns={
                'commodity': 'Commodity', 
                'commodity_type': 'CommodityType', 
                'commodity_name': 'CommodityName',
                'c_emission_factor_co2': 'CommodityEmissionFactor_CO2',
                'heat_rate': 'HeatRate',
                'unit': 'Unit'
            }
        )
        new_commodity_dataframe.to_csv(commodities_path, index=False)
        

        #Export Projections
        
        # Make initial dataframe excluding commodity data

        if len(self._commodity_datastore._data) ==0:
            raise NotImplementedError
        else:
            _, first_element = next(iter(commodity_data.items()))
        prices = [price.dict() for price in first_element.commodity_prices]
        projections_df = pd.DataFrame.from_records(data = prices, columns = ['region_name', 'time'])
        projections_df['Attribute'] = ['CommodityPrice']*len(projections_df)
        projections_df = projections_df[['region_name', 'Attribute', 'time']]

        for _, commodity in self._commodity_datastore._data.items():
            projections_df[commodity.commodity_name] = [price.value for price in commodity.commodity_prices]

        # Construct first row
        first_row = ['Unit', '-',' Year'] + [commodity.price_unit for _, commodity in commodity_data.items()]
        headers = list(projections_df)
        new_dict = {header: [first_row[i]] for i, header in enumerate(headers)}
        first_df = pd.DataFrame(new_dict)

        projections_df = pd.concat([first_df, projections_df])
        projections_df = projections_df.rename(
            columns = {
                'region_name': 'RegionName',
                'time': 'Time'
            }
        )
        projections_df.to_csv(projections_path, index=False)

