from itertools import product

import matplotlib.pyplot as plt
import pandas as pd

from muse_gui.backend.plots import price_data_frame_to_plots
from muse_gui.frontend.widget_funcs.plotting import price_plot_to_figure

out = pd.read_csv("MCAPrices.csv")
price_plots = price_data_frame_to_plots(out)

for final_plot in price_plots:
    price_plot_to_figure(final_plot)
    plt.show()
