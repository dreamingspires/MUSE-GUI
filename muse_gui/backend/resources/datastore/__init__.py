from typing import Any, Dict, List, Optional, Tuple, Union


from muse_gui.backend.data.agent import Agent
from muse_gui.backend.data.process import CommodityFlow, Cost, Demand, DemandFlow, ExistingCapacity, Process, Technodata, Utilisation, CapacityShare
from muse_gui.backend.data.run_model import RunModel

from muse_gui.backend.data.sector import InterpolationType, Production, StandardSector, PresetSector, Sector
from muse_gui.backend.data.timeslice import AvailableYear, LevelName, Timeslice
from muse_gui.backend.settings.global_input_files_model import GlobalInputFiles
from muse_gui.backend.utils import pack_timeslice, unpack_timeslice, TimesliceInfo
from .process import ProcessDatastore
from .timeslice import TimesliceDatastore
from .commodity import CommodityDatastore
from .level_name import LevelNameDatastore
from .available_year import AvailableYearDatastore
from .sector import SectorDatastore
from .region import RegionDatastore
from .agent import AgentDatastore

from muse_gui.backend.data.region import Region
from muse_gui.backend.data.commodity import Commodity
import toml
from pathlib import Path

import pandas as pd
from muse_gui.backend.settings import SettingsModel
from muse_gui.backend.settings.output import Output, Quantity, Sink
import os

from .importers import path_string_to_dataframe, get_commodities_data, get_sectors, get_agents, get_processes
from itertools import product

from muse.mca import MCA
from pathlib import Path
import os
import warnings
def replace_path_prefix(path: Path, prefix_to_replace: Path) -> str:
    absolute_path = str(path.absolute())
    prefix = str(prefix_to_replace.absolute())
    return "{path}"+f"{absolute_path[len(prefix):]}"


def agents_to_dataframe(agents: List[Agent]) -> pd.DataFrame:
    if len(agents) ==0:
        raise ValueError('Agents not defined')
    headers = ['AgentShare','Name','AgentNumber','RegionName','Objective1','Objective2','Objective3','ObjData1','ObjData2','ObjData3','Objsort1','Objsort2','Objsort3','SearchRule','DecisionMethod','Quantity','MaturityThreshold','Budget','Type']

    agents_list =[]
    for agent in agents:
        if agent.objective_2 is None:
            objective_2_objective_type = None
            objective_2_objective_data = None
            objective_2_objective_sort = None
        else:
            objective_2_objective_type = agent.objective_2.objective_type
            objective_2_objective_data = agent.objective_2.objective_data
            objective_2_objective_sort = agent.objective_2.objective_sort
        if agent.objective_3 is None:
            objective_3_objective_type = None
            objective_3_objective_data = None
            objective_3_objective_sort = None
        else:
            objective_3_objective_type = agent.objective_3.objective_type
            objective_3_objective_data = agent.objective_3.objective_data
            objective_3_objective_sort = agent.objective_3.objective_sort
        agents_list.append(
            {
                'AgentShare': agent.share,
                'Name': agent.name,
                'AgentNumber': agent.num,
                'RegionName': agent.region,
                'Objective1': agent.objective_1.objective_type,
                'Objective2': objective_2_objective_type,
                'Objective3': objective_3_objective_type,
                'ObjData1': agent.objective_1.objective_data,
                'ObjData2': objective_2_objective_data,
                'ObjData3': objective_3_objective_data,
                'Objsort1': agent.objective_1.objective_sort,
                'Objsort2': objective_2_objective_sort,
                'Objsort3': objective_3_objective_sort,
                'SearchRule': agent.search_rule,
                'DecisionMethod': agent.decision_method,
                'Quantity': agent.quantity,
                'MaturityThreshold': agent.maturity_threshold,
                'Budget': agent.budget,
                'Type': agent.type
            }
        )
    agent_df = pd.DataFrame(agents_list, columns=headers)
    return agent_df

