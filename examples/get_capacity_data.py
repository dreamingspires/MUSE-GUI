from itertools import product

import matplotlib.pyplot as plt
import pandas as pd

from muse_gui.backend.plots import capacity_data_frame_to_plots
from muse_gui.frontend.widget_funcs.plotting import capacity_plot_to_figure

out = pd.read_csv("MCACapacity.csv")

final_plots = capacity_data_frame_to_plots(out)
for final_plot in final_plots:
    capacity_plot_to_figure(final_plot)
    plt.show()
