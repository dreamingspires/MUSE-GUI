from dataclasses import dataclass
from itertools import product
from typing import Dict, List

import pandas as pd


@dataclass
class CapacityPlot:
    name: str
    region: str
    agent: str
    sector: str
    data: Dict[str, pd.DataFrame]


def capacity_data_frame_to_plots(dataframe: pd.DataFrame) -> List[CapacityPlot]:
    def get_data(
        all_data: pd.DataFrame, region: str, agent: str, sector: str
    ) -> pd.DataFrame:
        relevant_data = all_data.loc[
            (all_data["region"] == region)
            & (all_data["agent"] == agent)
            & (all_data["sector"] == sector)
        ]
        new_data = relevant_data[["technology", "year", "capacity"]]
        fresh = new_data.groupby(["technology", "year"]).sum()
        brand_new = []
        for _, row in fresh.iterrows():
            tech, year = row.name
            capacity = row["capacity"]
            brand_new.append([tech, year, capacity])
        return pd.DataFrame(brand_new, columns=["technology", "year", "capacity"])

    regions = dataframe["region"].unique()
    agents = dataframe["agent"].unique()
    sectors = dataframe["sector"].unique()

    plots = []
    for region, agent, sector in list(product(regions, agents, sectors)):
        output = get_data(dataframe, region, agent, sector)
        techs = output["technology"].unique()
        data_dict = {}
        for tech in techs:
            data_dict[tech] = output.loc[(output["technology"] == tech)][
                ["year", "capacity"]
            ]
        plots.append(
            CapacityPlot(
                name=f"{region}_{agent}_{sector}",
                region=region,
                agent=agent,
                sector=sector,
                data=data_dict,
            )
        )
    return plots


@dataclass
class PricePlot:
    region: str
    data: Dict[str, pd.DataFrame]


def price_data_frame_to_plots(dataframe: pd.DataFrame) -> List[PricePlot]:
    def get_data(all_data: pd.DataFrame, region: str) -> pd.DataFrame:
        relevant_data = all_data.loc[(all_data["region"] == region)]
        relevant_data = relevant_data.groupby(["commodity", "year"], as_index=False)[
            "prices"
        ].sum()
        return relevant_data[["commodity", "year", "prices"]]

    regions = dataframe["region"].unique()
    plots = []
    for region in regions:
        output = get_data(dataframe, region)
        commodities = output["commodity"].unique()
        data_dict = {}
        for commodity in commodities:
            data_dict[commodity] = output.loc[(output["commodity"] == commodity)][
                ["year", "prices"]
            ]
        plots.append(PricePlot(region=region, data=data_dict))
    return plots
