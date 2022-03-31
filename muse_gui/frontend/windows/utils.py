from typing import Tuple

import PySimpleGUI as sg

Font = Tuple[str, int]


def configure_theme() -> Font:
    light = "#E7F5F9"
    dark = "#D8EEF4"
    darker = "#CEEAF2"
    black = "#000000"
    custom_theme = {
        "BACKGROUND": light,
        "TEXT": black,
        "INPUT": dark,
        "TEXT_INPUT": black,
        "SCROLL": "#c7e78b",
        "BUTTON": ("white", "#709053"),
        "PROGRESS": ("#01826B", "#D0D0D0"),
        "BORDER": 2,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
    }

    sg.theme_add_new("CustomTheme", custom_theme)
    sg.theme("CustomTheme")
    font = ("Arial", 14)
    return font
