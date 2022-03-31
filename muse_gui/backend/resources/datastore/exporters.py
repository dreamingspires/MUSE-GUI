import os
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

import pandas as pd

from muse_gui.backend.data.agent import Agent, AgentData, AgentType
from muse_gui.backend.data.process import CommodityFlow, Process
from muse_gui.backend.data.sector import Sector
from muse_gui.backend.utils import TimesliceInfo, pack_timeslice

if TYPE_CHECKING:
    from . import Datastore


def replace_path_prefix(path: Path, prefix_to_replace: Path) -> str:
    absolute_path = str(path.absolute())
    prefix = str(prefix_to_replace.absolute())
    return "{path}" + f"{absolute_path[len(prefix):]}"


def agents_to_dataframe(agents: List[Agent]) -> pd.DataFrame:
    if len(agents) == 0:
        raise ValueError("Agents not defined")
    headers = [
        "AgentShare",
        "Name",
        "AgentNumber",
        "RegionName",
        "Objective1",
        "Objective2",
        "Objective3",
        "ObjData1",
        "ObjData2",
        "ObjData3",
        "Objsort1",
        "Objsort2",
        "Objsort3",
        "SearchRule",
        "DecisionMethod",
        "Quantity",
        "MaturityThreshold",
        "Budget",
        "Type",
    ]

    agents_list = []
    for agent in agents:
        for agent_type in AgentType:
            if agent_type == AgentType.New:
                rel_data: Dict[str, AgentData] = getattr(agent, "new")
            elif agent_type == AgentType.Retrofit:
                rel_data: Dict[str, AgentData] = getattr(agent, "retrofit")
            else:
                raise ValueError
            for region, agent_data in rel_data.items():
                if agent_data.objective_2 is None:
                    objective_2_objective_type = None
                    objective_2_objective_data = None
                    objective_2_objective_sort = None
                else:
                    objective_2_objective_type = agent_data.objective_2.objective_type
                    objective_2_objective_data = agent_data.objective_2.objective_data
                    objective_2_objective_sort = agent_data.objective_2.objective_sort
                if agent_data.objective_3 is None:
                    objective_3_objective_type = None
                    objective_3_objective_data = None
                    objective_3_objective_sort = None
                else:
                    objective_3_objective_type = agent_data.objective_3.objective_type
                    objective_3_objective_data = agent_data.objective_3.objective_data
                    objective_3_objective_sort = agent_data.objective_3.objective_sort
                agents_list.append(
                    {
                        "AgentShare": agent_data.share,
                        "Name": agent.name,
                        "AgentNumber": agent_data.num,
                        "RegionName": region,
                        "Objective1": agent_data.objective_1.objective_type,
                        "Objective2": objective_2_objective_type,
                        "Objective3": objective_3_objective_type,
                        "ObjData1": agent_data.objective_1.objective_data,
                        "ObjData2": objective_2_objective_data,
                        "ObjData3": objective_3_objective_data,
                        "Objsort1": agent_data.objective_1.objective_sort,
                        "Objsort2": objective_2_objective_sort,
                        "Objsort3": objective_3_objective_sort,
                        "SearchRule": agent_data.search_rule,
                        "DecisionMethod": agent_data.decision_method,
                        "Quantity": agent_data.quantity,
                        "MaturityThreshold": agent_data.maturity_threshold,
                        "Budget": agent_data.budget,
                        "Type": agent_type,
                    }
                )
    agent_df = pd.DataFrame(agents_list, columns=headers)
    return agent_df


def generate_empty_data_and_index(
    processes: List[Process],
    region_time_level_combos: List[Tuple[str, int, str]],
    all_commodity_names: List[str],
) -> Tuple[List[List[Union[str, float]]], List[List[str]]]:

    empty_data = []
    empty_data_index = []
    for process in processes:
        for region, time, level in region_time_level_combos:
            initial_data: List[Union[str, float]] = [process.name, region, time, level]
            commod_data: List[Union[str, float]] = [0.0] * len(all_commodity_names)
            empty_data.append(initial_data + commod_data)
            empty_data_index.append(initial_data)
    return empty_data, empty_data_index


