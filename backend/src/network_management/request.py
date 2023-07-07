from typing import TYPE_CHECKING, List

from pyparsing import Path

if TYPE_CHECKING:
    from ..topology.node import QuantumRouter,Node

from enum import Enum, auto

#from ..network_management.network_manager import NetworkManagerMessage
import networkx as nx

from ..kernel._event import Event
from ..kernel.timeline import Timeline
from ..message import Message
from ..resource_management.rule_manager import Rule

if Timeline.DLCZ:
    from ..entanglement_management.DLCZ_generation import \
        EntanglementGenerationA
    from ..entanglement_management.DLCZ_purification import BBPSSW
    from ..entanglement_management.DLCZ_swapping import (EntanglementSwappingA,
                                                         EntanglementSwappingB)
elif Timeline.bk:
    from ..entanglement_management.bk_generation import EntanglementGenerationA
    from ..entanglement_management.bk_purification import BBPSSW
    from ..entanglement_management.bk_swapping import EntanglementSwappingA, EntanglementSwappingB

import itertools
import json
import logging
import math

from ..resource_management.memory_manager import MemoryInfo, MemoryManager
from ..resource_management.task_manager import SubTask, Task, TaskManager
from ..topology.message_queue_handler import (ManagerType, MsgRecieverType,
                                              ProtocolType)

logger = logging.getLogger("main_logger.network_layer." + "request")
#from ..transport_layer.transport_manager import CongestionMsgType


class Request():


    newid=itertools.count()
    
    def __init__(self, initiator:str,responder: str, start_time: int, end_time: int, memory_size: int, target_fidelity: float,**kwargs):        
        self.initiator  = initiator
        self.responder  = responder
        self.start_time = start_time
        self.end_time = end_time
        self.memory_size=memory_size
        self.fidelity = target_fidelity
        # self.priority = priority
        # self.tp_id = tp_id
        if "priority" in kwargs:
            self.priority=kwargs["priority"]
        if "tp_id" in kwargs:
            self.tp_id=kwargs["tp_id"]
        self.path=[] #doubly linked list of Nodes (List(Nodes))
        self.pathnames=[]
        self.status=None
        # if "isvirtual" in kwargs:
        self.isvirtual=kwargs.get("isvirtual", False)
        self.id=next(self.newid)
        self.congestion=0
        self.congestion_retransmission=kwargs.get("congestion_retransmission",None)
        # if "congestion_retransmission" in kwargs:
        #     self.congestion_retransmission=kwargs["congestion_retransmission"]
        self.remaining_demand_size=0




class RoutingProtocol():
    
    def __init__(self, node: "Node", initiator:str,responder: str,temp_path:"List(Node)",marker:"Node"):
        """Constructor for routing protocol.
        Args:
            own (Node): node protocol is attached to.
            name (str): name of protocol instance.
            
            def __init__(self, own: "Node", name: str):
        
        """
        self.local_neighbor_table={} 
        self.node=node
        self.src=initiator
        self.dst=responder
        self.temp_path=temp_path
        self.marker=marker

    def setattributes(self,curr_node):
        '''Method to set the local neighborhood, distances, physical graphs and virtual link information'''
        
        """
        nodewise_dest_distance: dictionary of distance of a node with other nodes of the topology
        neighbors,vneighbors and nx_graph are attributes of node class.
        """

        all_pair_path = self.node.all_pair_shortest_dist
        all_pair_path=json.loads(json.dumps(all_pair_path))
        nodewise_dest_distance = all_pair_path[curr_node]
        nodewise_dest_distance = json.loads(json.dumps(nodewise_dest_distance))
        neighbors = self.node.neighbors
        vneighbors=self.node.virtualneighbors
        # #print('virtual neighbors',vneighbors,self.own.timeline.now()*1e-12)
        G=self.node.nx_graph
        # #print('nx graph',self.own.nx_graph)
        """
        The code below is used to populate local_neighbor_table.
        We iterate through the neighbors of node. If that node exist in the nodewise_dest_distance, if it a virtual link we assign distance as 0, else we assign the distance from the nodewise_dest_distance between those nodes.
        """
        for n_nodes in neighbors:
            key=self.node.name
            for node,dist in nodewise_dest_distance.items():  
                if n_nodes==node:  
                    if node in vneighbors:
                        self.local_neighbor_table.setdefault(key,{})[node]=0
                        G.add_edge(key,node,color='red',weight=dist)
                    else:    
                        self.local_neighbor_table.setdefault(key,{})[node]=dist
                    break  

    def tempnexthop(self):
        
        #Compute the next hop here using our logic
        #Pick the best possible nieghbor according to physical distance
        # #print('--------------self.own.name------------', self.own.name,self.own.neighborhood_list)
        


        assert self.dst != self.node.name
        self.setattributes(self.node.name)
        
        G=self.node.nx_graph
        skip=[]
        #print('source ',self.src, self.node.name)
        if self.node.name == self.src:         
            path=nx.dijkstra_path(G,self.node.name,self.dst) 
            # print("path", path)
            '''We initially calculate the temporary path using Dijkstra's algorithm.'''
            ''' We append this temporary path to message class temporary path'''
            self.temp_path=path
            
            '''
                Marker node: The end node of the the local neighborhood which lies in the temp path.
                We iterate through the temp path, then through the neighborhood_list, and check if the node in the temp path lies in the neighborhood_list.
                we add this marker node to the msg.
            '''
            #print("neighbour list of 1st node ",self.node.neighborhood_list)
            for items in self.temp_path:
                self.marker=items
                if self.node.neighborhood_list:
                    for nodes in self.node.neighborhood_list:
                        if nodes==items:

                            self.marker=nodes
            #self.own.send_message(path[1],msg)
            #print("marker nodes",self.temp_path,self.marker)   
        #print('temp path',self.temp_path,self.node.name)
        indexx=self.temp_path.index(self.node.name)
        # #print('indx',self.own.name,indexx,len(msg.temp_path))

        # If the node is the first node in the temp path, we run the next_hop method, which gives us the next node using Djisktr's algorithm
        #print('It is end node',type(self.src),self.node,type(self.node))
        if self.node.is_endnode:
            dst=self.node.service_node
            #print('end node dst',dst)

        # if not self.node.is_endnode:
        #     #print('Service node')

        if self.node.name == self.temp_path[0]:
            dst=self.nexthop(self.node.name,self.temp_path[-1])
            #print("dst 1",dst)
                
        # If the node is the marker node we do the routing again by calling next_hop method
        elif self.node.name ==self.marker:
            # #print('At marker node',self.own.name,self.own.marker)
            dst=self.nexthop(self.node.name,self.temp_path[-1])
            #print("dst 2",dst)

            #If the node is not the source, marker or end node, we skip the routing.
        elif indexx > 0 and indexx < len(self.temp_path)-1:
            dst=self.temp_path[indexx+1]
            if dst == self.node.end_node:
                #print('next node is end node',dst, self.node.name)
                dst=self.node.end_node
            #print("dst 3",dst)
            # #print('mddle',self.own.name,dst,indexx)
                
        #For end node
        elif indexx==len(self.temp_path)-1:
            # #print('last node')
            dst=self.temp_path[-1]
            #print("dst 4",dst)
        return dst
                
        
       
    def nexthop(self,src,dest):
        # This function will give the next hop of the Dijkstra's path.
        
        G=self.node.nx_graph
        path=nx.dijkstra_path(G,src,dest)
        next_hop = path[1]
        # #print('dijkstas path',path,path[1],path[-1])
        virtual_neighbors = self.node.find_virtual_neighbors()
        # print('Virtual neighbor', path, virtual_neighbors)
        for node in path:
            if node in virtual_neighbors.keys():
                next_hop = node
        # print('Virtual neighbor', next_hop,path, virtual_neighbors)
        return next_hop

    def next_hop(self):

        # This function will give the next hop of the Dijkstra's path.
        if (self.node.name==self.dst):
            pass
        #print("node",self.node.name)
        G=self.node.nx_graph
        path=nx.dijkstra_path(G,self.src,self.dst)
        #print("path" ,path)
        index=path.index(self.node.name)
        #print(path[index+1])
        return path[index+1]

        # #print('dijkstas path',path,path[1],path[-1])
      


