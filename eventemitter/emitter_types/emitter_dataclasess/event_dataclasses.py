from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ..type_aliases import Event


@dataclass
class EventCallback:
    event_name: Event
    callback_args: Optional[Tuple[Any]]
    callback_kwargs: Optional[Dict[Any, Any]]