def export_commodities(commodity_data, commodities_path):
    commodities = [commodity.dict() for _, commodity in commodity_data.items()]
    # Export GlobalCommodities
    commodity_dataframe = pd.DataFrame.from_records(
        data=commodities,
        columns=[
            "commodity",
            "commodity_type",
            "commodity_name",
            "c_emission_factor_co2",
            "heat_rate",
            "unit",
        ],
    )
    new_commodity_dataframe = commodity_dataframe.rename(
        columns={
            "commodity": "Commodity",
            "commodity_type": "CommodityType",
            "commodity_name": "CommodityName",
            "c_emission_factor_co2": "CommodityEmissionFactor_CO2",
            "heat_rate": "HeatRate",
            "unit": "Unit",
        }
    )
    new_commodity_dataframe.to_csv(commodities_path, index=False)


def export_projections(datastore: "Datastore", commodity_data, projections_path):
    # Export Projections

    # Make initial dataframe excluding commodity data

    if len(datastore.commodity._data) == 0:
        raise NotImplementedError
    else:
        _, first_element = next(iter(commodity_data.items()))
    prices = [price.dict() for price in first_element.commodity_prices]
    projections_df = pd.DataFrame.from_records(
        data=prices, columns=["region_name", "time"]
    )
    projections_df["Attribute"] = ["CommodityPrice"] * len(projections_df)
    projections_df = projections_df[["region_name", "Attribute", "time"]]

    for _, commodity in datastore._commodity_datastore._data.items():
        projections_df[commodity.commodity_name] = [
            price.value for price in commodity.commodity_prices
        ]

    # Construct first row
    first_row = ["Unit", "-", " Year"] + [
        commodity.price_unit for _, commodity in commodity_data.items()
    ]
    headers = list(projections_df)
    new_dict = {header: [first_row[i]] for i, header in enumerate(headers)}
    first_df = pd.DataFrame(new_dict)

    projections_df = pd.concat([first_df, projections_df])
    projections_df = projections_df.rename(
        columns={"region_name": "RegionName", "time": "Time"}
    )
    projections_df.to_csv(projections_path, index=False)


comm_initial_headings = ["ProcessName", "RegionName", "Time", "Level"]


def data_and_location(
    datastore: "Datastore",
    index: List[List[str]],
    process: Process,
    commodity_flow: CommodityFlow,
    all_commodity_names: List[str],
) -> Tuple[float, int, int]:
    row_index = index.index(
        [
            process.name,
            commodity_flow.region,
            commodity_flow.timeslice,
            commodity_flow.level,
        ]
    )
    commod_model = datastore.commodity.read(commodity_flow.commodity)
    col_index = len(comm_initial_headings) + all_commodity_names.index(
        commod_model.commodity_name
    )
    return commodity_flow.value, row_index, col_index


def export_comm_in_and_out(
    datastore: "Datastore",
    rel_processes: List[Process],
    comm_names: List[str],
    comm_units: List[str],
    comm_new_headers: List[str],
    sector_path: Path,
) -> Tuple[Path, Path, List[str]]:
    comm_in_path = Path(f"{str(sector_path)}{os.sep}CommIn.csv")
    comm_out_path = Path(f"{str(sector_path)}{os.sep}CommOut.csv")
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
    comm_in_data, comm_in_data_index = generate_empty_data_and_index(
        rel_processes, region_time_level_combos, comm_names
    )
    comm_out_data, comm_out_data_index = generate_empty_data_and_index(
        rel_processes, region_time_level_combos, comm_names
    )

    # Populate empty data
    for process in rel_processes:
        for comm in process.comm_in:
            v, i, j = data_and_location(
                datastore, comm_in_data_index, process, comm, comm_names
            )
            comm_in_data[i][j] = v
        for comm in process.comm_out:
            v, i, j = data_and_location(
                datastore, comm_out_data_index, process, comm, comm_names
            )
            comm_out_data[i][j] = v
    units: List[Union[str, float]] = [
        "Unit",
        "-",
        "Year",
        "-",
    ] + comm_units  # type:ignore
    comm_in_data.insert(0, units)
    comm_in_df = pd.DataFrame(comm_in_data, columns=comm_new_headers)
    comm_out_data.insert(0, units)
    comm_out_df = pd.DataFrame(comm_out_data, columns=comm_new_headers)
    comm_in_df.to_csv(comm_in_path, index=False)
    comm_out_df.to_csv(comm_out_path, index=False)
    return comm_in_path, comm_out_path, rel_regions


