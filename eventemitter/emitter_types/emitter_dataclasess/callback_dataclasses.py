from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Tuple, Union


@dataclass
class CallbackData:
    callback: Union[Callable, Awaitable]
    callback_args: Tuple[Any] = field(default_factory=tuple)
    callback_kwargs: Dict[Any, Any] = field(default_factory=dict)
