"""Definitions of node types.
This module provides definitions for various types of quantum network nodes.
All node types inherit from the base Node type, which inherits from Entity.
Node types can be used to collect all the necessary hardware and software for a network usage scenario.
"""

from math import inf
from time import monotonic_ns
from typing import TYPE_CHECKING, Any , List

if TYPE_CHECKING:
    #from ..kernel.timeline import Timeline
    from ..message import Message
    from ..protocol import StackProtocol
    from ..resource_management.memory_manager import MemoryInfo
    from ..network_management.reservation import Reservation
    from ..components.optical_channel import QuantumChannel, ClassicalChannel
#from ..kernel.timeline import DLCZ ,bk
from ..kernel.timeline import Timeline
if Timeline.DLCZ:
    from ..components.DLCZ_memory import Memory,MemoryArray
    from ..components.DLCZ_bsm import SingleAtomBSM
    print("DLCZ node")
elif Timeline.bk:
    from ..components.bk_memory import Memory, MemoryArray
    from ..components.bk_bsm import SingleAtomBSM
    print("bk node")

from ..kernel.entity import Entity

from ..components.light_source import LightSource, SPDCSource2
from ..components.detector import QSDetectorPolarization, QSDetectorTimeBin
from ..resource_management.resource_manager import ResourceManager
from ..transport_layer.transport_manager import TransportManager
from ..utils.encoding import *
from ..network_management.request import RRPMsgType
from ..network_management.network_manager import NetworkManager
from .message_queue_handler import MessageQueueHandler
from ..resource_management.task_manager import TaskManager
from ..resource_management.resource_manager import MsgRecieverType ,ResourceManagerMsgType