def generate_empty_data_and_index(
    processes: List[Process], 
    region_time_level_combos: List[Tuple[str, int, str]], 
    all_commodity_names: List[str]
) -> Tuple[List[List[Union[str,float]]], List[List[str]]]:

    empty_data = []
    empty_data_index = []
    for process in processes:
        for region, time, level in region_time_level_combos:
            initial_data: List[Union[str,float]] = [
                process.name,
                region,
                time,
                level
            ]
            commod_data: List[Union[str,float]] = [0.0]*len(all_commodity_names)
            empty_data.append(initial_data+ commod_data)
            empty_data_index.append(initial_data)
    return empty_data, empty_data_index

comm_initial_headings = ['ProcessName','RegionName','Time','Level']
def data_and_location(
    datastore, 
    index, 
    process: Process, 
    commodity_flow: CommodityFlow,
    all_commodity_names
) -> Tuple[float, int, int]:
    row_index = index.index([process.name, commodity_flow.region, commodity_flow.timeslice, commodity_flow.level])
    commod_model = datastore.commodity.read(commodity_flow.commodity)
    col_index = len(comm_initial_headings)+ all_commodity_names.index(commod_model.commodity_name)
    return commodity_flow.value, row_index, col_index

class Datastore:
    _region_datastore: RegionDatastore
    _sector_datastore: SectorDatastore
    _level_name_datastore: LevelNameDatastore
    _available_years_datastore: AvailableYearDatastore
    _timeslice_datastore: TimesliceDatastore
    _commodity_datastore: CommodityDatastore
    _process_datastore: ProcessDatastore
    _agent_datastore : AgentDatastore
    run_settings: Optional[RunModel]
    def __init__(
        self, 
        regions: List[Region] = [],
        sectors: List[Sector] = [],
        level_names: List[LevelName] = [],
        available_years: List[AvailableYear] = [],
        timeslices: List[Timeslice] = [],
        commodities: List[Commodity] = [],
        processes: List[Process] = [],
        agents: List[Agent] = [],
        run_model: Optional[RunModel] = None
    ) -> None:
        self._region_datastore = RegionDatastore(self, regions)
        self._sector_datastore = SectorDatastore(self, sectors)
        self._level_name_datastore = LevelNameDatastore(self, level_names)
        self._available_years_datastore = AvailableYearDatastore(self, available_years)
        self._timeslice_datastore = TimesliceDatastore(self, timeslices)
        self._commodity_datastore = CommodityDatastore(self, commodities)
        self._agent_datastore = AgentDatastore(self, agents)
        self._process_datastore = ProcessDatastore(self, processes)
        self.run_settings = run_model


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
    
    def run_muse(self, export_path: Optional[str] = None):
        if export_path is None:
            export_path = './Output'
        export_path_obj = Path(export_path)
        export_settings_file = self.export_to_folder(str(export_path_obj))
        
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
            my_mca = MCA.factory(export_settings_file)
            my_mca.run()
        

    @classmethod
    def from_settings(cls, settings_path: str):        
        toml_out = toml.load(settings_path)
        path = Path(settings_path)
        folder = path.parents[0].absolute()
        settings_model =  SettingsModel.parse_obj(toml_out)
        global_commodities_data = path_string_to_dataframe(folder, settings_model.global_input_files.global_commodities)
        projections_data = path_string_to_dataframe(folder, settings_model.global_input_files.projections)
        projections_data_without_unit = projections_data.drop(0)
        unit_row = projections_data.iloc[0]

        regions = projections_data_without_unit['RegionName'].unique()

        region_models = [Region(name=name) for name in regions]

        commodity_models = get_commodities_data(global_commodities_data, projections_data_without_unit, unit_row)
        
        year_models = [AvailableYear(year=i) for i in projections_data_without_unit['Time']]

        sector_models = get_sectors(settings_model)
        
        timeslice_info = unpack_timeslice(settings_model.timeslices)
        level_name_models = [LevelName(level=i) for i in timeslice_info.level_names]
        timeslice_models = [Timeslice(name = k, value = v) for k, v in timeslice_info.timeslices.items()]

        agent_models = get_agents(settings_model, folder)
        process_models = get_processes(settings_model, folder, commodity_models, agent_models)

        return cls(
            regions = region_models, 
            available_years=year_models, 
            commodities=commodity_models,
            sectors = sector_models,
            level_names=level_name_models,
            timeslices = timeslice_models,
            agents = agent_models,
            processes = process_models,
            run_model = RunModel.parse_obj(toml_out)
        )
    
    def export_to_folder(self, folder_path: str) -> Path:
        folder_path_obj = Path(folder_path)
        if not folder_path_obj.exists():
            folder_path_obj.mkdir(parents=True)
        input_folder = Path(f'{folder_path}{os.sep}input')
        if not input_folder.exists():
            input_folder.mkdir(parents=True)
        technodata_folder = Path(f'{folder_path}{os.sep}technodata')
        if not technodata_folder.exists():
            technodata_folder.mkdir(parents=True)
        commodities_path = Path(f'{str(input_folder)}{os.sep}GlobalCommodities.csv')
        projections_path = Path(f'{str(input_folder)}{os.sep}Projections.csv')
        new_settings_path = Path(f'{folder_path}{os.sep}settings.toml')
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


        
        # generate agents file
        agents_df = agents_to_dataframe(list(self._agent_datastore._data.values()))
        agents_path = Path(f"{technodata_folder}{os.sep}Agents.csv")
        agents_df.to_csv(agents_path, index=False)
        
        comm_names = [commodity.commodity_name for commodity in self.commodity._data.values()]
        comm_units = [commodity.unit+'/PJ' for commodity in self.commodity._data.values()]
        comm_new_headers = comm_initial_headings + comm_names

        # Create sector folders:
        sector_paths = {}
        new_sectors = {}
        for sector_name, sector in self.sector._data.items():
            sector_details = sector.dict()

            sector_path = Path(f"{str(technodata_folder)}{os.sep}{sector.name}")
            sector_paths[sector_name] = sector_path
            if not sector_path.exists():
                sector_path.mkdir(parents=True)
            # For each sector get forward deps on processes
            rel_process_names = self.sector.forward_dependents(sector)['process']

            rel_processes = [self.process.read(p) for p in rel_process_names]
            if sector.type == 'standard':

                subsector_details = {}

                sector_details['type'] = 'default'
                comm_in_path = Path(f"{str(sector_path)}{os.sep}CommIn.csv")
                comm_out_path = Path(f"{str(sector_path)}{os.sep}CommOut.csv")
                technodata_path = Path(f"{str(sector_path)}{os.sep}Technodata.csv")
                existing_capacity_path = Path(f"{str(sector_path)}{os.sep}ExistingCapacity.csv")
                sector_details['commodities_in'] = replace_path_prefix(comm_in_path, folder_path_obj)
                sector_details['commodities_out'] = replace_path_prefix(comm_out_path,folder_path_obj)
                sector_details['technodata'] = replace_path_prefix(technodata_path,folder_path_obj)
                subsector_details['agents'] = replace_path_prefix(agents_path,folder_path_obj)
                subsector_details['existing_capacity'] = replace_path_prefix(existing_capacity_path,folder_path_obj)
                
                rel_regions = []
                rel_times = []
                rel_levels = []
                for process in rel_processes:
                    for comm in process.comm_in:
                        if comm.region not in rel_regions:
                            rel_regions.append(comm.region)
                        if comm.timeslice not in rel_times:
                            rel_times.append(comm.timeslice)
                        if comm.level not in rel_levels:
                            rel_levels.append(comm.level)
                    for comm in process.comm_out:
                        if comm.region not in rel_regions:
                            rel_regions.append(comm.region)
                        if comm.timeslice not in rel_times:
                            rel_times.append(comm.timeslice)
                        if comm.level not in rel_levels:
                            rel_levels.append(comm.level)
                    for tech in process.technodatas:
                        if tech.region not in rel_regions:
                            rel_regions.append(tech.region)
                        if tech.time not in rel_times:
                            rel_times.append(tech.time)
                        if tech.level not in rel_levels:
                            rel_levels.append(tech.level)
                region_time_level_combos = list(product(rel_regions, rel_times, rel_levels))
                comm_in_data,comm_in_data_index = generate_empty_data_and_index(rel_processes, region_time_level_combos, comm_names)
                comm_out_data,comm_out_data_index = generate_empty_data_and_index(rel_processes, region_time_level_combos, comm_names)
                
                # Populate empty data
                for process in rel_processes:
                    for comm in process.comm_in:
                        v, i, j = data_and_location(self, comm_in_data_index, process, comm, comm_names)
                        comm_in_data[i][j] = v
                    for comm in process.comm_out:
                        v, i, j = data_and_location(self, comm_out_data_index, process, comm, comm_names)
                        comm_out_data[i][j] = v
                units: List[Union[str,float]] = ['Unit','-','Year', '-']+ comm_units #type:ignore
                comm_in_data.insert(0, units)
                comm_in_df = pd.DataFrame(comm_in_data, columns = comm_new_headers)
                comm_out_data.insert(0, units)
                comm_out_df = pd.DataFrame(comm_out_data, columns = comm_new_headers)
                comm_in_df.to_csv(comm_in_path, index=False)
                comm_out_df.to_csv(comm_out_path, index=False)


                agent_index = [agent for agent in self.agent._data.values()]
                agent_shares = [agent.share for agent in agent_index]
                technodata_headers = [
                    'ProcessName',
                    'RegionName',
                    'Time',
                    'Level',
                    'cap_par',
                    'cap_exp',
                    'fix_par',
                    'fix_exp',
                    'var_par',
                    'var_exp',
                    'MaxCapacityAddition',
                    'MaxCapacityGrowth',
                    'TotalCapacityLimit',
                    'TechnicalLife',
                    'UtilizationFactor',
                    'ScalingSize',
                    'efficiency',
                    'InterestRate',
                    'Type',
                    'Fuel',
                    'EndUse'
                ] + agent_shares
                data = [['Unit','-','Year','-','MUS$2010/PJ_a','-','MUS$2010/PJ','-','MUS$2010/PJ','-','PJ','%','PJ','Years','-','PJ','%','-','-','-','-']+[agent.type for agent in agent_index]]
                for process in rel_processes:
                    technodatas = process.technodatas
                    for technodata in technodatas:
                        initial_row = [
                            process.name,
                            technodata.region,
                            technodata.time,
                            technodata.level,
                            technodata.cost.cap_par,
                            technodata.cost.cap_exp,
                            technodata.cost.fix_par,
                            technodata.cost.fix_exp,
                            technodata.cost.var_par,
                            technodata.cost.var_exp,
                            technodata.capacity.max_capacity_addition,
                            technodata.capacity.max_capacity_growth,
                            technodata.capacity.total_capacity_limit,
                            technodata.capacity.technical_life,
                            technodata.utilisation.utilization_factor,
                            technodata.capacity.scaling_size,
                            technodata.utilisation.efficiency,
                            technodata.cost.interest_rate,
                            process.type,
                            process.fuel,
                            process.end_use
                        ]
                        zeros = [0.0]*len(self.agent._data)

                        for agent in technodata.agents:
                            agent_model = self.agent.read(agent.agent_name)
                            current_agent_index = agent_index.index(agent_model)
                            zeros[current_agent_index] = agent.share
                        row = initial_row + zeros
                        data.append(row)
                    
                df = pd.DataFrame(data, columns = technodata_headers)
                df.to_csv(technodata_path, index= False)
                
                data =[]
                years = self.available_year.list()
                headers = [
                    'ProcessName',
                    'RegionName',
                    'Unit',
                ] + years
                years_int = [int(i) for i in years]
                region_process_combos = list(product(rel_regions, rel_processes))
                for region_name, process in region_process_combos:
                    row = [0.0]*len(years)
                    final_row = []
                    for existing_capacity in process.existing_capacities:
                        if region_name == existing_capacity.region:
                            assert self.run_settings is not None
                            year_index = years_int.index(existing_capacity.year)
                            row[year_index] = existing_capacity.value
                            final_row: List[Union[str, float]] = [process.name,existing_capacity.region,process.capacity_unit] + row # type:ignore
                    data.append(final_row)
                df = pd.DataFrame(data, columns = headers)
                df.to_csv(existing_capacity_path, index = False)
                sector_details['subsectors'] = {'retro_and_new': subsector_details}
            elif sector.type == 'preset':
                sector_details['type'] = 'presets'
                Year = int
                data_dict: Dict[Year, List[List[Any]]] = {}
                basic_headers = ['RegionName','ProcessName','Timeslice']
                headers = basic_headers + comm_names
                
                for process in rel_processes:
                    rel_demands = process.demands
                    for demand in rel_demands:
                        year = demand.year
                        demand_flows = demand.demand_flows
                        data: List[List[Any]] = []
                        processes_regions_and_timeslices_seen: List[Tuple[str,str, str]] = []
                        for demand_flow in demand_flows:
                            row: List[Any] = [demand_flow.region, process.name, demand_flow.timeslice]
                            if (process.name, demand_flow.region, demand_flow.timeslice) in processes_regions_and_timeslices_seen:
                                row_index = processes_regions_and_timeslices_seen.index((process.name, demand_flow.region, demand_flow.timeslice))
                                commodity_name = self.commodity.read(demand_flow.commodity).commodity_name
                                comm_index = comm_names.index(commodity_name)
                                data[row_index][comm_index + len(basic_headers)] = demand_flow.value
                            else:
                                data_row = [0.0]*len(comm_names)
                                commodity_name = self.commodity.read(demand_flow.commodity).commodity_name
                                comm_index = comm_names.index(commodity_name)
                                data_row[comm_index] = demand_flow.value
                                data.append(row+data_row)
                                processes_regions_and_timeslices_seen.append((process.name, demand_flow.region, demand_flow.timeslice))
                        if year in data_dict:
                            data_dict[year] += data
                        else:
                            data_dict[year] = data
                consumption_path = None
                for year, data in data_dict.items():
                    consumption_path = Path(f"{str(sector_path)}{os.sep}A{year}Consumption.csv")
                    df = pd.DataFrame(data, columns = headers)
                    df.to_csv(consumption_path)
                assert consumption_path is not None
                sector_details['consumption_path'] = replace_path_prefix(consumption_path.parents[0], folder_path_obj)+f"{os.sep}*Consumption.csv"
            else:
                assert False
            new_sectors[sector_name] = sector_details

        timeslice_info = TimesliceInfo(
            timeslices={timeslice.name: timeslice.value for timeslice in self.timeslice._data.values()},
            level_names=self.level_name.list())
        new_timeslices = pack_timeslice(timeslice_info)

        assert self.run_settings is not None
        new_settings_model = SettingsModel(
            **self.run_settings.dict(),
            global_input_files=GlobalInputFiles(
                projections=replace_path_prefix(projections_path, folder_path_obj),
                global_commodities=replace_path_prefix(commodities_path, folder_path_obj)
            ),
            sectors=new_sectors,
            timeslices=new_timeslices,
            outputs=[
                Output(
                    quantity=Quantity.prices,
                    sink = Sink.csv,
                    filename = "{cwd}/{default_output_dir}/MCA{Quantity}.csv",
                    overwrite=True,
                    keep_columns = None,
                    index = True
                ),
                Output(
                    quantity=Quantity.capacity,
                    sink = Sink.csv,
                    filename = "{cwd}/{default_output_dir}/MCA{Quantity}.csv",
                    overwrite=True,
                    keep_columns = ["technology","region","agent","type","sector","capacity","year"],
                    index = False
                ),
            ]
        )
        with open(new_settings_path, 'w+' )as f:
            toml.dump(new_settings_model.dict(),f)
        return new_settings_path
