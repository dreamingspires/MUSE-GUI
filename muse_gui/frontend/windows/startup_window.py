from typing import Optional, Tuple

import PySimpleGUI as sg


def boot_initial_window(font) -> Tuple[Optional[bool], Optional[str]]:
    layout = [
        [
            sg.Col(
                [
                    [
                        sg.FileBrowse(
                            "Import Toml",
                            key=True,
                            font=font,
                            size=(15, 4),
                            enable_events=True,
                        )
                    ]
                ],
                pad=1,
            ),
            sg.Col(
                [[sg.Button("Start New Project", key=False, font=font, size=(15, 4))]],
                pad=1,
            ),
        ]
    ]
    window = sg.Window(
        "Start Screen", layout, resizable=True, finalize=True, element_justification="c"
    )
    event, values = window.read()
    if event is True:
        file_path = values[True]
    else:
        file_path = None

    window.close()
    if event == sg.WIN_CLOSED:
        return None, None
    return event, file_path
