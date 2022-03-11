import csv
from typing import Dict
import pandas as pd
from dataclasses import dataclass
from itertools import product
import matplotlib.pyplot as plt
import numpy as np
@dataclass
class Plot:
    region: str
    agent: str
    sector: str
    data: Dict[str, pd.DataFrame]


out = pd.read_csv('MCACapacity.csv')
regions = out['region'].unique()
agents = out['agent'].unique()
sectors = out['sector'].unique()

plots = list(product(regions, agents, sectors))

def get_data(all_data: pd.DataFrame, region: str, agent: str, sector: str) -> pd.DataFrame:
    relevant_data = all_data.loc[(all_data['region'] == region) & (all_data['agent'] == agent) &  (all_data['sector'] == sector)]
    return relevant_data[['technology', 'year', 'capacity']]

final_plots = []
for region, agent, sector in list(product(regions, agents, sectors)):
    output = get_data(out, region, agent, sector)
    techs = output['technology'].unique()
    data_dict = {}
    for tech in techs:
        data_dict[tech] = output.loc[(output['technology'] == tech) ][['year', 'capacity']]
    final_plots.append(Plot(region=region, agent=agent, sector=sector, data=data_dict))
print(final_plots)


test_plot = final_plots[0]

line1 = test_plot.data['heatpump']
x = list(line1['year'])
y = list(line1['capacity'])

y1 = y
y2 = y

fig = plt.figure(num = 3, figsize=(8, 5))
ax = fig.add_subplot(1,1,1)
ax0 = ax.plot(x, y2)
ax1 = ax.plot(x, y1, 
         color='red',   
         linewidth=1.0,  
         linestyle='--',
        )
ax.legend((ax0[0], ax1[0]), ('Data Group 1','DataGroup2'),)

plt.show()


"""
values_to_plot = (20, 35, 30, 35, 27)
ind = np.arange(len(values_to_plot))
width = 0.4
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
p1 = ax.bar(ind, values_to_plot, width)
ax.set_xlabel('xaxis')
ax.set_ylabel('yaxis')
ax.set_title('title')
ax.set_xticks(ind, ('Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5'))
ax.set_yticks(np.arange(0, 81, 10))
ax.legend((p1[0],), ('Data Group 1',))

plt.show()
"""