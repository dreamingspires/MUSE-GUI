from typing import Dict, List
import pandas as pd
from dataclasses import dataclass
from itertools import product
import matplotlib.pyplot as plt

@dataclass
class Plot:
    region: str
    agent: str
    sector: str
    data: Dict[str, pd.DataFrame]


def data_frame_to_plots(dataframe: pd.DataFrame) -> List[Plot]:
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
        final_plots.append(Plot(region=region, agent=agent, sector=sector, data=data_dict))
    return final_plots

def plot_to_figure(plot: Plot) -> plt.Figure:
    assert len(plot.data) > 0
    fig = plt.figure(num = 3, figsize=(8, 5))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Capacity')
    ax.set_title(f'Region: {plot.region}, Agent: {plot.agent}, Sector: {plot.sector}')
    axes = []
    headers = []
    for tech, data in plot.data.items():
        y_vals = list(data['capacity'])
        x_vals = list(data['year'])
        new_ax = ax.plot(x_vals, y_vals)
        axes.append(new_ax)
        headers.append(tech)

    ax.legend(tuple([i[0] for i in axes]), tuple(headers))
    return fig

out = pd.read_csv('MCACapacity.csv')

final_plots = data_frame_to_plots(out)
for final_plot in final_plots:
    plot_to_figure(final_plot)
    plt.show()
