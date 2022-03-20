from enum import Enum
import PySimpleGUI as sg
from functools import partial
from typing import Dict, Callable, Union

from .base import BaseWidget


def get_all_keys(d: Dict):
    return list(d.keys()) + [x for v in d.values() if isinstance(v, dict) for x in get_all_keys(v)]


def get_optionmenu_for_enum(_enum: Enum):
    values = [f'{x}' for x in _enum]
    default_value = values[0]
    size = 2 + max([len(x) for x in values])
    return partial(
        sg.OptionMenu,
        values,
        default_value=default_value,
        size=(size, 1),
        expand_x=False,
        expand_y=False,
    ), identity


def identity(x): return {'value': x}


registry = {
    Enum: get_optionmenu_for_enum,
    int: lambda _: (partial(sg.Input, '', size=(8, 1), justification='right'), identity),
    float: lambda _: (partial(sg.Input, '', size=(8, 1), justification='right'), identity),
    str: lambda _: (partial(sg.Input, '', size=(25, 1), justification='left'), identity),
}

# TODO Cache for type / put it in registry?


def get_creator_and_updater_for_type(_type):
    # Get direct match if any
    f = registry.get(_type, None)
    if f == None:
        f = next((v for x, v in registry.items() if isinstance(
            _type, type) and issubclass(_type, x)), lambda _: (partial(sg.Text), identity))

    return f(_type)


def render(
        field_creator: Dict[str, Union[Callable, BaseWidget]],
        _layout=None,
        _prefix=None):

    prefix = _prefix or tuple()

    def prefixf(k):
        return prefix + ((k, ) if k else tuple())

    if not _layout:
        default_layout = [[k] for k in field_creator]
        return render(field_creator, default_layout)

    final_layout = []

    # Normalize layout children
    assert all(all(isinstance(c, (str, tuple)) for c in r)
               for r in _layout), 'Layout only accepts string and tuple'
    layout = [[(c, ) if isinstance(c, str) else c for c in r] for r in _layout]

    all_keys = [c[0] for r in layout if r for c in r]
    max_length = max([len(x) for x in all_keys])
    char_length = max_length if max_length < 10 else round(
        0.9*max_length)  # Magic!

    for r in layout:
        if not r:
            # Empty row
            final_layout.append([sg.Text('')])
            continue
        _row = []
        for c in r:

            key, *child = c
            if key == 'sep':
                _row.append(sg.HorizontalSeparator())
                continue

            if key not in field_creator:
                raise KeyError()

            _key = prefixf(key)
            display = key.replace('_', ' ').strip().title()
            if not isinstance(field_creator[key], BaseWidget):
                # No submodel to be rendered
                _row.extend([
                    sg.Text(f'{display:<{char_length}}',
                            size=(char_length, 1)),
                    sg.Text(':', auto_size_text=True),
                    field_creator[key](key=_key)
                ])
                continue

            # There is a subtree to be rendered
            if not child:
                child = [('col',)]

            container, *child = child[0]
            cf = sg.Col if container == 'col' else sg.Frame
            cl = child[0] if child else None

            inner_layout = cf(([
                [sg.Text(display, auto_size_text=True),
                 sg.HorizontalSeparator()]
            ] +
                field_creator[key].layout(prefix=_key, layout=cl) +
                [[sg.Text('')]]
            ), expand_x=True)
            _row.append(inner_layout)
        final_layout.append(_row)
    return final_layout
