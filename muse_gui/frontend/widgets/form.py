from typing import Any, Callable, Dict, Optional, Tuple, Type

from pydantic import BaseModel
from PySimpleGUI.PySimpleGUI import Element

from .base import BaseWidget
from .utils import get_creator_and_updater_for_type, render


def get_creator_and_updater_for_model(
    model: Type[BaseModel],
) -> Tuple[
    Dict[str, Callable[..., Element]],
    Dict[str, Callable[..., Dict[str, Any]]],
]:

    if not issubclass(model, BaseModel):
        raise NotImplementedError
        return get_creator_and_updater_for_type(model)

    creator = {}
    updater = {}
    for k, v in model.__fields__.items():
        # If type is a class and is a basemodel
        if isinstance(v.type_, type) and issubclass(v.type_, BaseModel):
            _cf = Form(v.type_)
            _uf = None
        else:
            # Can be builtin type, or a typing type
            _cf, _uf = get_creator_and_updater_for_type(v.type_)
        creator[k] = _cf
        updater[k] = _uf

    return creator, updater


class Form(BaseWidget):
    _model: Type[BaseModel]

    def __init__(self, model: Type[BaseModel], key: Optional[str] = None):
        super().__init__(key)
        self._model = model
        self._creator, self._updater = get_creator_and_updater_for_model(model)
        self._layout = None
        self._disabled = False

    def _disable(self, window, disabled: bool):
        for k in self._creator:
            if isinstance(self._creator[k], Form):
                self._creator[k]._disable(window, disabled)
            else:
                _key = self._prefixf(k)
                window[_key].update(disabled=disabled)

    def disable(self, window):
        if not self._disabled:
            self._disable(window, True)
            self._disabled = True

    def enable(self, window):
        if self._disabled:
            self._disable(window, False)
            self._disabled = False

    def read(self, values_dict):
        values = {}
        for k in self._creator:
            if isinstance(self._creator[k], Form):
                values[k] = self._creator[k].read(values_dict)
            else:
                _key = self._prefixf(k)
                values[k] = values_dict[_key]
        return values

    def update(self, window, values: BaseModel):
        if not isinstance(values, self._model):
            raise TypeError()

        for k, v in values:
            if k not in self._creator:
                # Ignore keys that aren't present
                continue
            if isinstance(self._creator[k], Form):
                self._creator[k].update(window, v)
            else:
                _key = self._prefixf(k)
                _update_f = self._updater[k]
                window[_key].update(**_update_f(v))

    def layout(self, prefix, layout=None):
        if not self._layout:
            self.prefix = prefix
            if layout:
                all_keys = [
                    c if isinstance(c, str) else c[0] for r in layout if r for c in r
                ]
                dkeys = [k for k in self._creator if k not in all_keys]
                for k in dkeys:
                    self._creator.pop(k, None)
                    self._updater.pop(k, None)

            self._layout = render(self._creator, layout, self._prefixf())
        return self._layout

    def bind_handlers(self):
        pass
