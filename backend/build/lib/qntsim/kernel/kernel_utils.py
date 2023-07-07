"""Definition of EventList class.
This module defines the EventList class, used by the timeline to order and execute events.
EventList is implemented as a min heap ordered by simulation time.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._event import Event

from fibheap import *



class EventList:
    """Class of event list.
    This class is implemented as a min-heap. The event with the lowest time and priority is placed at the top of fibonacci heap.
    
    Attributes:
        data (Fheap()): fibonacci heap storing events as nodes (where node.key = event).
        nodesl(List[Node(event)]):list of all nodes .
    """

    def __init__(self): 
        self.data = makefheap()
        self.nodesl = []
        self.data_list = []

    def __len__(self):
        return self.data.num_nodes

    
    def push(self, event: "Event") -> "None":
        """Method to insert the event into heap ,maintaing min-heap structure.
        The event is converted to heap node , appended to nodesl and inserted into heap.
        """
        t = Node(event)
        self.nodesl.append(t)
        self.data.insert(t)
        self.data_list.append(event)

    def pop(self) -> "Event":
        """Method to extract minium node (i.e, event with min time )
        """
        return self.data.extract_min().key
        
    def isempty(self) -> bool:
        return self.data.num_nodes == 0

    def remove(self, event: "Event") -> None:
        """Method to remove events from heap.
        The event is set as the invalid state to save the time of removing event from heap.
        """
        event._is_removed=True
        self.data_list.remove(event)

    def update_event_time(self, event: "Event", time: int):
        """Method to update the timestamp of event and maintain the min-heap structure.
        Search for the event in nodesl,
        if event's time is needed to be:
             a) updated to an earlier time than that is scheduled -
                decrease_key(node ,key) method of fibonacci heap updates the event's time  while maintaining min-heap structure
             b) updated to an later time than that is scheduled -
                using decrease_key(node ,key) method of fibonacci heap change the event's time to -1,
                hence making it min node ,extract it from heap ,update event's time and insert into heap.
        """  
        if time == event.time:
            return

        for node in self.nodesl:
            if node.key==event:
                if event.time > time :
                    event.time = time
                    self.data.decrease_key(node, event)
                
                elif event.time < time:
                    event.time = -1
                    self.data.decrease_key(node, event)
                    self.data.extract_min()
                    event.time=time
                    t = Node(event)
                    self.nodesl.append(t)
                    self.data.insert(t)
                break
    
    def filter_events(self):
        events = [(event.owner,event.activation, event.act_params[1]) if len(event.act_params)>0 else (event.owner,event.activation) for event in self.data_list]
        return events