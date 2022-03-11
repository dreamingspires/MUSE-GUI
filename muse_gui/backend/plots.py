from typing import Dict, List
import pandas as pd
from dataclasses import dataclass
from itertools import product

@dataclass
class CapacityPlot:
    region: str
    agent: str
    sector: str
    data: Dict[str, pd.DataFrame]


def capacity_data_frame_to_plots(dataframe: pd.DataFrame) -> List[CapacityPlot]:
    def get_data(all_data: pd.DataFrame, region: str, agent: str, sector: str) -> pd.DataFrame:
        relevant_data = all_data.loc[(all_data['region'] == region) & (all_data['agent'] == agent) &  (all_data['sector'] == sector)]
        return relevant_data[['technology', 'year', 'capacity']]

    regions = dataframe['region'].unique()
    agents = dataframe['agent'].unique()
    sectors = dataframe['sector'].unique()

    final_plots = []
    for region, agent, sector in list(product(regions, agents, sectors)):
        output = get_data(dataframe, region, agent, sector)
        techs = output['technology'].unique()
        data_dict = {}
        for tech in techs:
            data_dict[tech] = output.loc[(output['technology'] == tech) ][['year', 'capacity']]
        final_plots.append(CapacityPlot(region=region, agent=agent, sector=sector, data=data_dict))
    return final_plots