class RRPMsgType(Enum):
    """Defines possible message types for the reservation protocol."""

    RESERVE = auto()
    CREATE_TASKS = auto()
    FAIL = auto()
    #ABORT = auto()
    #SKIP_ROUTING=auto()
    

class Message():

    """Message used by Transport layer protocols.
    This message contains all information passed between transport protocol instances.
    Messages of different types contain different information.
    Attributes:
        msg_type (GenerationMsgType): defines the message type.
        receiver (str): name of destination protocol instance.
        src_obj : source node protocol instance
        dest_obj : destination node protocol instance.
    """


    def __init__(self, receiver_type : Enum, receiver : Enum, msg_type , **kwargs) -> None:
        
        self.receiver_type =receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs

class RRMessage(Message):
    """Message used by resource reservation protocol.
    This message contains all information passed between reservation protocol instances.
    Messages of different types contain different information.
    Attributes:
        msg_type (GenerationMsgType): defines the message type.
        receiver (str): name of destination protocol instance.
        reservation (Reservation): reservation object relayed between nodes.
        qcaps (List[QCaps]): cumulative quantum capacity object list (if `msg_type == REQUEST`)
        path (List[str]): cumulative node list for entanglement path (if `msg_type == APPROVE`)
    """

    def __init__(self, msg_type: any, receiver: str,request:"Request"):
        Message.__init__(self, msg_type, receiver )
        self.payload = request
        self.temp_path=None
        self.marker=None
        

class NetworkManagerMessage(Message):
    """Message used by the network manager.
    Attributes:
        message_type (Enum): message type required by base message type.
        receiver (str): name of destination protocol instance.
        payload (Message): message to be passed through destination network manager.
    """

    def __init__(self, msg_type: Enum, receiver: str, payload: "Message"):
        Message.__init__(self, msg_type, receiver)
        self.payload = payload

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
        # print('inside has virtual reservation',self.reservations.initiator,self.reservations.responder)
        for res in self.reservations:
            if res.isvirtual:
                return True
        return False


