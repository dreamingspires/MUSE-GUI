import glob
import math
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from muse_gui.backend.data.agent import Agent, AgentData, AgentObjective, AgentType
from muse_gui.backend.data.commodity import Commodity, CommodityPrice
from muse_gui.backend.data.process import (
    Capacity,
    CapacityShare,
    CommodityFlow,
    Cost,
    Demand,
    DemandFlow,
    ExistingCapacity,
    Process,
    Technodata,
    Utilisation,
)
from muse_gui.backend.data.sector import (
    InterpolationType,
    InvProduction,
    PresetSector,
    Production,
    Sector,
    StandardSector,
)
from muse_gui.backend.settings import SettingsModel


def replace_path(folder_path: Path, current_path_string: Path) -> str:
    new_folder = folder_path.as_posix()
    new_current = current_path_string.as_posix()
    return str(Path(re.sub(r"{path}", new_folder, new_current)))


def path_string_to_dataframe(
    folder_path: Path, current_path_string: Path
) -> pd.DataFrame:
    return pd.read_csv(replace_path(folder_path, current_path_string))


def get_commodities_data(
    global_commodities_data, projections_data, unit_row
) -> List[Commodity]:
    commodity_models = []
    for i, name in enumerate(global_commodities_data["Commodity"]):
        commodity = global_commodities_data.iloc[i]
        unit = unit_row[commodity["CommodityName"]]
        rel_price_data = pd.DataFrame(
            projections_data, columns=[commodity["CommodityName"], "RegionName", "Time"]
        )
        commodity_prices = []
        for j, row in rel_price_data.iterrows():
            commodity_prices.append(
                CommodityPrice(
                    region_name=row["RegionName"],
                    time=row["Time"],
                    value=row[commodity["CommodityName"]],
                )
            )
        com = Commodity(
            commodity=commodity["Commodity"],
            commodity_type=commodity["CommodityType"].title(),
            commodity_name=commodity["CommodityName"],
            c_emission_factor_co2=commodity["CommodityEmissionFactor_CO2"],
            heat_rate=commodity["HeatRate"],
            unit=commodity["Unit"],
            commodity_prices=commodity_prices,
            price_unit=unit,
        )
        commodity_models.append(com)
    return commodity_models


def get_sectors(settings_model: SettingsModel) -> List[Sector]:
    sectors = settings_model.sectors
    sector_models = []
    for sector_name, sector in sectors.items():
        if sector.type == "default":
            new_sector = StandardSector(
                name=sector_name,
                priority=sector.priority,
                interpolation=InterpolationType(sector.interpolation),
                dispatch_production=Production(sector.dispatch_production),
                investment_production=InvProduction(
                    name=sector.production.name, costing=sector.production.costing
                )
                if sector.production is not None
                else None,
                forecast=sector.subsectors["retro_and_new"].forecast,
                lpsolver=sector.subsectors["retro_and_new"].lpsolver,
                constraints=sector.subsectors["retro_and_new"].constraints,
            )
        else:
            new_sector = PresetSector(name=sector_name, priority=sector.priority)
        sector_models.append(new_sector)
    return sector_models


def is_nan_new(value) -> bool:
    if value is None:
        return False
    try:
        return math.isnan(float(value))
    except ValueError:
        return False


def get_objective(
    objective_type, objective_data, objective_sort
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
        objective_type=new_type, objective_data=new_data, objective_sort=new_sort
    )


