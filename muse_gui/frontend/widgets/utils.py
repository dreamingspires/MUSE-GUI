from enum import Enum
from functools import partial
from typing import Any, Callable, Dict, List, Tuple, Type, Union

import PySimpleGUI as sg
from PySimpleGUI import Element

from .base import BaseWidget


def get_all_keys(d: Dict) -> List:
    return list(d.keys()) + [
        x for v in d.values() if isinstance(v, dict) for x in get_all_keys(v)
    ]


def get_btn_maker(text, **kwargs):
    return partial(sg.Button, text, **kwargs)


def get_optionmenu_for_enum(
    _enum: Type[Enum],
) -> Tuple[Callable[..., Element], Callable[..., Dict[str, Any]]]:
    values = [f"{x}" for x in _enum]
    default_value = values[0]
    size = 2 + max([len(x) for x in values])
    return (
        partial(
            sg.OptionMenu,
            values,
            default_value=default_value,
            size=(size, 1),
            expand_x=False,
            expand_y=False,
        ),
        identity,
    )


def identity(x):
    return {"value": x}


num_input_func = partial(sg.Input, "", size=(8, 1), justification="right")
string_input_func = partial(sg.Input, "", size=(25, 1), justification="left")

registry = {
    int: (num_input_func, identity),
    float: (num_input_func, identity),
    str: (string_input_func, identity),
}


def get_creator_and_updater_for_type(
    _type: Any,
) -> Tuple[Callable[..., Element], Callable[..., Dict[str, Any]]]:
    # Get direct match if any

    if isinstance(_type, type) and issubclass(_type, Enum):
        return get_optionmenu_for_enum(_type)
    if _type in registry:
        return registry[_type]

    creator_f = next(
        (
            v
            for x, v in registry.items()
            if isinstance(_type, type) and issubclass(_type, x)
        ),
        None,
    )
    if creator_f:
        return creator_f
    else:
        return partial(sg.Text), identity


def render(
    field_creator: Dict[str, Union[Callable[..., Element], BaseWidget]],
    _layout=None,
    _prefix=None,
) -> List[List[Element]]:

    prefix = _prefix or tuple()

    def prefixf(k):
        return prefix + ((k,) if k else tuple())

    if not _layout:
        default_layout = [[k] for k in field_creator]
        return render(field_creator, default_layout, prefix)

    final_layout = []

    # Normalize layout children
    assert all(
        all(isinstance(c, (str, tuple)) for c in r) for r in _layout
    ), "Layout only accepts string and tuple"
    layout = [[(c,) if isinstance(c, str) else c for c in r] for r in _layout]

    all_keys = [c[0] for r in layout if r for c in r]
    max_length = max([len(x) for x in all_keys])
    char_length = (
        max(max_length, 7) if max_length < 12 else round(0.9 * max_length)
    )  # Magic!

    for r in layout:
        if not r:
            # Empty row
            final_layout.append([sg.Text("")])
            continue
        _row = []
        for c in r:

            key, *child = c
            if key == "sep":
                _row.append(sg.HorizontalSeparator())
                continue

            if key not in field_creator:
                raise KeyError(f"{key} not present in field_creator {field_creator}")

            _key = prefixf(key)
            display = key.replace("_", " ").strip().title()
            if not isinstance(field_creator[key], BaseWidget):
                # No submodel to be rendered
                creator = field_creator[key]
                if isinstance(creator, BaseWidget):
                    raise NotImplementedError
                else:
                    assert isinstance(creator, partial)
                    _row.extend(
                        [
                            sg.Text(f"{display:<{char_length}}", size=(char_length, 1)),
                            sg.Text(":", auto_size_text=True),
                            creator(key=_key),
                        ]
                    )
                    continue

            # There is a subtree to be rendered
            if not child:
                child = [("col",)]

            container, *child = child[0]
            cf = sg.Col if container == "col" else sg.Frame
            cl = child[0] if child else None

            inner_layout = cf(
                (
                    [[sg.Text(display, auto_size_text=True), sg.HorizontalSeparator()]]
                    + field_creator[key].layout(prefix=_key, layout=cl)
                    + [[sg.Text("")]]
                )
            )
            _row.append(inner_layout)
        final_layout.append(_row)
    return final_layout