"""
def force_import(backend):

    if backend=="DLCZ":
        from ..components.DLCZ_memory import Memory,MemoryArray
        from ..components.DLCZ_bsm import SingleAtomBSM
        #print("DLCZ node")
    elif backend=="bk" :
        from ..components.bk_memory import Memory, MemoryArray
        from ..components.bk_bsm import SingleAtomBSM
"""
class Node(Entity):

    """Base node type.
    
    Provides default interfaces for network.
    Attributes:
        name (str): label for node instance.
        timeline (Timeline): timeline for simulation.
        cchannels (Dict[str, ClassicalChannel]): mapping of destination node names to classical channel instances.
        qchannels (Dict[str, ClassicalChannel]): mapping of destination node names to quantum channel instances.
        protocols (List[Protocol]): list of attached protocols.
    """

    def __init__(self, name: str, timeline: "Timeline"):
        """Constructor for node.
        name (str): name of node instance.
        timeline (Timeline): timeline for simulation.
        """

        Entity.__init__(self, name, timeline)
        self.owner = self
        self.cchannels = {}  # mapping of destination node names to classical channels
        self.qchannels = {}  # mapping of destination node names to quantum channels
        self.protocols = []
        self.virtual_links = {} # node: [subtask] for more than one virtual links between a pair of nodes
        self.snapshots = []##TODO:Enhance way to store snapshots
        self.qubit_buffer = {1: []}
        self.all_pair_shortest_dist = None
        self.neighbors = None

    def init(self) -> None:
        pass

    def assign_cchannel(self, cchannel: "ClassicalChannel", another: str) -> None:
        """Method to assign a classical channel to the node.
        This method is usually called by the `ClassicalChannel.add_ends` method and not called individually.
        Args:
            cchannel (ClassicalChannel): channel to add.
            another (str): name of node at other end of channel.
        """

        self.cchannels[another] = cchannel

    def assign_qchannel(self, qchannel: "QuantumChannel", another: str) -> None:
        """Method to assign a quantum channel to the node.
        This method is usually called by the `QuantumChannel.add_ends` method and not called individually.
        Args:
            qchannel (QuantumChannel): channel to add.
            another (str): name of node at other end of channel.
        """

        self.qchannels[another] = qchannel

    

    def receive_message(self, src: str, msg: "Message") -> None:
        """Method to receive message from classical channel.
        Searches through attached protocols for those matching message, then invokes `received_message` method of protocol(s).
        Args:
            src (str): name of node sending the message.
            msg (Message): message transmitted from node.
        """

        # signal to protocol that we've received a message
        # #print('node msg', msg)
        if msg.receiver is not None:
            #print("rrrrrr")
            for protocol in self.protocols:
                #print('protocol', protocol)
                if protocol.name == msg.receiver and protocol.received_message(src, msg):
                    return
        else:
            #print("rrrrrr")
            matching = [p for p in self.protocols if type(p) == msg.protocol_type]
            for p in matching:
                p.received_message(src, msg)

    def schedule_qubit(self, dst: str, min_time: int) -> int:
        """Interface for quantum channel `schedule_transmit` method."""

        return self.qchannels[dst].schedule_transmit(min_time)

    def send_qubit(self, dst: str, qubit, app = 1) -> None:
        """Interface for quantum channel `transmit` method."""
        ##print(f'sent qubit from node: {self.name} to node: {dst}')
        # #print((dst), type(qubit))
        # #print("qchannels", self.qchannels)
        #Find the next hop using the cached flloyd-warshall output
        next_hop, min_dist = None, inf
        
        #If dst is the BSM node, it will be present in channels map but not in neigbors map
        if dst in self.qchannels.keys() and dst not in self.neighbors:
            #For Entanglement
            next_hop = dst
        else:
            #For Direct Transmission
            for neighbor in self.neighbors:
                print(f'Looping over neighbors: {neighbor}')
                if  self.all_pair_shortest_dist[neighbor][dst]< min_dist:
                    next_hop = neighbor
                    min_dist = self.all_pair_shortest_dist[neighbor][dst]
        
        if next_hop != None:
            self.qchannels[next_hop].init()
            self.qchannels[next_hop].transmit(self.name, qubit, dst, app, self)
        else:
            print('Error: Next Hop not Found')

    def receive_qubit(self, _from:str, dst:str, app:str, qubit) -> None:
        """Method to receive qubits from quantum channel (does nothing for this class)."""

        """
            If this node is the dst:
                pass this qubit to the application
            else:
                find the next hop using the djiksta algo and push this along the path
        """
        if dst == self.name:
            self.qubit_buffer[app].append(qubit)
        else:
            self.send_qubit(dst, qubit)


class BSMNode(Node):
    """Bell state measurement node.
    This node provides bell state measurement and the EntanglementGenerationB protocol for entanglement generation.
    Attributes:
        name (str): label for node instance.
        timeline (Timeline): timeline for simulation.
        bsm (SingleAtomBSM): BSM instance object.
        eg (EntanglementGenerationB): entanglement generation protocol instance.
    """

    def __init__(self, name: str, timeline: "Timeline", other_nodes: List[str]) -> None:
        """Constructor for BSM node.
        Args:
            name (str): name of node.
            timeline (Timeline): simulation timeline.
            other_nodes (str): 2-member list of node names for adjacent quantum routers.
        """
        from ..kernel.timeline import Timeline
        if Timeline.DLCZ:
            #print('DLCZ node egb')
            from ..entanglement_management.DLCZ_generation import EntanglementGenerationB
        elif Timeline.bk:
            from ..entanglement_management.bk_generation import EntanglementGenerationB
        Node.__init__(self, name, timeline)
        self.bsm = SingleAtomBSM("%s_bsm" % name, timeline)
        self.eg = EntanglementGenerationB(self, "{}_eg".format(name), other_nodes)
        self.bsm.attach(self.eg)
        self.message_handler = MessageQueueHandler(self)
        
    def receive_message(self, src: str, msg: "Message") -> None:
        # signal to protocol that we've received a message
        # #print("protocols on bsm: ", self.protocols)
        #for protocol in self.protocols:
            #protocol.received_message(src, msg)
            # if type(protocol) == msg.owner_type:
            #     if protocol.received_message(src, msg):
            #         return

        # if we reach here, we didn't successfully receive the message in any protocol
        ###print(src, msg)
        # raise Exception("Unkown protocol")
    
        self.message_handler.push_message(src,msg)

    def receive_qubit(self, _from:str, dst:str, app:str, qubit):
        """Method to receive qubit from quantum channel.
        Invokes get method of internal bsm with `qubit` as argument.
        Args:
            src (str): name of node where qubit was sent from.
            qubit (any): transmitted qubit.
        """
        ##print(f'optical_channel at node: {self.name}, recv qubit from {src}')
        self.bsm.get(qubit)

    def eg_add_others(self, other):
        """Method to addd other protocols to entanglement generation protocol.
        Args:
            other (EntanglementProtocol): other entanglement protocol instance.
        """

        self.eg.others.append(other.name)