def _get_technodatas(process_technodata, agent_models: List[Agent]) -> List[Technodata]:
    technodatas = []
    for i, technodata in process_technodata.iterrows():
        # TODO Consider structure of capacity share
        agent_shares = []
        for agent_model in agent_models:
            for region, agent_data in agent_model.new.items():
                if (
                    agent_data.share in technodata
                    and float(technodata[agent_data.share]) != 0
                ):
                    agent_share = CapacityShare(
                        agent_name=agent_model.name,
                        agent_type=AgentType.New,
                        region=region,
                        share=technodata[agent_data.share],
                    )
                    agent_shares.append(agent_share)
            for region, agent_data in agent_model.retrofit.items():
                if (
                    agent_data.share in technodata
                    and float(technodata[agent_data.share]) != 0
                ):
                    agent_share = CapacityShare(
                        agent_name=agent_model.name,
                        agent_type=AgentType.Retrofit,
                        region=region,
                        share=technodata[agent_data.share],
                    )
                    agent_shares.append(agent_share)

        technodatas.append(
            Technodata(
                region=technodata["RegionName"],
                time=technodata["Time"],
                level=technodata["Level"],
                cost=Cost(
                    cap_par=technodata["cap_par"],
                    cap_exp=technodata["cap_exp"],
                    fix_par=technodata["fix_par"],
                    fix_exp=technodata["fix_exp"],
                    var_par=technodata["var_par"],
                    var_exp=technodata["var_exp"],
                    interest_rate=technodata["InterestRate"],
                ),
                utilisation=Utilisation(
                    utilization_factor=technodata["UtilizationFactor"],
                    efficiency=technodata["efficiency"],
                ),
                capacity=Capacity(
                    max_capacity_addition=technodata["MaxCapacityAddition"],
                    max_capacity_growth=technodata["MaxCapacityGrowth"],
                    total_capacity_limit=technodata["TotalCapacityLimit"],
                    technical_life=technodata["TechnicalLife"],
                    scaling_size=technodata["ScalingSize"],
                ),
                agents=agent_shares,
            )
        )
    return technodatas


# Get demand mapper
SectorName = str
ProcessName = str
Year = int


def _get_demand_mapper(
    settings_model: SettingsModel, folder: Path, commodity_models: List[Commodity]
) -> Dict[ProcessName, Dict[SectorName, List[Demand]]]:
    demand_mapper = {}
    for sector_name, sector in settings_model.sectors.items():
        if sector.type == "presets":

            def construct_path_set(consumption_path: str, folder: Path) -> List[Path]:
                split_path = consumption_path.split(os.sep)
                preset_path = os.sep.join(split_path[:-1])
                regex = split_path[-1]
                replaced_p = replace_path(folder, Path(preset_path))
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

            consumption_dataframes = {
                years[i]: pd.read_csv(consumption_p)
                for i, consumption_p in enumerate(path_set)
            }

            for year, consumption_df in consumption_dataframes.items():
                process_names = consumption_df["ProcessName"].unique()

                for process_name in process_names:
                    rel_c_df = consumption_df.query(f'ProcessName == "{process_name}"')
                    for i, row in rel_c_df.iterrows():
                        if process_name in demand_mapper:
                            demands = demand_mapper[process_name][sector_name]
                            demand_years = [i.year for i in demands]
                            if year in demand_years:
                                demand_index = demand_years.index(year)
                                new_demands = demand_mapper[process_name][sector_name][
                                    demand_index
                                ].demand_flows + [
                                    DemandFlow(
                                        commodity=commodity.commodity,
                                        region=row["RegionName"],
                                        timeslice=row["Timeslice"],
                                        value=row[commodity.commodity_name],
                                    )
                                    for commodity in commodity_models
                                ]
                                demand_mapper[process_name][sector_name][
                                    demand_index
                                ] = Demand(year=year, demand_flows=new_demands)
                            else:
                                demand_mapper[process_name][sector_name] += [
                                    Demand(
                                        year=year,
                                        demand_flows=[
                                            DemandFlow(
                                                commodity=commodity.commodity,
                                                region=row["RegionName"],
                                                timeslice=row["Timeslice"],
                                                value=row[commodity.commodity_name],
                                            )
                                            for commodity in commodity_models
                                        ],
                                    )
                                ]

                        else:
                            demand_mapper[process_name] = {
                                sector_name: [
                                    Demand(
                                        year=year,
                                        demand_flows=[
                                            DemandFlow(
                                                commodity=commodity.commodity,
                                                region=row["RegionName"],
                                                timeslice=row["Timeslice"],
                                                value=row[commodity.commodity_name],
                                            )
                                            for commodity in commodity_models
                                        ],
                                    )
                                ]
                            }

    return demand_mapper


