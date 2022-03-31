from pathlib import Path
from typing import Tuple

import PySimpleGUI as sg


def boot_waiting_window(font, datastore) -> Tuple[Path, Path]:
    window = sg.Window(
        "Waiting",
        [[sg.Text("Calculating MUSE")]],
        resizable=True,
        font=font,
        auto_size_text=True,
        finalize=True,
        element_justification="c",
    )
    prices_path, capacity_path = datastore.run_muse()
    window.close()
    return prices_path, capacity_path