class MemoryTimeCard():
    """Class for tracking reservations on a specific memory.
    Attributes:
        memory_index (int): index of memory being tracked (in memory array).
        reservations (List[Reservation]): list of reservations for the memory.
    """

    def __init__(self, memory_index: int):
        """Constructor for time card class.
        Args:
            memory_index (int): index of memory to track.
        """

        self.memory_index = memory_index
        self.reservations = []
    
    def has_virtual_reservation(self):
        # print('len of res', len(self.reservations))
        for res in self.reservations:
            # print('inside has virtual reservation',res.initiator,res.responder)
            if res.isvirtual:
                # print('res.isvirtual',res.isvirtual)
                return True
        return False



class EndNode(Node):

    def __init__(self, name: str, timeline: "Timeline", memo_size=500):
        super().__init__(name, timeline)
        self.memo_size = memo_size
        self.memory_array = MemoryArray(name + ".MemoryArray", timeline, num_memories=memo_size)
        self.memory_array.owner = self
        self.message_handler = MessageQueueHandler(self)
        self.reservation_manager = []
        self.task_manager = TaskManager(self)
        self.network_manager = NetworkManager(self)
        self.resource_manager = ResourceManager(self)
        self.transport_manager = TransportManager(self)
        self.is_endnode = True
        self.service_node = None
        self.app = None
        self.nx_graph = None
        # self.all_pair_shortest_dist = None
        self.all_neighbor={}
        # self.neighbors = None
        self.random_seed = None
        self.virtualneighbors=[]
        self.delay_graph=None
        self.neighborhood_list=None
        self.marker=None
        self.vmemory_list=[MemoryTimeCard(i) for i in range(len(self.memory_array))]
        self.map_to_middle_node = {}
        self.lightsource = SPDCSource2(self, name, timeline)
    #--------------------------------------------------------------------------
    def find_virtual_neighbors(self):
        virtual_neighbors = {}

        #Check the memory of this node for existing entanglements
        for info in self.resource_manager.memory_manager:
            
            if info.state != 'ENTANGLED':
                continue
            else:
                ##print((node, info.remote_node))
                #This is a virtual neighbor
                #nx_graph.add_edge(node, str(info.remote_node), color='r')
                if str(info.remote_node) in virtual_neighbors.keys():
                    virtual_neighbors[str(info.remote_node)] = virtual_neighbors[str(info.remote_node)] + 1
                else:
                    virtual_neighbors[str(info.remote_node)] = 1

        return virtual_neighbors
    #--------------------------------------------------------------------------
    
    def receive_message(self, src: str, msg: "Message") -> None:
        # print('receive msg', msg.receiver,msg.protocol_type)
        #print("Quantum roter receive message")
        #if hasattr(msg, 'id'):
            #if msg.id == 1:
                #print('BSM_MSG_RECV_TIME: ', self.timeline.now(), ' at node: ', self.name)
            #if msg.id == 2:
                #print('REQ_FUNC_RECV_TIME: ', self.timeline.now(), ' at node: ', self.name)

        self.message_handler.push_message(src,msg)

    def init(self):
        """Method to initialize quantum router node.
        Sets up map_to_middle_node dictionary.
        """

        super().init()
        for dst in self.qchannels:
            end = self.qchannels[dst].receiver
            if isinstance(end, BSMNode):
                for other in end.eg.others:
                    if other != self.name:
                        self.map_to_middle_node[other] = end.name
        # print('self to middel',self.map_to_middle_node)

    def get_idle_memory(self, info: "MemoryInfo") -> None:
        """Method for application to receive available memories."""

        if self.app:
            self.app.get_memory(info)