def get_agent_datas(
    agent_raw_data, agent_name
) -> Tuple[Dict[str, AgentData], Dict[str, AgentData]]:
    rel_data = agent_raw_data.query(f'Name == "{agent_name}"')
    agent_new_datas: Dict[str, AgentData] = {}
    agent_retrofit_datas: Dict[str, AgentData] = {}
    for i, agent in rel_data.iterrows():
        objective_1 = get_objective(
            objective_type=agent["Objective1"],
            objective_data=agent["ObjData1"],
            objective_sort=agent["Objsort1"],
        )
        assert objective_1 is not None
        objective_2 = get_objective(
            objective_type=agent["Objective2"],
            objective_data=agent["ObjData2"],
            objective_sort=agent["Objsort2"],
        )
        objective_3 = get_objective(
            objective_type=agent["Objective3"],
            objective_data=agent["ObjData3"],
            objective_sort=agent["Objsort3"],
        )
        agent_data = AgentData(
            num=agent.get("AgentNumber")
            if not is_nan_new(agent.get("AgentNumber"))
            else None,
            objective_1=objective_1,
            objective_2=objective_2,
            objective_3=objective_3,
            budget=agent["Budget"],
            share=agent["AgentShare"],
            search_rule=agent["SearchRule"],
            decision_method=agent["DecisionMethod"],
            quantity=agent["Quantity"],
            maturity_threshold=agent["MaturityThreshold"],
        )
        if agent["Type"] == "Retrofit":
            agent_retrofit_datas[agent["RegionName"]] = agent_data
        elif agent["Type"] == "New":
            agent_new_datas[agent["RegionName"]] = agent_data
        else:
            raise ValueError
    return agent_new_datas, agent_retrofit_datas


def get_agents(settings_model: SettingsModel, folder: Path) -> List[Agent]:
    agent_models: List[Agent] = []
    agent_name_index: List[str] = []
    for sector_name, sector in settings_model.sectors.items():
        if sector.type == "default":
            if len(sector.subsectors) != 1:
                raise ValueError("Only single subsector case supported")
            else:
                subsector_name, subsector = next(iter(sector.subsectors.items()))

            agent_raw_data = path_string_to_dataframe(folder, Path(subsector.agents))
            agent_names = agent_raw_data["Name"].unique()
            for agent_name in agent_names:
                agent_new_datas, agent_retrofit_datas = get_agent_datas(
                    agent_raw_data, agent_name
                )

                if agent_name in agent_name_index:
                    existing_agent_no = agent_name_index.index(agent_name)
                    existing_agent = agent_models[existing_agent_no]
                    if (agent_new_datas == existing_agent.new) and (
                        agent_retrofit_datas == existing_agent.retrofit
                    ):
                        new_agent = Agent(
                            name=agent_name,
                            sectors=[sector_name] + existing_agent.sectors,
                            new=agent_new_datas,
                            retrofit=agent_retrofit_datas,
                        )
                        agent_models[existing_agent_no] = new_agent
                    else:
                        raise RuntimeError(
                            f"Multiple definitions found for AgentName {agent_name} "
                        )
                else:
                    new_agent = Agent(
                        name=agent_name,
                        sectors=[sector_name],
                        new=agent_new_datas,
                        retrofit=agent_retrofit_datas,
                    )
                    agent_name_index.append(agent_name)
                    agent_models.append(new_agent)
    return agent_models