def export_technodata(
    rel_processes: List[Process], datastore: "Datastore", technodata_path: Path
):
    agent_data_index: List[Tuple[str, AgentType, AgentData]] = []
    agent_shares = []
    agent_types = []
    for agent in datastore.agent._data.values():
        for region, agent_data in agent.new.items():
            agent_shares.append(agent_data.share)
            agent_types.append(AgentType.New)
            agent_data_index.append((region, AgentType.New, agent_data))
        for region, agent_data in agent.retrofit.items():
            agent_shares.append(agent_data.share)
            agent_types.append(AgentType.Retrofit)
            agent_data_index.append((region, AgentType.Retrofit, agent_data))
    technodata_headers = [
        "ProcessName",
        "RegionName",
        "Time",
        "Level",
        "cap_par",
        "cap_exp",
        "fix_par",
        "fix_exp",
        "var_par",
        "var_exp",
        "MaxCapacityAddition",
        "MaxCapacityGrowth",
        "TotalCapacityLimit",
        "TechnicalLife",
        "UtilizationFactor",
        "ScalingSize",
        "efficiency",
        "InterestRate",
        "Type",
        "Fuel",
        "EndUse",
    ] + agent_shares
    data = [
        [
            "Unit",
            "-",
            "Year",
            "-",
            "MUS$2010/PJ_a",
            "-",
            "MUS$2010/PJ",
            "-",
            "MUS$2010/PJ",
            "-",
            "PJ",
            "%",
            "PJ",
            "Years",
            "-",
            "PJ",
            "%",
            "-",
            "-",
            "-",
            "-",
        ]
        + agent_types
    ]
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
                process.end_use,
            ]
            zeros = [0.0] * len(agent_data_index)

            for capacity_share in technodata.agents:
                agent_model = datastore.agent.read(capacity_share.agent_name)
                if capacity_share.agent_type == AgentType.New:
                    agent_data = agent_model.new
                elif capacity_share.agent_type == AgentType.Retrofit:
                    agent_data = agent_model.retrofit
                else:
                    raise RuntimeError
                rel_agent_data = agent_data[capacity_share.region]
                current_agent_index = agent_data_index.index(
                    (capacity_share.region, capacity_share.agent_type, rel_agent_data)
                )
                zeros[current_agent_index] = capacity_share.share
            row = initial_row + zeros
            data.append(row)

    df = pd.DataFrame(data, columns=technodata_headers)
    df.to_csv(technodata_path, index=False)


def export_existing_capacities(
    datastore: "Datastore",
    rel_regions: List[str],
    rel_processes: List[Process],
    existing_capacity_path: Path,
) -> None:
    data = []
    years = datastore.available_year.list()
    headers = [
        "ProcessName",
        "RegionName",
        "Unit",
    ] + years
    years_int = [int(i) for i in years]
    region_process_combos = list(product(rel_regions, rel_processes))
    for region_name, process in region_process_combos:
        row = [0.0] * len(years)
        final_row = []
        for existing_capacity in process.existing_capacities:
            if region_name == existing_capacity.region:
                assert datastore.run_settings is not None
                year_index = years_int.index(existing_capacity.year)
                row[year_index] = existing_capacity.value
                final_row: List[Union[str, float]] = [
                    process.name,
                    existing_capacity.region,
                    process.capacity_unit,
                ] + row  # type:ignore
        data.append(final_row)
    df = pd.DataFrame(data, columns=headers)
    df.to_csv(existing_capacity_path, index=False)


