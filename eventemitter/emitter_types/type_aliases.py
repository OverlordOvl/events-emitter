from typing import Callable, DefaultDict, List

from .emitter_dataclasess.callback_dataclasses import CallbackData
from .enums.base_enum import BaseEnum


Event = str or BaseEnum
Callback = Callable or CallbackData
EventsStorage = DefaultDict[Event, List[CallbackData]]
