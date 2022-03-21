from typing import Dict, List, Optional, Tuple

from muse_gui.backend.data.agent import Agent, AgentObjective
from muse_gui.backend.data.process import Capacity, CommodityFlow, Cost, DemandFlow, ExistingCapacity, Process, Technodata, Utilisation, CapacityShare


from muse_gui.backend.data.sector import InterpolationType, Production, StandardSector, PresetSector, Sector

from muse_gui.backend.data.commodity import Commodity, CommodityPrice

from pathlib import Path

import re

import pandas as pd
from muse_gui.backend.settings import SettingsModel
import os
import glob
import math

def replace_path(folder_path:Path, current_path_string: str) -> str:
    return re.sub(r"{path}", str(folder_path), current_path_string)
def path_string_to_dataframe(folder_path:Path, current_path_string: str) -> pd.DataFrame:
    return pd.read_csv(replace_path(folder_path, current_path_string))

def get_commodities_data(global_commodities_data, projections_data, unit_row) -> List[Commodity]:
    commodity_models = []
    for i, name in enumerate(global_commodities_data["Commodity"]):
        commodity = global_commodities_data.iloc[i]
        unit = unit_row[commodity['CommodityName']]
        rel_price_data = pd.DataFrame(projections_data, columns=[commodity['CommodityName'], 'RegionName', 'Time'])
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
    return commodity_models

def get_sectors(settings_model: SettingsModel) -> List[Sector]:
    sectors = settings_model.sectors    
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
    return sector_models

def is_nan_new(value) -> bool:
    try:
        return math.isnan(float(value))
    except ValueError:
        return False
def get_objective(
    objective_type,
    objective_data, 
    objective_sort
) -> Optional[AgentObjective]:
    if is_nan_new(objective_type):
        return None
    else:
        new_type = objective_type
    if is_nan_new(objective_data):
        return None
    else:
        new_data = objective_data
    if is_nan_new(objective_sort):
        return None
    else:
        new_sort = objective_sort
    return AgentObjective(
        objective_type = new_type,
        objective_data = new_data,
        objective_sort = new_sort
    )


def _get_technodatas(process_technodata, agent_models: List[Agent]) -> List[Technodata]:
    technodatas = []
    for i, technodata in process_technodata.iterrows():
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
                agents = [CapacityShare(agent_name=agent.share, share= technodata[agent.share]) for agent in agent_models if float(technodata[agent.share]) > 0]
            )
        )
    return technodatas

# Get demand mapper
SectorName = str
ProcessName = str

SectorDemands = Dict[SectorName, List[DemandFlow]]

def _get_demand_mapper(settings_model: SettingsModel, folder: Path, commodity_models: List[Commodity]) -> Dict[ProcessName, SectorDemands]:
    demand_mapper  = {}
    for sector_name, sector in settings_model.sectors.items():
        if sector.type == 'presets':
            def construct_path_set(consumption_path: str, folder: Path) -> List[Path]:
                split_path = consumption_path.split(os.sep)
                preset_path = os.sep.join(split_path[:-1])
                regex = split_path[-1]
                replaced_p = replace_path(folder, preset_path)
                path_set = [Path(p) for p in glob.glob(os.path.join(replaced_p, regex))]
                return path_set
            
            path_set = construct_path_set(sector.consumption_path, folder)

            years = []
            for path in path_set:
                reyear = re.match(r"\S*.(\d{4})\S*\.csv", path.name)
                if reyear is None:
                    raise IOError(f"Unexpected filename {path.name}")
                year = int(reyear.group(1))
                years.append(year)

            consumption_dataframes = {years[i]: pd.read_csv(consumption_p) for i, consumption_p in enumerate(path_set)}

            for year, consumption_df in consumption_dataframes.items():
                process_names = consumption_df['ProcessName'].unique()
                
                for process_name in process_names:
                    rel_c_df = consumption_df.query(f'ProcessName == "{process_name}"')
                    for i, row in rel_c_df.iterrows():
                        if process_name in demand_mapper:
                            demand_mapper[process_name][sector_name]+=[DemandFlow(commodity=commodity.commodity, region=row['RegionName'], timeslice=row['Timeslice'], value=row[commodity.commodity_name]) for commodity in commodity_models]
                        else:
                            demand_mapper[process_name] = {sector_name: [DemandFlow(commodity=commodity.commodity, region=row['RegionName'], timeslice=row['Timeslice'], value=row[commodity.commodity_name]) for commodity in commodity_models]}
    return demand_mapper