def export_preset_consumption(
    datastore: "Datastore",
    rel_processes: List[Process],
    comm_names: List[str],
    sector_path: Path,
) -> None:
    Year = int
    data_dict: Dict[Year, List[List[Any]]] = {}
    basic_headers = ["RegionName", "ProcessName", "Timeslice"]
    headers = basic_headers + comm_names
    for process in rel_processes:
        rel_demands = process.demands
        for demand in rel_demands:
            year = demand.year
            demand_flows = demand.demand_flows
            data: List[List[Any]] = []
            processes_regions_and_timeslices_seen: List[Tuple[str, str, str]] = []
            for demand_flow in demand_flows:
                row: List[Any] = [
                    demand_flow.region,
                    process.name,
                    demand_flow.timeslice,
                ]
                if (
                    process.name,
                    demand_flow.region,
                    demand_flow.timeslice,
                ) in processes_regions_and_timeslices_seen:
                    row_index = processes_regions_and_timeslices_seen.index(
                        (process.name, demand_flow.region, demand_flow.timeslice)
                    )
                    commodity_name = datastore.commodity.read(
                        demand_flow.commodity
                    ).commodity_name
                    comm_index = comm_names.index(commodity_name)
                    data[row_index][comm_index + len(basic_headers)] = demand_flow.value
                else:
                    data_row = [0.0] * len(comm_names)
                    commodity_name = datastore.commodity.read(
                        demand_flow.commodity
                    ).commodity_name
                    comm_index = comm_names.index(commodity_name)
                    data_row[comm_index] = demand_flow.value
                    data.append(row + data_row)
                    processes_regions_and_timeslices_seen.append(
                        (process.name, demand_flow.region, demand_flow.timeslice)
                    )
            if year in data_dict:
                data_dict[year] += data
            else:
                data_dict[year] = data

    for year, data in data_dict.items():
        consumption_path = Path(f"{str(sector_path)}{os.sep}A{year}Consumption.csv")
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(consumption_path)


def get_sector_details(
    datastore: "Datastore",
    sector: Sector,
    technodata_folder: Path,
    folder_path_obj: Path,
    agents_path: Path,
    comm_names: List[str],
    comm_units: List[str],
    comm_new_headers: List[str],
) -> Dict:
    sector_details = sector.dict()
    sector_path = Path(f"{str(technodata_folder)}{os.sep}{sector.name}")
    if not sector_path.exists():
        sector_path.mkdir(parents=True)
    # For each sector get forward deps on processes
    rel_process_names = datastore.sector.forward_dependents(sector)["process"]
    rel_processes = [datastore.process.read(p) for p in rel_process_names]
    if sector.type == "standard":

        subsector_details = {}
        sector_details["type"] = "default"

        subsector_details["agents"] = replace_path_prefix(agents_path, folder_path_obj)

        comm_in_path, comm_out_path, rel_regions = export_comm_in_and_out(
            datastore,
            rel_processes,
            comm_names,
            comm_units,
            comm_new_headers,
            sector_path,
        )
        sector_details["commodities_in"] = replace_path_prefix(
            comm_in_path, folder_path_obj
        )
        sector_details["commodities_out"] = replace_path_prefix(
            comm_out_path, folder_path_obj
        )

        technodata_path = Path(f"{str(sector_path)}{os.sep}Technodata.csv")
        sector_details["technodata"] = replace_path_prefix(
            technodata_path, folder_path_obj
        )
        export_technodata(rel_processes, datastore, technodata_path)

        existing_capacity_path = Path(f"{str(sector_path)}{os.sep}ExistingCapacity.csv")
        subsector_details["existing_capacity"] = replace_path_prefix(
            existing_capacity_path, folder_path_obj
        )
        export_existing_capacities(
            datastore, rel_regions, rel_processes, existing_capacity_path
        )

        sector_details["subsectors"] = {"retro_and_new": subsector_details}
    elif sector.type == "preset":
        sector_details["type"] = "presets"

        export_preset_consumption(datastore, rel_processes, comm_names, sector_path)

        sector_details["consumption_path"] = (
            replace_path_prefix(sector_path, folder_path_obj)
            + f"{os.sep}*Consumption.csv"
        )
    else:
        assert False
    return sector_details


def generate_sectors(
    datastore: "Datastore",
    technodata_folder: Path,
    folder_path_obj: Path,
    agents_path: Path,
) -> Dict:
    comm_names = [
        commodity.commodity_name for commodity in datastore.commodity._data.values()
    ]
    comm_units = [
        commodity.unit + "/PJ" for commodity in datastore.commodity._data.values()
    ]
    comm_new_headers = comm_initial_headings + comm_names
    new_sectors = {}
    for sector_name, sector in datastore.sector._data.items():
        new_sectors[sector_name] = get_sector_details(
            datastore,
            sector,
            technodata_folder,
            folder_path_obj,
            agents_path,
            comm_names,
            comm_units,
            comm_new_headers,
        )
    return new_sectors


def convert_timeslices(datastore):
    timeslice_info = TimesliceInfo(
        timeslices={
            timeslice.name: timeslice.value
            for timeslice in datastore.timeslice._data.values()
        },
        level_names=datastore.level_name.list(),
    )
    return pack_timeslice(timeslice_info)