class ServiceNode(Node):

    def __init__(self,name: str, timeline: "Timeline",memo_size=500):
        super().__init__(name, timeline)
        self.memory_array = MemoryArray(name + ".MemoryArray", timeline, num_memories=memo_size)
        self.memory_array.owner = self
        self.message_handler = MessageQueueHandler(self)
        self.reservation_manager = []
        self.network_manager = NetworkManager(self)
        self.resource_manager = ResourceManager(self)
        self.transport_manager = TransportManager(self)
        self.task_manager = TaskManager(self)
        self.app = None
        self.end_node = None
        self.is_endnode = False
        # self.neighbors = None
        self.nx_graph = None
        # self.all_pair_shortest_dist = None
        self.all_neighbor={}
        self.random_seed = None
        self.virtualneighbors=[]
        self.delay_graph=None
        self.neighborhood_list=None
        self.marker=None
        self.vmemory_list=[MemoryTimeCard(i) for i in range(len(self.memory_array))]
        self.map_to_middle_node = {}
        self.lightsource = SPDCSource2(self, name, timeline)
        
    def receive_message(self, src: str, msg: "Message") -> None:
        self.message_handler.push_message(src,msg)

    def find_virtual_neighbors(self):
        virtual_neighbors = {}

        #Check the memory of this node for existing entanglements
        for info in self.resource_manager.memory_manager:
            
            if info.state != 'ENTANGLED':
                continue
            else:
                ##print((node, info.remote_node))
                #This is a virtual neighbor
                #nx_graph.add_edge(node, str(info.remote_node), color='r')
                if str(info.remote_node) in virtual_neighbors.keys():
                    virtual_neighbors[str(info.remote_node)] = virtual_neighbors[str(info.remote_node)] + 1
                else:
                    virtual_neighbors[str(info.remote_node)] = 1

        return virtual_neighbors

    def init(self):
        """Method to initialize quantum router node.
        Sets up map_to_middle_node dictionary.
        """

        super().init()
        for dst in self.qchannels:
            end = self.qchannels[dst].receiver
            if isinstance(end, BSMNode):
                for other in end.eg.others:
                    if other != self.name:
                        self.map_to_middle_node[other] = end.name


    def get_idle_memory(self, info: "MemoryInfo") -> None:
        """Method for application to receive available memories."""

        if self.app:
            self.app.get_memory(info)        

# class QuantumRouter(Node):
#     """Node for entanglement distribution networks.

#     This node type comes pre-equipped with memory hardware, along with the default SeQUeNCe modules (sans application).

#     Attributes:
#         name (str): label for node instance.
#         timeline (Timeline): timeline for simulation.
#         memory_array (MemoryArray): internal memory array object.
#         resource_manager (ResourceManager): resource management module.
#         network_manager (NetworkManager): network management module.
#         map_to_middle_node (Dict[str, str]): mapping of router names to intermediate bsm node names.
#         app (any): application in use on node.
#     """

#     def __init__(self, name, tl, memo_size=50):
#         """Constructor for quantum router class.

#         Args:
#             name (str): label for node.
#             tl (Timeline): timeline for simulation.
#             memo_size (int): number of memories to add in the array (default 50).
#         """

