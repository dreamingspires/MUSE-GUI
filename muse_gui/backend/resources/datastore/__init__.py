from typing import List, Union

from pydantic.main import BaseModel
from muse_gui.backend.data.agent import Agent
from muse_gui.backend.data.process import Capacity, CommodityFlow, Cost, Process, Technodata, Utilisation, CapacityShare

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
        def replace_path(folder_path:Path, current_path_string: str) -> str:
            return re.sub(r"{path}", str(folder_path), current_path_string)
        def path_string_to_dataframe(folder_path:Path, current_path_string: str) -> pd.DataFrame:
            return pd.read_csv(replace_path(folder_path, current_path_string))
        toml_out = toml.load(settings_path)
        path = Path(settings_path)
        folder = path.parents[0].absolute()
        settings_model =  SettingsModel.parse_obj(toml_out)

        global_commodities_data = path_string_to_dataframe(folder, settings_model.global_input_files.global_commodities)
        projections_data = path_string_to_dataframe(folder, settings_model.global_input_files.projections)
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
        for sector_name, sector in sectors.items():
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

        # Get process data from sectors
        processes = []
        for sector_name, sector in sectors.items():
            if sector.type == 'default':
                technodata_data = path_string_to_dataframe(folder, sector.technodata)
                technodata_data_without_unit = technodata_data.drop(0)
                technodata_data_unit = technodata_data.loc[0]
                
                comm_in_data = path_string_to_dataframe(folder, sector.commodities_in)
                comm_in_data_without_unit = comm_in_data.drop(0)
                comm_in_data_unit = comm_in_data.loc[0]

                comm_out_data = path_string_to_dataframe(folder, sector.commodities_out)
                comm_out_data_without_unit = comm_out_data.drop(0)
                comm_out_data_unit = comm_out_data.loc[0]
                if len(sector.subsectors) != 1:
                    raise ValueError('Only single subsector case supported')
                else:
                    subsector_name, subsector = next(iter(sector.subsectors.items()))
                agent_data = path_string_to_dataframe(folder, subsector.agents)
                existing_cap_data = path_string_to_dataframe(folder, subsector.existing_capacity)
                process_names = technodata_data_without_unit['ProcessName'].unique()
                for process_name in process_names:
                    
                    process_technodata = technodata_data_without_unit.query(f'ProcessName == "{process_name}"')
                    
                    process_comm_in = comm_in_data_without_unit.query(f'ProcessName == "{process_name}"')
                    assert len(process_comm_in) == 1
                    process_comm_in = process_comm_in.iloc[0]
                    process_comm_out = comm_out_data_without_unit.query(f'ProcessName == "{process_name}"')
                    assert len(process_comm_out) == 1
                    process_comm_out = process_comm_out.iloc[0]
                    technodatas = []
                    for i, technodata in process_technodata.iterrows():
                        print("techno", technodata)
                        technodatas.append(
                            Technodata(
                                region = technodata['RegionName'],
                                time = technodata['Time'],
                                level = technodata['Level'],
                                cost = Cost(
                                    cap_par = technodata['cap_par'],
                                    cap_exp = technodata['cap_exp'],
                                    fix_par = technodata['fix_par'],
                                    fix_exp = technodata['fix_exp'],
                                    var_par = technodata['var_par'],
                                    var_exp = technodata['var_exp'],
                                    interest_rate = technodata['InterestRate']
                                ),
                                utilisation = Utilisation(
                                    utilization_factor = technodata['UtilizationFactor'],
                                    efficiency = technodata['efficiency']
                                ),
                                capacity=Capacity(
                                    max_capacity_addition=technodata['MaxCapacityAddition'],
                                    max_capacity_growth=technodata['MaxCapacityGrowth'],
                                    total_capacity_limit=technodata['TotalCapacityLimit'],
                                    technical_life = technodata['TechnicalLife'],
                                    scaling_size= technodata['ScalingSize']
                                ),
                                agents = [
                                    CapacityShare(agent_name='Agent1', share = technodata['Agent1']),
                                    CapacityShare(agent_name='Agent2', share = technodata['Agent2']),
                                ]

                            )
                        )
                    print(process_comm_in)
                    print(process_comm_out)
                    """
                    Process(
                        name = process_technodata['ProcessName'],
                        sector = sector_name,
                        fuel = technodata_data['Fuel'],
                        end_use = technodata_data['EndUse'],
                        type = technodata_data['Type'],
                        technodatas = technodatas,
                        comm_in=[CommodityFlow(
                            commodity=process_comm_in['Commodity'],
                            region = process_comm_in['Region'],
                            timeslice = process_comm_in
                        )],
                        comm_out = [],
                        existing_capacities=[],
                        capacity_unit=''
                    )
                    """
                    raise NotImplementedError
                print(process_names)
                print("commin", comm_in_data)
                print(comm_out_data)
                print(existing_cap_data)
                
                #print(technodata_data)
                #Process
            elif sector.type == 'presets':
                print('here')
            else:
                raise TypeError(f"Sector type {sector.type} not supported")
        #Process()

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

        if len(self.commodity._data) ==0:
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

        # Create sector folders:
        sector_paths = {}
        for sector_name, sector in self.sector._data.items():
            sector_path = Path(f"{str(technodata_folder)}{os.sep}{sector.name}")
            sector_paths[sector_name] = sector_path
            if not sector_path.exists():
                sector_path.mkdir(parents=True)
            