def get_agents(settings_model: SettingsModel, folder: Path) -> List[Agent]:
    agent_models: List[Agent] = []
    shares_seen: List[str] = []
    for sector_name, sector in settings_model.sectors.items():
        if sector.type == 'default':
            if len(sector.subsectors) != 1:
                raise ValueError('Only single subsector case supported')
            else:
                subsector_name, subsector = next(iter(sector.subsectors.items()))

            agent_raw_data = path_string_to_dataframe(folder, subsector.agents)
            for i, agent in agent_raw_data.iterrows():
                objective_1 = get_objective(
                    objective_type = agent['Objective1'],
                    objective_data = agent['ObjData1'],
                    objective_sort= agent['Objsort1']
                )
                assert objective_1 is not None
                objective_2 = get_objective(
                    objective_type = agent['Objective2'],
                    objective_data = agent['ObjData2'],
                    objective_sort= agent['Objsort2']
                )
                objective_3 = get_objective(
                    objective_type = agent['Objective3'],
                    objective_data = agent['ObjData3'],
                    objective_sort= agent['Objsort3']
                )
                agent_model = Agent(
                    name = agent['Name'],
                    type = agent['Type'],
                    region = agent['RegionName'],
                    num = agent['AgentNumber'],
                    sectors = [sector_name], # TODO: Make this all sectors relavent
                    objective_1 = objective_1,
                    objective_2 = objective_2,
                    objective_3 = objective_3,
                    budget = agent['Budget'],
                    share = agent['AgentShare'],
                    search_rule= agent['SearchRule'],
                    decision_method=agent['DecisionMethod'],
                    quantity = agent['Quantity'],
                    maturity_threshold = agent['MaturityThreshold']
                )
                if agent_model.share not in shares_seen:
                    agent_models.append(agent_model)
                    shares_seen.append(agent['AgentShare'])
    
    return agent_models

def get_processes(settings_model: SettingsModel, folder: Path, commodity_models: List[Commodity], agent_models: List[Agent]) -> List[Process]:
    demand_mapper = _get_demand_mapper(settings_model, folder, commodity_models)
    process_models: List[Process] = []
    for sector_name, sector in settings_model.sectors.items():
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

                process_cap_data = existing_cap_data.query(f'ProcessName == "{process_name}"')

                technodatas = _get_technodatas(process_technodata, agent_models)
                example_process_technodata = process_technodata.iloc[0]

                cap_datas = []
                units = []
                for i, region_cap_data in process_cap_data.iterrows():
                    region_name = region_cap_data['RegionName']
                    unit = region_cap_data['Unit']
                    units.append(unit)
                    years = list(region_cap_data.keys()[3:])
                    for year in years:
                        cap_data = ExistingCapacity(
                            region=region_name,
                            year = year,
                            value = region_cap_data[str(year)]
                        )
                        cap_datas.append(cap_data)
                cap_units = list(set(units))
                assert len(cap_units) ==1
                cap_unit = cap_units[0]
                if process_name in demand_mapper:
                    sector_dict = demand_mapper[process_name]
                    assert len(sector_dict) == 1
                    demand_mapper_list = [(preset_sector_name,demand) for preset_sector_name, demand in sector_dict.items()]
                    preset_sector_name, demand = demand_mapper_list[0]
                else:
                    preset_sector_name = None
                    demand = []

                process_model = Process(
                    name = example_process_technodata['ProcessName'],
                    sector = sector_name,
                    preset_sector = preset_sector_name,
                    fuel = example_process_technodata['Fuel'],
                    end_use = example_process_technodata['EndUse'],
                    type = example_process_technodata['Type'],
                    technodatas = technodatas,
                    comm_in=[
                        CommodityFlow(
                            commodity=commodity.commodity,
                            region = process_comm_in['RegionName'],
                            timeslice = process_comm_in['Time'],
                            level = process_comm_in['Level'],
                            value = process_comm_in[commodity.commodity_name]
                        ) for commodity in commodity_models if float(process_comm_in[commodity.commodity_name]) !=0],
                    comm_out=[
                        CommodityFlow(
                            commodity=commodity.commodity,
                            region = process_comm_out['RegionName'],
                            timeslice = process_comm_out['Time'],
                            level = process_comm_out['Level'],
                            value = process_comm_out[commodity.commodity_name]
                        ) for commodity in commodity_models if float(process_comm_out[commodity.commodity_name]) !=0],
                    demand=demand,
                    existing_capacities=cap_datas,
                    capacity_unit=cap_unit
                )
                process_models.append(process_model)

        elif sector.type == 'presets':
            pass
        else:
            raise TypeError(f"Sector type {sector.type} not supported")
    return process_models