#         Node.__init__(self, name, tl)
#         self.memory_array = MemoryArray(name + ".MemoryArray", tl, num_memories=memo_size)
        
#         self.memory_array.owner = self
#         self.reservation_manager=[]
#         self.resource_manager = ResourceManager(self)
#         self.network_manager = NetworkManager(self)
#         self.transport_manager=TransportManager(self)
#         self.message_handler = MessageQueueHandler(self)
#         self.map_to_middle_node = {}
#         self.app = None
#         self.lightsource = SPDCSource2(self, name, tl)
#         #-------------------------------------
#         self.all_pair_shortest_dist = None
#         self.all_neighbor={}
#         self.neighbors = None
#         self.random_seed = None
#         self.virtualneighbors=[]
#         self.nx_graph=None
#         self.delay_graph=None
#         self.neighborhood_list=None
#         self.marker=None
#         self.vmemory_list=[MemoryTimeCard(i) for i in range(len(self.memory_array))]
#         #-------------------------------------

#     #--------------------------------------------------------------------------
#     def find_virtual_neighbors(self):
#         virtual_neighbors = {}
#         virtual_neighbor=[]
#         #Check the memory of this node for existing entanglements
#         for info in self.resource_manager.memory_manager:
            
#             if info.state != 'ENTANGLED':
#                 continue
#             else:
#                 ###print((node, info.remote_node))
#                 #This is a virtual neighbor
#                 #nx_graph.add_edge(node, str(info.remote_node), color='r')
#                 if str(info.remote_node) in virtual_neighbors.keys():
#                     # #print('remotre',info.remote_node,virtual_neighbors)
#                     virtual_neighbors[str(info.remote_node)] = virtual_neighbors[str(info.remote_node)] + 1
#                 else:
#                     virtual_neighbors[str(info.remote_node)] = 1
#             # virtual_neighbor=[info.remote_node,self.name]
#             # #print('findvirtualneighbors',virtual_neighbors,self.name,info.remote_node)
#         return virtual_neighbors
#     #--------------------------------------------------------------------------
    
#     def receive_message(self, src: str, msg: "Message") -> None:
#         # #print('receive msg', msg.receiver,msg.protocol_type)
#         ##print("Quantum roter receive message")
#         self.message_handler.push_message(src,msg)

#     def init(self):
#         """Method to initialize quantum router node.

#         Sets up map_to_middle_node dictionary.
#         """

#         super().init()
#         for dst in self.qchannels:
#             end = self.qchannels[dst].receiver
#             if isinstance(end, BSMNode):
#                 for other in end.eg.others:
#                     if other != self.name:
#                         self.map_to_middle_node[other] = end.name

#     def memory_expire(self, memory: "Memory") -> None:
#         """Method to receive expired memories.

#         Args:
#             memory (Memory): memory that has expired.
#         """

#         self.resource_manager.memory_expire(memory)

#     def reserve_net_resource(self, responder: str, start_time: int, end_time: int, memory_size: int,
#                              target_fidelity: float) -> None:
#         """Method to request a reservation.

#         Args:
#             responder (str): name of the node with which entanglement is requested.
#             start_time (int): desired simulation start time of entanglement.
#             end_time (int): desired simulation end time of entanglement.
#             memory_size (int): number of memories requested.
#             target_fidelity (float): desired fidelity of entanglement.
#         """

#         self.network_manager.request(responder, start_time, end_time, memory_size, target_fidelity)

#     def get_idle_memory(self, info: "MemoryInfo") -> None:
#         """Method for application to receive available memories."""

#         if self.app:
#             self.app.get_memory(info)

#     def get_reserve_res(self, reservation: "Reservation", res: bool) -> None:
#         """Method for application to receive reservations results."""

#         if self.app:
#             self.app.get_reserve_res(reservation, res)

#     def get_other_reservation(self, reservation: "Reservation"):
#         """Method for application to get another reservation."""

#         if self.app:
#             self.app.get_other_reservation(reservation)