def get_processes(
    settings_model: SettingsModel,
    folder: Path,
    commodity_models: List[Commodity],
    agent_models: List[Agent],
) -> List[Process]:
    demand_mapper = _get_demand_mapper(settings_model, folder, commodity_models)
    process_models: List[Process] = []
    for sector_name, sector in settings_model.sectors.items():
        if sector.type == "default":
            technodata_data = path_string_to_dataframe(folder, Path(sector.technodata))
            technodata_data_without_unit = technodata_data.drop(0)
            technodata_data.loc[0]

            comm_in_data = path_string_to_dataframe(folder, Path(sector.commodities_in))
            comm_in_data_without_unit = comm_in_data.drop(0)
            comm_in_data.loc[0]

            comm_out_data = path_string_to_dataframe(
                folder, Path(sector.commodities_out)
            )
            comm_out_data_without_unit = comm_out_data.drop(0)
            comm_out_data.loc[0]

            if len(sector.subsectors) != 1:
                raise ValueError("Only single subsector case supported")
            else:
                subsector_name, subsector = next(iter(sector.subsectors.items()))

            existing_cap_data = path_string_to_dataframe(
                folder, Path(subsector.existing_capacity)
            )
            process_names = technodata_data_without_unit["ProcessName"].unique()
            for process_name in process_names:

                process_technodata = technodata_data_without_unit.query(
                    f'ProcessName == "{process_name}"'
                )

                process_comm_in = comm_in_data_without_unit.query(
                    f'ProcessName == "{process_name}"'
                )
                assert len(process_comm_in) == 1
                process_comm_in = process_comm_in.iloc[0]
                process_comm_out = comm_out_data_without_unit.query(
                    f'ProcessName == "{process_name}"'
                )
                assert len(process_comm_out) == 1
                process_comm_out = process_comm_out.iloc[0]

                process_cap_data = existing_cap_data.query(
                    f'ProcessName == "{process_name}"'
                )

                technodatas = _get_technodatas(process_technodata, agent_models)
                example_process_technodata = process_technodata.iloc[0]

                cap_datas = []
                units = []
                for i, region_cap_data in process_cap_data.iterrows():
                    region_name = region_cap_data["RegionName"]
                    unit = region_cap_data["Unit"]
                    units.append(unit)
                    years = list(region_cap_data.keys()[3:])
                    for year in years:
                        cap_data = ExistingCapacity(
                            region=region_name,
                            year=year,
                            value=region_cap_data[str(year)],
                        )
                        cap_datas.append(cap_data)
                cap_units = list(set(units))
                assert len(cap_units) == 1
                cap_unit = cap_units[0]
                if process_name in demand_mapper:
                    demand_map = demand_mapper[process_name]
                    assert len(demand_map) == 1
                    preset_sector_name = list(demand_map.keys())[0]
                    demands = demand_map[preset_sector_name]
                else:
                    preset_sector_name = None
                    demands = []

                process_model = Process(
                    name=example_process_technodata["ProcessName"],
                    sector=sector_name,
                    preset_sector=preset_sector_name,
                    fuel=example_process_technodata["Fuel"],
                    end_use=example_process_technodata["EndUse"],
                    type=example_process_technodata["Type"],
                    technodatas=technodatas,
                    comm_in=[
                        CommodityFlow(
                            commodity=commodity.commodity,
                            region=process_comm_in["RegionName"],
                            timeslice=process_comm_in["Time"],
                            level=process_comm_in["Level"],
                            value=process_comm_in[commodity.commodity_name],
                        )
                        for commodity in commodity_models
                        if float(process_comm_in[commodity.commodity_name]) != 0
                    ],
                    comm_out=[
                        CommodityFlow(
                            commodity=commodity.commodity,
                            region=process_comm_out["RegionName"],
                            timeslice=process_comm_out["Time"],
                            level=process_comm_out["Level"],
                            value=process_comm_out[commodity.commodity_name],
                        )
                        for commodity in commodity_models
                        if float(process_comm_out[commodity.commodity_name]) != 0
                    ],
                    demands=demands,
                    existing_capacities=cap_datas,
                    capacity_unit=cap_unit,
                )
                process_models.append(process_model)

        elif sector.type == "presets":
            pass
        else:
            raise TypeError(f"Sector type {sector.type} not supported")
    return process_models
