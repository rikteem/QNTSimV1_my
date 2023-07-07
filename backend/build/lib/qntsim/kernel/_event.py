"""Definition of the Event class.

This module defines the Event class, which is executed by the timeline.
Events should be scheduled through the timeline to take effect.
"""

from math import inf
from typing import TYPE_CHECKING ,Any, List


if TYPE_CHECKING:
    from .process import Process


class Event:
    
    def __init__(self, time: int, owner: Any, activation_method: str, act_params: List[Any],priority=inf):
    
        self.time = time
        self._is_removed = False
        self.owner = owner
        self.activation = activation_method
        self.act_params = act_params
        self.priority = priority

    def __eq__(self, another):
        return (self.time == another.time) and (self.priority == another.priority)

    def __ne__(self, another):
        return (self.time != another.time) or (self.priority != another.priority)

    def __gt__(self, another):
        return (self.time > another.time) or (self.time == another.time and self.priority > another.priority)

    def __lt__(self, another):
        return (self.time < another.time) or (self.time == another.time and self.priority < another.priority)

        
    def run(self) -> None:
        return getattr(self.owner, self.activation)(*self.act_params)

    