class ReservationProtocol():     #(Protocol): 

    def __init__(self,node:"QuantumRouter",request:"Request",routing:"RoutingProtocol", es_success_prob = 1, es_degradation = 0.95):
        
        self.node=node
        self.request = request
        self.routing = routing
        #self.node=Node
        self.vmemorylist=self.node.vmemory_list
        self.accepted_reservation=[]
        self.es_succ_prob = es_success_prob
        self.es_degradation = es_degradation
        print(f'self.es_succ_prob: {self.es_succ_prob}')
        print(f'self.es_degradation: {self.es_degradation}')
        self.name = "ReservationProtocol_"+self.node.name+"_R"+str(request.id)

    def memories_available(self):


        demand_count=0

        #self.vmemorylist = [MemoryTimeCard(i) for i in range(len(self.node.memory_array))]
        self.vmemorylist=self.node.vmemory_list

        #print(len(self.node.vmemory_list),self.node.name,self.request,"memory available")

        index_list=[]

        if self.node.name==self.request.initiator or self.node.name==self.request.responder :
            
            demand_count=self.request.memory_size

        else :

            demand_count=self.request.memory_size*2

        ##print("demand count by request",demand_count,self.request)
       
        for vmemory in self.vmemorylist:
            physical_requests=[]
            
            isCardVirtual = False
            #print('requestsss1', self.node.name,self.request.initiator,self.request.responder)
            for res in vmemory.reservations:
                if res.isvirtual:#$ or self.reservation.isvirtual
                    isCardVirtual = True
                else:
                    physical_requests.append(res)
            
            if isCardVirtual and  self.request.isvirtual:
                return -1, isCardVirtual


            start =0
            end = len(physical_requests)-1
            while start<=end :
                mid=(start+end)//2 
                #print('mid',mid,start,end)
                if physical_requests[mid].start_time>self.request.end_time :
                    
                    end=mid-1

                elif physical_requests[mid].end_time<self.request.start_time :

                    start=mid+1

                elif max(physical_requests[mid].start_time,self.request.start_time)<min(physical_requests[mid].end_time,self.request.end_time):
                    start=-1
                    break
        
                else:
                    
                    pass 
    
            if (start>=0):
                
                index_list.append((start,vmemory.memory_index))
                demand_count=demand_count-1
            
            #print('line 902')
            if(demand_count==0):

                for i in range(0,len(index_list)) :
                    #print(index_list,index_list[i],)
                    # #print("memory index",vmemorylist[index_list[i][1]])
                    #print("list index" ,index_list[i][0] )
                    self.vmemorylist[index_list[i][1]].reservations.insert(index_list[i][0],self.request)
                    if self.request.id not in self.node.resource_manager.reservation_id_to_memory_map:

                        self.node.resource_manager.reservation_id_to_memory_map[self.request.id] = []
                        self.node.resource_manager.reservation_id_to_memory_map[self.request.id].append(index_list[i][1])
                    else:
                        self.node.resource_manager.reservation_id_to_memory_map[self.request.id].append(index_list[i][1])
                
                #print('reservation to memory map',self.node.name,self.node.resource_manager.reservation_id_to_memory_map)
        
                return True    
        
        if (demand_count>0):

            #print(demand_count,"demand count")
            index_list.clear()
            return False
        

    def start(self):

        # print("start",self.node.name)
            #if RESOURCES AVAILABLE:
        if self.memories_available() :

            if (self.request.responder!=self.node.name):

                # print("start!",self.request.responder)
                next_node=self.routing.tempnexthop()
                #msgr=RRMessage(RRPMsgType.RESERVE,next_node,self.request) #msg_type="RESERVE"
                
                # print("request src , resp , curr node", self.request.initiator,self.request.responder,self.node.name ,self.request.status)
                msg=Message(MsgRecieverType.MANAGER, ManagerType.NetworkManager, RRPMsgType.RESERVE,request=self.request)
                msg.temp_path=self.routing.temp_path
                msg.marker=self.routing.marker
                #print("msg.msg_typed",msg.msg_type,msg)
                self.request.path.append(self.node)
                self.request.pathnames.append(self.node.name)
                self.node.message_handler.send_message(next_node,msg)
                #send_message(self, dst: str, msg: "Message", priority=inf)
                #self.node.messagehandler.send_message(receiver_node,request , msg_type)####send message to next hop node's network manager (send message function?network manager or protocol)
             
            if (self.request.responder==self.node.name):
                
                # print("start",self.request.responder)
                #print("request src , resp , curr node", self.request.initiator,self.request.responder,self.node.name ,self.request.status)
                # print ("destination",self.node.name)
                self.request.path.append(self.node)
                self.request.pathnames.append(self.node.name)
                logger.info("Resources reserved")
                #print("Request ID:", self.requst.id)
                logger.info("Finalized path"+str(self.request.pathnames))
                index=self.request.path.index(self.node)
                prev_node=self.request.path[index-1]
                msg=Message(MsgRecieverType.MANAGER, ManagerType.ReservationManager,RRPMsgType.CREATE_TASKS,request=self.request)
                #print(" final message type fp , receiver", msg.msg_type ,msg.receiver)
                #index=path.index(self.node.name)
                ##print(path[index+1])

                """create tasks and back propagate that msg to create tasks to previous node
                
                """
                #rules=self.create_rules(self.request.pathnames,self.request)
                self.set_dependencies_subtask(self.request.pathnames,self.request)
                self.schedule_tasks(self.request)
                #self.load_rules(rules,self.request)
                #print("tasks created at" ,self.node.name )
                #call task and dependency creation method
                self.node.message_handler.send_message(prev_node.name,msg)
                #send classical message to previous node path[index-1]'s Reservation protocol to createtasks 
                #in receive msg check this condn
                #send(msg_type)
                ##print("congestion_retransmission in sucess",self.request.congestion_retransmission)
                """if self.request.congestion_retransmission==1:
                    #print("congestion sucess")
                    msg1=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,CongestionMsgType.SUCCESS,request=self.request)
                    self.node.message_handler.send_message(self.request.initiator,msg1)"""
                #self.node.transport_manager.recv_success_reallocation(self.request.memory_size,self.request)
                

                          
        else :

            self.request.status='REJECT'
            #print("request src , resp , curr node", self.request.initiator,self.request.responder,self.node.name ,self.request.status)
            msg=Message(MsgRecieverType.MANAGER, ManagerType.ReservationManager,RRPMsgType.FAIL,request=self.request)
            
            #(RESORCES NOT AVAILABLE)
            #msg_type="FAIL"
            #self.request.status='REJECT'
            #print('inside reservation reject',self.node.name,self.request.id,self.request.initiator,self.request.responder)
            #self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)

            #self.rnode.send_message(path[len(path)-1].name ,msg)
            if self.node.name==self.request.initiator:
                #print("------node at which it is failing---",self.node.name,self.request.responder)
                if self.request.congestion_retransmission!=1:

                    self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)
                """if self.request.congestion_retransmission==1:
                    msg1=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,CongestionMsgType.FAIL,request=self.request)
                    self.node.message_handler.send_message(src.name,msg1)"""
                    
                return
            else :
                #index=self.request.path.index(self.node)
                index=len(self.request.path)-1
                #prev_node=self.request.path[index-1]
                prev_node=self.request.path[index]
                self.node.message_handler.send_message(prev_node.name,msg)
                """if self.request.congestion_retransmission==1:
                    msg1=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,CongestionMsgType.FAIL,request=self.request)
                    self.node.message_handler.send_message(src.name,msg1)"""
                    
            self.request.congestion = 1

    
    def receive_message(self ,msg :"RRPMsgType"):

        if msg.msg_type==RRPMsgType.CREATE_TASKS :
            payload=msg.kwargs['request']
            self.request=payload
            #print("request src , resp , curr node", self.request.initiator,self.request.responder,self.node.name ,self.request.status)
            if self.node.name==self.request.initiator:
                #create tasks
                #print("tasks created at ",self.node.name)
                # rules=self.create_rules(self.request.pathnames,self.request)
                # self.load_rules(rules,self.request)
                self.set_dependencies_subtask(self.request.pathnames,self.request)
                self.schedule_tasks(self.request)
                #print("tasks created at ",self.node.name)
                if self.request.congestion_retransmission==1:

                    #print("congestion_retransmission in sucess",self.request.congestion_retransmission)
                    remaining_demand_size=self.request.remaining_demand_size-self.request.memory_size
                    self.node.transport_manager.recv_success_reallocation(self.request.memory_size,self.request,remaining_demand_size)

            else:
                index=self.request.path.index(self.node)
                prev_node=self.request.path[index-1]
                
                """create tasks and back propagate that msg to crate tasks to previous node"""
                # rules=self.create_rules(self.request.pathnames,self.request)
                # self.load_rules(rules,self.request)
                self.set_dependencies_subtask(self.request.pathnames,self.request)
                self.schedule_tasks(self.request)
                #call tasks and dependency
                #print("tasks created at ",self.node.name)
                msg=Message(MsgRecieverType.MANAGER, ManagerType.ReservationManager,RRPMsgType.CREATE_TASKS,request=self.request)
                self.node.message_handler.send_message(prev_node.name,msg)
                
            
                #previous_node=self.request.path[previous_node_index]

                #send classical msg to previous node to create tasks
            #elif msg.msg_type==RRPMsgType.FAIL:
            # Mechanism to release resources
            #send_message(to release)
            #vmemoryarray[index_list[i][1]].reservations.remove(req.reser)

            #back track path and release resources"""

        elif msg.msg_type==RRPMsgType.FAIL :
            
            #self.request=msg.payload
            self.request=msg.kwargs['request']
            #self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)
            #print("request src , resp , curr node", self.request.initiator,self.request.responder,self.node.name ,self.request.status)
            if self.node.name==self.request.initiator:
                #create tasks
                #print("removed resources at ",self.node.name ,self.request.id)
                #vmemoryarray[index_list[i][1]].reservations.remove(req.reser)
                #print('inside reservation reject received at src',self.node.name,self.request.id,self.request.initiator,self.request.responder)
                #self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)
                for vmemory in self.vmemorylist:
                    if self.request in vmemory.reservations:
                        vmemory.reservations.remove(self.request)
                    """if self.request.congestion_retransmission==1:
                    msg1=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,CongestionMsgType.FAIL,request=self.request)
                    self.node.message_handler.send_message(self.node.name,msg1)"""

                #self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)
                if self.request.congestion_retransmission==1:
                    self.node.transport_manager.recv_fail_reallocation(self.request.memory_size,self.request,self.request.remaining_demand_size)
                else:
                    self.node.network_manager.notify_nm('REJECT',self.request.id,self.request)
                

            else:
                for vmemory in self.vmemorylist:
                    if self.request in vmemory.reservations:
                        vmemory.reservations.remove(self.request)
                index=self.request.path.index(self.node)
                prev_node=self.request.path[index-1]
                #print("removed resources at ",self.node.name)
                msg=Message(MsgRecieverType.MANAGER, ManagerType.ReservationManager,RRPMsgType.FAIL,request=self.request)
                self.node.message_handler.send_message(prev_node.name,msg)

        self.node.message_handler.process_msg(msg.receiver_type,msg.receiver)

   
    def schedule_tasks(self, reservation: "Request") -> None:
        
        self.accepted_reservation.append(reservation)  #Don't know the exact use for this

        #Scheduling the expire event for reservations
        for card in self.vmemorylist:
            if reservation in card.reservations:
                # process = Process(self.own.resource_manager, "update",
                #                   [None, self.own.memory_array[card.memory_index], "RAW"])
                # event = Event(reservation.end_time, process, 1)
                event = Event(reservation.end_time,self.node.resource_manager, "update", [None, self.node.memory_array[card.memory_index], "RAW"] )
                #self.node.timeline.schedule(event)
                self.node.timeline.schedule_counter += 1
                self.node.timeline.events.push(event)

        # process = Process(self.own.task_manager, "load", [rule])
        # process = Process(self.own.task_manager, "initiate_tasks", [])
        # event = Event(reservation.start_time, process)
        event = Event(reservation.start_time,self.node.task_manager, "initiate_tasks", [] )
        #self.node.timeline.schedule(event)             #This was the right way
        
        #This way of scheduling things is wrong, needs to be changed
        self.node.timeline.schedule_counter += 1
        self.node.timeline.events.push(event)
        """process = Process(self.own.resource_manager, "expire", [rule])
        event = Event(reservation.end_time, process, 0)
        self.own.timeline.schedule(event)"""


    def set_dependencies_subtask(self, path: List[str], reservation: "Request"):
        
        #print('setting dependencies')
        
        #     self.node.resource_manager.rule_manager.rules = []
    #     # print(f'Rules for this node: {self.own.name} are {len(self.own.resource_manager.rule_manager.rules)}')
    #     memory_indices = []
    #     virtual_indices = []
    #     memory_indices_occupied = []
    #     last_virtual_index = -1
    #     memories_indices_free=[]

    #     for card in self.vmemorylist:
    #         #print("1")
    #         #print('111111', card)
    #         if reservation in card.reservations:
    #             memory_indices.append(card.memory_index)
    #             # print("To maintain the virtual link indices")
    #             if card.has_virtual_reservation() and not reservation.isvirtual:
    #                 virtual_indices.append(card.memory_index)
    #                 if card.memory_index > last_virtual_index:
    #                     last_virtual_index= card.memory_index
    #             # elif card.has_virtual_reservation() and reservation.isvirtual:
    #             #     print('Another virtual request arrived')
                
                    
                    
    #     # print('last_virtual_index', last_virtual_index)   
        
        
        #Offset the memory indices used by Virtual links
        memory_indices = []
        virtual_indices = []
        last_virtual_index = -1
        for card in self.vmemorylist:
            if reservation in card.reservations:
                memory_indices.append(card.memory_index)
                #print("To maintain the virtual link indices")
                if card.has_virtual_reservation() and not reservation.isvirtual:
                    virtual_indices.append(card.memory_index)
                    if card.memory_index > last_virtual_index:
                        last_virtual_index= card.memory_index
                elif card.has_virtual_reservation() and reservation.isvirtual:
                    print('Another virtual request arrived')

        #print('last_virtual_index', last_virtual_index)

        #print('----------Enatanglement Generation Task----------')
        #print('Current node in Entanglement generation', self.node.name)
        index = path.index(self.node.name)
        #print('Path--------', path)
        #print('Reservation------', reservation.initiator, reservation.responder,reservation.id)
        
        """
            A --- B ---- C
            A - ent gen with B
            B - ent gen with A
                ent gen with C
            C - ent gen with B
        """

        """
            Making the memory cell allocation part of the action methods
        """
        
        task_gen_left, task_gen_right = None, None
        last_left_task, last_right_task = None, None
        #For middle nodes        
        if index > 0:
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index - 1] in self.node.neighbors:
                print("type(reservation.memory_size): ", type(reservation.memory_size))
                mem_indices = memory_indices[ last_virtual_index+1 : int(reservation.memory_size)]
    
                
                task_EG_right = Task('TaskEntGen_'+self.node.name+'_'+path[index - 1], [], self.node.timeline.now(), False, None, self.node.task_manager, mem_indices = mem_indices)
                self.node.task_manager.add_task(task_EG_right, [])
                task_EG_right.set_reservation(reservation)

                def ent_gen_action(memories_info: List["MemoryInfo"], **kwargs):
                    #print('task name in action: ', task_EG_left.name)
                    sub_tasks = []
                    
                    #subtask action: specifies what to do in subtask
                    def gen_subtask_action(memarg):
                        memarg = [info.memory for info in memarg]
                        mid = self.node.map_to_middle_node[path[index - 1]]
                        protocol = EntanglementGenerationA(None, "EGA." + memarg[0].name, mid, path[index - 1], memarg[0])
                        return [protocol], [None], [None]

                    #Creating subtask for each memory
                    for memory_info in memories_info:
                        ent_gen_subtask = SubTask(None, gen_subtask_action, [memory_info])
                        sub_tasks.append(ent_gen_subtask)
                        ent_gen_subtask.initial_dependency_subtasks = [ent_gen_subtask]
                        #task_EG_left.memory_to_subtask[memory_info] = ent_gen_subtask
                        self.node.task_manager.memory_to_gen_subtask[memory_info] = ent_gen_subtask
                    return sub_tasks
                
                task_EG_right.set_action(ent_gen_action)
                last_right_task = task_EG_right
        
        if index < len(path) - 1:
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index + 1] in self.node.neighbors:

                if index == 0:   #Starting node
                    mem_indices = memory_indices
                else:   #second to second last node
                    # mem_indices = memory_indices[(last_virtual_index+1) + reservation.memory_size:]
                    mem_indices = memory_indices[reservation.memory_size:]

                #memory_info = []
                
                #for mem_index in mem_indices:
                #    memory_info.append(self.own.resource_manager.memory_manager.__getitem__(mem_index))
                #print('current node, mem_indices, available_memory_indices: ', self.node.name, mem_indices, memory_indices)
                task_EG_left = Task('TaskEntGen_'+self.node.name+'_'+path[index + 1], [], self.node.timeline.now(), False, None, self.node.task_manager, mem_indices = mem_indices)
                self.node.task_manager.add_task(task_EG_left, [])
                task_EG_left.set_reservation(reservation)

                def ent_gen_action(memories_info: List["MemoryInfo"], **kwargs):
                    #print('inside EG right task action:  ', task_EG_right.name)
                    sub_tasks = []
    
                    def gen_subtask_action(memarg):
                        memarg = [info.memory for info in memarg]
                        mid = self.node.map_to_middle_node[path[index + 1]]

                        #Validation function
                        def req_func(protocols):
                            for protocol in protocols:
                                if isinstance(protocol,
                                            EntanglementGenerationA) and protocol.other == self.node.name and protocol.subtask.task.get_reservation() == reservation:
                                    return protocol
                        
                        protocol = EntanglementGenerationA(None, "EGA." + memarg[0].name, mid, path[index + 1], memarg[0])
                        return [protocol], [path[index + 1]], [req_func]

                    for memory_info in memories_info:
                        ent_gen_subtask = SubTask(None, gen_subtask_action, [memory_info])
                        sub_tasks.append(ent_gen_subtask)
                        ent_gen_subtask.initial_dependency_subtasks = [ent_gen_subtask]
                        #task_EG_right.memory_to_subtask[memory_info] = ent_gen_subtask
                        self.node.task_manager.memory_to_gen_subtask[memory_info] = ent_gen_subtask
                    return sub_tasks
                
                task_EG_left.set_action(ent_gen_action)
                last_left_task = task_EG_left
                
        #Task for purification creation
        if index > 0:
            #To accept virtual links, we skip the purification step when a non physical neighbor is found
            if path[index - 1] in self.node.neighbors:
                def ent_purify_action(memories_info: List["MemoryInfo"], **kwargs):
                    #print('inside ent_purify_action1')
                    #print(self.name)
                    gen_subtask = kwargs['dependency_subtasks'][0]
                    #print('len(gen_subtask.dependents): ', len(gen_subtask.dependents))
                    if len(gen_subtask.dependents) != 0 and gen_subtask.dependents != None:
                        #Make use of previously mapped purification subtask
                        #print('Make use of previously mapped purification subtask')
                        return gen_subtask.dependents

                    #print('Not Making use of previously mapped purification subtask')
                    def purify_subtask_action(memarg):
                        #Find another memory that can be used to purify
                        #If memory is available, purify
                        #Otherwise exit without doing anything
                        # print('purify subtask action right')
                        purify_indices = []
                        if (memarg[0].state == "ENTANGLED" and memarg[0].fidelity < reservation.fidelity):
                            for other_mem in self.node.resource_manager.memory_manager:
                                if other_mem != memarg[0] and other_mem.state == "ENTANGLED" and other_mem.remote_node == memarg[0].remote_node and other_mem.fidelity == memarg[0].fidelity:
                                # if other_mem != memarg[0] and other_mem.state == "ENTANGLED" and other_mem.remote_node == memarg[0].remote_node:
                                    # print(f'found pair of memories to purify')
                                    purify_indices.append(memarg[0])
                                    purify_indices.append(other_mem)
                                    break
                        if len(purify_indices) == 0:
                            #Purification not needed
                            if memarg[0].fidelity >= reservation.fidelity:
                                # print('purification not needed')
                                return True, None, None

                            #could not find memory to purify so exit
                            # print('No memory found to purify')
                            return None, None, None
                        

                        memories = [info.memory for info in purify_indices]
                        #print('inside ent_purify subtask 1: ', memories[0].name,  memories[1].name)
                        def req_func(protocols):
                            _protocols = []
                            #print('purify_indices inside req_func: ', purify_indices)
                            #print('protocols list: ', [protocol.name for protocol in protocols])
                            for protocol in protocols:
                                # print('protocol name inside req_func: ', protocol.kept_memo.name, ' protocol: ', protocol, 'protocol.kept_memo.name: ', protocol.kept_memo.name, 'purify_indices: ', [(i.remote_memo, i.memory.name) for i in purify_indices])
                                if not isinstance(protocol, BBPSSW):
                                    continue

                                if protocol.kept_memo.name == purify_indices[0].remote_memo:
                                    _protocols.insert(0, protocol)
                                if protocol.kept_memo.name == purify_indices[1].remote_memo:
                                    _protocols.insert(1, protocol)

                            if len(_protocols) != 2:
                                #print('Pair of protocol instances could not be found to purify')
                                return None

                            protocols.remove(_protocols[1])
                            #_protocols[1].rule.protocols.remove(_protocols[1])
                            _protocols[1].subtask.protocols.remove(_protocols[1])
                            _protocols[1].kept_memo.detach(_protocols[1])
                            _protocols[0].meas_memo = _protocols[1].kept_memo
                            _protocols[0].memories = [_protocols[0].kept_memo, _protocols[0].meas_memo]
                            _protocols[0].name = _protocols[0].name + "." + _protocols[0].meas_memo.name
                            _protocols[0].meas_memo.attach(_protocols[0])
                            _protocols[0].t0 = _protocols[0].kept_memo.timeline.now()
                            #print('Inside purification req_func: kept_memo ', _protocols[0].kept_memo.name, ', meas_memo: ', _protocols[0].meas_memo.name)

                            return _protocols[0]

                        name = "EP.%s.%s" % (memories[0].name, memories[1].name)
                        #print('purification_name1:  ', name)
                        protocol = BBPSSW(None, name, memories[0], memories[1])
                        dsts = [purify_indices[0].remote_node]
                        req_funcs = [req_func]
                        return [protocol], dsts, req_funcs
                    
                    ent_purify_subtask_right = SubTask('EP_'+gen_subtask.name, purify_subtask_action, memories_info)
                    gen_subtask.dependents = [ent_purify_subtask_right]
                    ent_purify_subtask_right.dependencies = [gen_subtask]
                    ent_purify_subtask_right.initial_dependency_subtasks = [gen_subtask]
                    #print('newly created purification subtask for the gen subtask: ', gen_subtask.name)
                    return gen_subtask.dependents

                task_Purify_right = Task('TaskPurifyRight'+self.node.name+path[index-1], [task_EG_right], self.node.timeline.now(), False, ent_purify_action, self.node.task_manager)
                self.node.task_manager.add_task(task_Purify_right, [task_EG_right])
                task_Purify_right.set_reservation(reservation)
                last_right_task = task_Purify_right

        if index < len(path) - 1:
            #To accept virtual links, we skip the purification step when a non physical neighbor is found
            if path[index + 1] in self.node.neighbors:
                def ent_purify_action(memories_info: List["MemoryInfo"], **kwargs):
                    #print('inside ent_purify_action2')
                    gen_subtask2 = kwargs['dependency_subtasks'][0]
                    # dependency_subtasks = kwargs.get('dependency_subtasks')
                    # if dependency_subtasks != None:
                    #     gen_subtask = dependency_subtasks[0]
                    if len(gen_subtask2.dependents) != 0 and gen_subtask2.dependents != None:
                        #Make use of previously mapped purification subtask
                        #print('making use of previously mapped subtask for the gen_subtask: ', gen_subtask2.name)
                        return gen_subtask2.dependents

                    def purify_subtask_action(memarg):
                        # print('purify subtask action left')
                        purify_indices = []
                        if (memarg[0].state == "ENTANGLED" and memarg[0].fidelity < reservation.fidelity):
                            purify_indices.extend(memarg)
                        
                        if len(purify_indices) == 0:
                            if memarg[0].fidelity >= reservation.fidelity:
                                # print('purification not needed')
                                return True, None, None
                            # print('purification needed but memory not available')
                            return None, None, None

                        memories = [info.memory for info in purify_indices]
                        #print('inside ent_purify subtask 2: ', memories[0].name)
                        
                        name = "EP.%s" % (memories[0].name)
                        #print('purification_name2:  ', name)
                        protocol = BBPSSW(None, name, memories[0], None)
                        return [protocol], [None], [None]
                    
                    ent_purify_subtask_left = SubTask('EP_'+gen_subtask2.name, purify_subtask_action, memories_info)
                    gen_subtask2.dependents = [ent_purify_subtask_left]
                    ent_purify_subtask_left.dependencies = [gen_subtask2]
                    ent_purify_subtask_left.initial_dependency_subtasks = [gen_subtask2]
                    return gen_subtask2.dependents
                
                task_Purify_left = Task('TaskPurifyLeft'+self.node.name+path[index+1], [task_EG_left], self.node.timeline.now(), False, ent_purify_action, self.node.task_manager)
                self.node.task_manager.add_task(task_Purify_left, [task_EG_left])
                task_Purify_left.set_reservation(reservation)
                last_left_task = task_Purify_left
    
        
        """
            Entanglement swapping tasks
        """
        nPurify_counter = 0
        #Compute the schedule of swaps
        schedule = {}
        for node in path[1:-1]:
            _path = path[:]
            while _path.index(node) % 2 == 0:
                new_path = []
                for i, n in enumerate(_path):
                    if i % 2 == 0 or i == len(_path) - 1:
                        new_path.append(n)
                _path = new_path
            _index = _path.index(node)
            left, right = _path[_index - 1], _path[_index + 1]
            #print(f'Swap at node: {node} left: {left} and right: {right}')
            schedule[(left, right, node)] = path.index(right) - path.index(left)
        #print(schedule)
        sorted_schedule = sorted(schedule.items(), key=lambda x: x[1])
        #print('order of swaps: ', sorted_schedule)

        #Loop through the schedule and find the places where current node occurs so that we can generate tasks
        #curr_task = None
        #task_list = []
        
        is_final_virtual_swap = False
        for (left, right, mid), val in sorted_schedule:

            nPurify_counter += 1
            
            if reservation.isvirtual and left == reservation.initiator and right == reservation.responder:
                is_final_virtual_swap = True

            #If current node is left, then instantiate EntSwapLeft instance
            if self.node.name == left:
                
                #If the middle node is a virtual neighbor of this node, pick the cached task as a dependency:
                if mid in self.node.virtual_links.keys():
                    #Find the cached VL task with this node
                    subtask_list = self.node.virtual_links[mid]
                    last_left_task = subtask_list[0].task

                def ent_swap_action(memories_info: List["MemoryInfo"], **kwargs):
                    #purify_subtask_left = kwargs['dependency_subtasks'][0]
                    purify_subtask_right = kwargs['dependency_subtasks'][0]
                    #print('len(gen_subtask.dependents): ', len(gen_subtask.dependents))
                    
                    if len(purify_subtask_right.dependents) != 0:
                        #Find the swap subtask that is common to both these subtasks
                        #Will do this logic later,right now it's clear purification will be followed by swap
                        #dependents = list(set(purify_subtask_left.dependents).intersection(purify_subtask_right.dependents))
                        
                        #Make use of previously mapped purification subtask
                        return purify_subtask_right.dependents
                    
                    def swap_subtask_action(memarg):
                        swap_indices = []
                        if (memarg[0].state == "ENTANGLED"
                            and memarg[0].index in memory_indices
                            and memarg[0].remote_node != path[-1]
                            #and memarg[0].fidelity >= reservation.fidelity
                            ):
                        
                            swap_indices.append(memarg[0])
                        
                        if len(swap_indices) == 0:
                            return None, None, None
                        
                        memories = [info.memory for info in swap_indices]
                        memory = memories[0]
                        protocol = EntanglementSwappingB(None, "ESB." + memory.name, memory)
                        return [protocol], [None], [None]
                    
                    ent_swap_subtask = SubTask('ES-'+purify_subtask_right.name, swap_subtask_action, memories_info)
                    purify_subtask_right.dependents = [ent_swap_subtask]
                    ent_swap_subtask.dependencies = [purify_subtask_right]
                    ent_swap_subtask.initial_dependency_subtasks = purify_subtask_right.initial_dependency_subtasks
                    return purify_subtask_right.dependents
                
                #if path.index(right) - path.index(left) == 2:
                task_swap_left_end= Task('TaskSwapLeftEnd'+left+right, [last_left_task], self.node.timeline.now(), False, ent_swap_action, self.node.task_manager)
                if is_final_virtual_swap:
                    #print('final swap flagged to true')
                    task_swap_left_end.is_vl_final_swap_task = True
                self.node.task_manager.add_task(task_swap_left_end, [last_left_task])
                task_swap_left_end.set_reservation(reservation)
                last_left_task = task_swap_left_end
                #print('ENT_SWAP_LEFT at: ', self.node.name)

                #If the middle node is a virtual neighbor of this node, pick the cached task as a dependency:
                if mid in self.node.virtual_links.keys():
                    #we need to set_dependency_to_subtask
                    subtask_list = self.node.virtual_links[mid]
                    for subtask in subtask_list:
                        task_swap_left_end.set_dependency_to_subtask(subtask)
                    task_swap_left_end.can_run_on_init = True

                # else:
                #     task_swap_left_end= Task('TaskSwapLeftEnd'+left+right, [task_list[-1]], self.own.timeline.now(), ent_swap_action, self.own.task_manager)
                #     self.own.task_manager.add_task(task_swap_left_end, [task_list[-1]])
                #     task_swap_left_end.set_reservation(reservation)
                #     curr_task = task_swap_left_end


                #Nested Purification Task
                def ent_purify_action(memories_info: List["MemoryInfo"], **kwargs):
                    # print('inside nested_purify_task_left')
                    nested_swap_subtask = kwargs['dependency_subtasks'][0]
                    # dependency_subtasks = kwargs.get('dependency_subtasks')
                    # if dependency_subtasks != None:
                    #     gen_subtask = dependency_subtasks[0]
                    if len(nested_swap_subtask.dependents) != 0 and nested_swap_subtask.dependents != None:
                        #Make use of previously mapped purification subtask
                        # print('making use of previously mapped subtask for the nested_swap_subtask_left: ', nested_swap_subtask.name)
                        return nested_swap_subtask.dependents

                    def purify_subtask_action(memarg):
                        # print(f'inside purify_subtask_action left: nPurify_counter-> {nPurify_counter}')
                        purify_indices = []
                        if (memarg[0].state == "ENTANGLED" and memarg[0].fidelity < reservation.fidelity):
                            purify_indices.extend(memarg)
                        
                        if len(purify_indices) == 0:
                            if memarg[0].fidelity >= reservation.fidelity:
                                # print('purification not needed')
                                return True, None, None
                            # print('purification needed but memory not available')
                            return None, None, None

                        memories = [info.memory for info in purify_indices]
                        # print('inside nested_swap_subtask_left: ', memories[0].name)
                        
                        name = "EP.%s" % (memories[0].name)
                        # print('nested_swap_subtask_left:  ', name)
                        protocol = BBPSSW(None, name, memories[0], None)
                        return [protocol], [None], [None]
                    
                    nested_purify_subtask_left = SubTask('EP_'+nested_swap_subtask.name, purify_subtask_action, memories_info)
                    nested_swap_subtask.dependents = [nested_purify_subtask_left]
                    nested_purify_subtask_left.dependencies = [nested_swap_subtask]
                    nested_purify_subtask_left.initial_dependency_subtasks = nested_swap_subtask.initial_dependency_subtasks
                    return nested_swap_subtask.dependents
                
                # task_nested_purify_left = Task('TaskNestedPurifyLeft'+self.node.name+path[index+1], [last_left_task], self.node.timeline.now(), False, ent_purify_action, self.node.task_manager)
                # self.node.task_manager.add_task(task_nested_purify_left, [last_left_task])
                # task_nested_purify_left.set_reservation(reservation)
                # last_left_task = task_nested_purify_left
            
            elif right == self.node.name:
                
                #If the middle node is a virtual neighbor of this node, pick the cached task as a dependency:
                if mid in self.node.virtual_links.keys():
                    #Find the cached VL task with this node
                    subtask_list = self.node.virtual_links[mid]
                    last_right_task = subtask_list[0].task

                def ent_swap_action(memories_info: List["MemoryInfo"], **kwargs):
                    purify_subtask_left = kwargs['dependency_subtasks'][0]
                    #purify_subtask_right = kwargs['dependency_subtasks'][0]
                    #print('len(gen_subtask.dependents): ', len(gen_subtask.dependents))
                    
                    if len(purify_subtask_left.dependents) != 0:
                        #Find the swap subtask that is common to both these subtasks
                        #Will do this logic later,right now it's clear purification will be followed by swap
                        #dependents = list(set(purify_subtask_left.dependents).intersection(purify_subtask_right.dependents))
                        
                        #Make use of previously mapped purification subtask
                        return purify_subtask_left.dependents
                    
                    def swap_subtask_action(memarg):
                        swap_indices = []
                
                        if (memarg[0].state == "ENTANGLED"
                                and memarg[0].index in memory_indices
                                and memarg[0].remote_node != path[0]
                                #and memarg[0].fidelity >= reservation.fidelity
                                ):
                            swap_indices.append(memarg[0])
                        
                        if len(swap_indices) == 0:
                            return None, None, None
                        
                        memories = [info.memory for info in swap_indices]
                        memory = memories[0]
                        protocol = EntanglementSwappingB(None, "ESB." + memory.name, memory)
                        return [protocol], [None], [None]
                    
                    ent_swap_subtask = SubTask('ES-'+purify_subtask_left.name, swap_subtask_action, memories_info)
                    purify_subtask_left.dependents = [ent_swap_subtask]
                    ent_swap_subtask.dependencies = [purify_subtask_left]
                    ent_swap_subtask.initial_dependency_subtasks = purify_subtask_left.initial_dependency_subtasks
                    return purify_subtask_left.dependents
                
                #if path.index(right) - path.index(left) == 2:
                task_swap_right_end= Task('TaskSwapRightEnd'+right+left, [last_right_task], self.node.timeline.now(), False, ent_swap_action, self.node.task_manager)
                if is_final_virtual_swap:
                    #print('final swap flagged to true')
                    task_swap_right_end.is_vl_final_swap_task = True
                self.node.task_manager.add_task(task_swap_right_end, [last_right_task])
                task_swap_right_end.set_reservation(reservation)
                last_right_task = task_swap_right_end
                #print('ENT_SWAP_RIGHT at: ', self.node.name)

                #If the middle node is a virtual neighbor of this node, pick the cached task as a dependency:
                if mid in self.node.virtual_links.keys():
                    #we need to set_dependency_to_subtask
                    subtask_list = self.node.virtual_links[mid]
                    for subtask in subtask_list:
                        task_swap_right_end.set_dependency_to_subtask(subtask)
                    task_swap_right_end.can_run_on_init = True

                # else:
                #     task_swap_right_end= Task('TaskSwapRightEnd'+right+left, [task_list[-1]], self.own.timeline.now(), ent_swap_action, self.own.task_manager)
                #     self.own.task_manager.add_task(task_swap_right_end, [task_list[-1]])
                #     task_swap_right_end.set_reservation(reservation)
                #     curr_task = task_swap_right_end

                #Nested purification task
                def ent_purify_action(memories_info: List["MemoryInfo"], **kwargs):
                    # print('inside nested_purify_task_right')
                    #print(self.name)
                    nested_swap_subtask_right = kwargs['dependency_subtasks'][0]
                    #print('len(gen_subtask.dependents): ', len(gen_subtask.dependents))
                    if len(nested_swap_subtask_right.dependents) != 0 and nested_swap_subtask_right.dependents != None:
                        #Make use of previously mapped purification subtask
                        # print('making use of previously mapped subtask for the nested_swap_subtask_right: ', nested_swap_subtask_right.name)
                        return nested_swap_subtask_right.dependents

                    #print('Not Making use of previously mapped purification subtask')
                    def purify_subtask_action(memarg):
                        #Find another memory that can be used to purify
                        #If memory is available, purify
                        #Otherwise exit without doing anything
                        # print(f'nested purify subtask action right: nPurify_counter-> {nPurify_counter}')
                        purify_indices = []
                        
                        if (memarg[0].state == "ENTANGLED" and memarg[0].fidelity < reservation.fidelity):
                            for other_mem in self.node.resource_manager.memory_manager:
                                if other_mem != memarg[0] and other_mem.state == "ENTANGLED" and other_mem.remote_node == memarg[0].remote_node and other_mem.fidelity == memarg[0].fidelity:
                                    purify_indices.append(memarg[0])
                                    purify_indices.append(other_mem)
                                    break
                        
                        if len(purify_indices) == 0:
                            #Purification not needed
                            if memarg[0].fidelity >= reservation.fidelity:
                                # print(f'purification not needed right: target_fidelity -> {reservation.fidelity}')
                                return True, None, None

                            #could not find memory to purify so exit
                            # print('No memory found to purify right')
                            return None, None, None
                        

                        memories = [info.memory for info in purify_indices]
                        #print('inside ent_purify subtask 1: ', memories[0].name,  memories[1].name)
                        def req_func(protocols):
                            _protocols = []
                            #print('purify_indices inside req_func: ', purify_indices)
                            #print('protocols list: ', [protocol.name for protocol in protocols])
                            for protocol in protocols:
                                # print('protocol name inside req_func: ', protocol.kept_memo.name, ' protocol: ', protocol, 'protocol.kept_memo.name: ', protocol.kept_memo.name, 'purify_indices: ', [(i.remote_memo, i.memory.name) for i in purify_indices])
                                if not isinstance(protocol, BBPSSW):
                                    continue

                                if protocol.kept_memo.name == purify_indices[0].remote_memo:
                                    _protocols.insert(0, protocol)
                                if protocol.kept_memo.name == purify_indices[1].remote_memo:
                                    _protocols.insert(1, protocol)

                            if len(_protocols) != 2:
                                #print('Pair of protocol instances could not be found to purify')
                                return None

                            protocols.remove(_protocols[1])
                            #_protocols[1].rule.protocols.remove(_protocols[1])
                            _protocols[1].subtask.protocols.remove(_protocols[1])
                            _protocols[1].kept_memo.detach(_protocols[1])
                            _protocols[0].meas_memo = _protocols[1].kept_memo
                            _protocols[0].memories = [_protocols[0].kept_memo, _protocols[0].meas_memo]
                            _protocols[0].name = _protocols[0].name + "." + _protocols[0].meas_memo.name
                            _protocols[0].meas_memo.attach(_protocols[0])
                            _protocols[0].t0 = _protocols[0].kept_memo.timeline.now()
                            #print('Inside purification req_func: kept_memo ', _protocols[0].kept_memo.name, ', meas_memo: ', _protocols[0].meas_memo.name)

                            return _protocols[0]

                        name = "EP.%s.%s" % (memories[0].name, memories[1].name)
                        # print('nested_purification_subtask_right:  ', name)
                        protocol = BBPSSW(None, name, memories[0], memories[1])
                        dsts = [purify_indices[0].remote_node]
                        req_funcs = [req_func]
                        return [protocol], dsts, req_funcs
                    
                    nested_purify_subtask_right = SubTask('EP_'+nested_swap_subtask_right.name, purify_subtask_action, memories_info)
                    nested_swap_subtask_right.dependents = [nested_purify_subtask_right]
                    nested_purify_subtask_right.dependencies = [nested_swap_subtask_right]
                    nested_purify_subtask_right.initial_dependency_subtasks = nested_swap_subtask_right.initial_dependency_subtasks
                    # print('newly created purification subtask for the gen subtask: ', gen_subtask.name)
                    return nested_swap_subtask_right.dependents

                # task_nested_purify_right = Task('TaskNestedPurifyRight'+self.node.name+path[index-1], [last_right_task], self.node.timeline.now(), False, ent_purify_action, self.node.task_manager)
                # self.node.task_manager.add_task(task_nested_purify_right, [last_right_task])
                # task_nested_purify_right.set_reservation(reservation)
                # last_right_task = task_nested_purify_right
            
            elif mid == self.node.name:
                left_m = left
                right_m = right
                #print(f'while setting task action: left :{left} right: {right} and mid: {mid} and self.own.name: {self.node.name}')

                #If the left node is a virtual neighbor of this node, pick the cached task as a dependency:
                if left in self.node.virtual_links.keys():
                    #Find the cached VL task with this node
                    #print('at mid of swap node: ', self.node.name, 'self.node.virtual_links: ',self.node.virtual_links)
                    subtask_list = self.node.virtual_links[left]
                    last_right_task = subtask_list[0].task
                    #print('right task from VL:', last_left_task.name)

                #If the right node is a virtual neighbor of this node, pick the cached task as a dependency:
                if right in self.node.virtual_links.keys():
                    #Find the cached VL task with this node
                    subtask_list = self.node.virtual_links[right]
                    last_left_task = subtask_list[0].task
                    #print('left task from VL:', last_right_task.name)

                def ent_swap_action_middle(memories_info: List["MemoryInfo"], **kwargs):
                    #print(f'inside task actin: left :{left} right: {right} and mid: {mid} and self.own.name: {self.node.name}')
                    #print(f'inside task actin: left_m :{left_m} right_m: {right_m} and mid: {mid} and self.own.name: {self.node.name}')
                    purify_subtask_left = kwargs['dependency_subtasks'][0]
                    purify_subtask_right = kwargs['dependency_subtasks'][1]
                    #print('inside ent_swap_action_middle')
                    #print('purify_subtask_left: ', purify_subtask_left.name)
                    #print('purify_subtask_right: ', purify_subtask_right.name)
                    
                    if len(purify_subtask_left.dependents) != 0 and len(purify_subtask_right.dependents) != 0:
                        #Find the swap subtask that is common to both these subtasks
                        #Will do this logic later,right now it's clear purification will be followed by swap
                        dependents = list(set(purify_subtask_left.dependents).intersection(purify_subtask_right.dependents))
                        
                        #Make use of previously mapped swap subtask
                        #print('Make use of previously mapped swap subtask')
                        return dependents
                    
                    def swap_subtask_action(memarg):

                        isEligible = False
                        if (memarg[0].state == "ENTANGLED"
                                and memarg[0].index in memory_indices
                                and memarg[0].remote_node == left_m
                                #and memarg[0].remote_node == left
                                #and memarg[0].fidelity >= reservation.fidelity
                                ):
                            
                            if (memarg[1].state == "ENTANGLED"
                                    and memarg[1].index in memory_indices
                                    and memarg[1].remote_node == right_m
                                    #and memarg[1].remote_node == right
                                    #and memarg[1].fidelity >= reservation.fidelity
                                    ):
                                    isEligible = True
                        
                        if (memarg[0].state == "ENTANGLED"
                                and memarg[0].index in memory_indices
                                and memarg[0].remote_node == right_m
                                #and memarg[0].fidelity >= reservation.fidelity
                                ):
                            
                            if (memarg[1].state == "ENTANGLED"
                                    and memarg[1].index in memory_indices
                                    and memarg[1].remote_node == left_m
                                    #and memarg[1].fidelity >= reservation.fidelity
                                    ):
                                    isEligible = True
                                    #Swap the two indices:
                                    temp = memarg[0]
                                    memarg[0] = memarg[1]
                                    memarg[1] = temp
                        
                        if not isEligible:
                            #print('Not eligible for swap')
                            #print(f'memarg[0].index : {memarg[0].index} and memarg[1].index : {memarg[1].index}')
                            #print(f'memarg[0].state : {memarg[0].state} an memarg[1].state : {memarg[1].state}')
                            #print(f'memarg[0].remote_node : {memarg[0].remote_node} an memarg[1].remote_node : {memarg[1].remote_node}')
                            #print(f'left_m: {left_m} and right_m: {right_m} and mid: {mid} and self.own.name: {self.node.name}')

                            return None, None, None
                        
                        memories = [info.memory for info in memarg]

                        def req_func1(protocols):
                            for protocol in protocols:
                                if (isinstance(protocol, EntanglementSwappingB)
                                        and protocol.memory.name == memarg[0].remote_memo):
                                    return protocol

                        def req_func2(protocols):
                            for protocol in protocols:
                                if (isinstance(protocol, EntanglementSwappingB)
                                        and protocol.memory.name == memarg[1].remote_memo):
                                    return protocol

                        protocol = EntanglementSwappingA(None, "ESA.%s.%s" % (memories[0].name, memories[1].name),
                                                        memories[0], memories[1],
                                                        success_prob=self.es_succ_prob, degradation=self.es_degradation)
                        dsts = [info.remote_node for info in memarg]
                        req_funcs = [req_func1, req_func2]
                        #print('Make use of newly created swap subtask : ',protocol.name)
                        return [protocol], dsts, req_funcs
                    
                    #print('Created new swap subtask')
                    ent_swap_subtask = SubTask(None, swap_subtask_action, memories_info)
                    purify_subtask_left.dependents = [ent_swap_subtask]
                    purify_subtask_right.dependents = [ent_swap_subtask]
                    ent_swap_subtask.dependencies = [purify_subtask_left, purify_subtask_right]
                    ent_swap_subtask.initial_dependency_subtasks.extend(purify_subtask_left.initial_dependency_subtasks)
                    ent_swap_subtask.initial_dependency_subtasks.extend(purify_subtask_right.initial_dependency_subtasks)
                    return purify_subtask_left.dependents
                
                task_swap_middle= Task('TaskSwapMiddle'+right+left, [last_left_task, last_right_task], self.node.timeline.now(), False, ent_swap_action_middle, self.node.task_manager)
                # if is_final_virtual_swap:
                #     task_swap_middle.is_vl_final_swap_task = True
                self.node.task_manager.add_task(task_swap_middle, [last_left_task, last_right_task])
                task_swap_middle.set_reservation(reservation)
                #print('ENT_SWAP_MIDDLE at: ', self.node.name)
                #print('last_left_task   : ', last_left_task.name)
                #print('last_right_task   : ', last_right_task.name)

                #If the left node is a virtual neighbor of this node, pick the cached task as a dependency:
                if left in self.node.virtual_links.keys():
                    #we need to set_dependency_to_subtask
                    subtask_list = self.node.virtual_links[left]
                    for subtask in subtask_list:
                        task_swap_middle.set_dependency_to_subtask(subtask)
                
                #If the right node is a virtual neighbor of this node, pick the cached task as a dependency:
                if right in self.node.virtual_links.keys():
                    #we need to set_dependency_to_subtask
                    subtask_list = self.node.virtual_links[right]
                    for subtask in subtask_list:
                        task_swap_middle.set_dependency_to_subtask(subtask)

                #If both sides are pre-shared VLs then we don't need to wait
                if left in self.node.virtual_links.keys() and right in self.node.virtual_links.keys():
                    task_swap_middle.can_run_on_init = True
                
            #task_list.append(curr_task)
    
    def set_swapping_success_rate(self, prob: float) -> None:
        assert 0 <= prob <= 1
        self.es_succ_prob = prob

    def set_swapping_degradation(self, degradation: float) -> None:
        assert 0 <= degradation <= 1
        self.es_degradation = degradation