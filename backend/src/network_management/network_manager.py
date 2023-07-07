"""Definition of the Network Manager.
This module defines the NetworkManager class, an implementation of the SeQUeNCe network management module.
Also included in this module is the message type used by the network manager and a function for generating network managers with default protocols.
"""
import itertools
from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..topology.node import QuantumRouter
    from ..protocol import StackProtocol
    from ..kernel._event import Event
    from .request import Request
    from .request import RoutingProtocol 
    from .request import ReservationProtocol

import logging

from ..kernel._event import Event
from ..message import Message
from ..resource_management.resource_manager import ResourceManagerMsgType
from ..transport_layer.transport_manager import TransportProtocol
from .request import Request, ReservationProtocol, RoutingProtocol, RRPMsgType
from .reservation import Reservation, ResourceReservationProtocol, RSVPMsgType
from .routing import (NewRoutingProtocol, RoutingTableUpdateProtocol,
                      StaticRoutingProtocol)

logger = logging.getLogger("main_logger." + "network_manager")


class NetworkManager():
    """Network manager implementation class.
    The network manager is responsible for the operations of a node within a broader quantum network.
    This is done through a `protocol_stack` of protocols, which messages are passed and packaged through.
    Attributes:
        name (str): name of the network manager instance.
        owner (QuantumRouter): node that protocol instance is attached to.
        protocol_stack (List[StackProtocol]): network manager protocol stack.
    """
    #, protocol_stack: "List[StackProtocol]"
    id=itertools.count()
    def __init__(self, owner: "QuantumRouter"):
        """Constructor for network manager.
        Args:
            owner (QuantumRouter): node network manager is attached to.
            protocol_stack (List[StackProtocol]): stack of protocols to use for processing.
        """

        self.name = "network_manager"
        self.owner = owner
        self.abort = False
        self.requests={}
        self.networkmap={}
        self.tp_id=None
        self.schedule_rtup()
        self.es_swap_success = 1
        self.es_swap_degradation = 0.99
        # self.net_id=next(self.id)
    
    def set_swap_success(self, es_swap_success):
        self.es_swap_success = es_swap_success

    def set_swap_degradation(self, es_swap_degradation):
        self.es_swap_degradation = es_swap_degradation

    def received_message(self, src: str, msg: "Message"):
        """Method to receive transmitted network reservation method.
        Will pop message to lowest protocol in protocol stack.
        Args:
            src (str): name of source node for message.
            msg (NetworkManagerMessage): message received.
        Side Effects:
            Will invoke `pop` method of 0 indexed protocol in `protocol_stack`.
        """
        #if the abort message is received, set the abort flag for the network manager and append the aborted connection to the preempted reservations
        """ if msg.msg_type == RSVPMsgType.ABORT:
            self.abort = True
            self.preempted_reservation = msg.reservation
            # #print("received a message to abort the connection")
            # self.notify_nm(status='ABORT')
            return
        self.protocol_stack[0].pop(src=src, msg=msg.payload)"""
        if msg.msg_type==RRPMsgType.RESERVE :
            #print("received at ", self.owner.name,msg.kwargs)
            self.process_request(msg)
        self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)
        #logger.info("Reservation message received by "+self.owner.name)
        

   
    #Add notify method
    def notify_nm(self,status,ReqId,ResObj):
        
        # This method would receive notification from the reservation protocols about the status of the request.
        # Depending upon the nature of the status of the request it would propagate that message to the transport manager notify method.
        # 

        ####bug
        #self.networkmap[ReqId]=[self.tp_id,status]
        if not ResObj.isvirtual:
            self.networkmap[ReqId]=[ResObj.tp_id,status]
        #print('netwrok map',self.networkmap)
        # for ReqId,ResObj in self.requests.items():
        #     #print('REqId',ReqId,self.tp_id,status,ResObj.isvirtual)
           
        #     #print('nnwetwork map',self.networkmap)
        if ResObj.isvirtual:
            # #print('approved virtual link',self.owner.name,ResObj.responder)
            self.owner.virtualneighbors.append(ResObj.responder)
            self.owner.virtualneighbors=list(set(self.owner.virtualneighbors))
            # #print('virtual neighbours',self.owner.name,self.owner.virtualneighbors,self.owner.timeline.now()*1e-12)
        #print('Network map',self.networkmap)
        for key,value in self.networkmap.items():
            ##print('id status',key , value[1])
            ##print("network map",self.networkmap.items())
            ##print( "notify_nm ",ResObj.initiator,ResObj.responder,status,ResObj.status,value[1],value[0])
            if value[0]==ResObj.tp_id and ( value[1]== 'REJECT' or value[1]=='ABORT'): # For reject and abort call notify of the transport manager
                fail_time=self.owner.timeline.now()
                #print('faileds,tp_id,status,resobj.tpid',fail_time*1e-12,value[0],value[1],ResObj.tp_id)
                self.owner.transport_manager.notify_tm(fail_time,value[0],value[1])
                break

         
        #call transport manager notify

    def createvirtualrequest(self, initiator, responder: str, start_time: int, end_time: int, memory_size: int, target_fidelity: float) -> None:#$$
        """Method to make an entanglement request.
        Will defer request to top protocol in protocol stack.
        Args:
            responder (str): name of node to establish entanglement with.
            start_time (int): simulation start time of entanglement.
            end_time (int): simulation end time of entanglement.
            memory_size (int): number of entangledd memory pairs to create.
            target_fidelity (float): desired fidelity of entanglement.
        Side Effects:
            Will invoke `push` method of -1 indexed protocol in `protocol_stack`.
        """

        # self.protocol_stack[-1].push(responder, start_time, end_time, memory_size, target_fidelity, True,1)#$$
        virtual_request = Request(initiator,responder, start_time, end_time, memory_size, target_fidelity, isvirtual=True)
        self.requests.update({virtual_request.id:virtual_request})
        virtual_request.status = 'INITIATED'
        routing_protocol = RoutingProtocol(self.owner,initiator,responder,[], self.owner.name)
        resource_reservation_protocol = ReservationProtocol(self.owner,virtual_request,routing_protocol)

        self.owner.reservation_manager.append(resource_reservation_protocol)

        resource_reservation_protocol.start()
    
    def create_request(self,initiator:str, responder: str, start_time: int, end_time: int, memory_size: int, target_fidelity: float,priority: int,tp_id: int,congestion_retransmission:int,remaining_demand_size:int):
        
        user_request = Request(initiator,responder,start_time,end_time,memory_size,target_fidelity,priority=priority,tp_id=tp_id,congestion_retransmission=congestion_retransmission)
        user_request.status='INITIATED'
        user_request.remaining_demand_size=remaining_demand_size
        self.requests.update({user_request.id:user_request})
        # print("user request id ,tp_id ,src,path,des,size ",user_request.id,user_request.tp_id, user_request.initiator,user_request.path,user_request.responder,user_request.memory_size,memory_size)
        routing_protocol=RoutingProtocol(self.owner,initiator,responder,[],self.owner.name)
        #nextnode=routing_protocol.next_hop()
        ##print(nextnode)
        resource_reservation_protocol = ReservationProtocol(self.owner,user_request,routing_protocol)
        self.owner.reservation_manager.append(resource_reservation_protocol)
        resource_reservation_protocol.start()

    def process_request(self ,msg: "Message"): 
        payload=msg.kwargs['request']
        ##print('process request payload', payload)
        ##print(user_request)
        user_request = payload
        #tmp_path =msg.temp_path
        ##print(msg.payload)
        ##print(user_request)
        # Resource Reservation Protocol Object
    
        # Routing Protocol Object
        ##print("in request temp_path,marker",user_request,self.owner.name,msg.temp_path,msg.marker)
        routing_protocol=RoutingProtocol(self.owner,user_request.initiator,user_request.responder,msg.temp_path,msg.marker)

        resource_reservation_protocol = ReservationProtocol(self.owner,user_request,routing_protocol, self.es_swap_success, self.es_swap_degradation)

        self.owner.reservation_manager.append(resource_reservation_protocol)
   
        # ResourceReservationProtocol.Start()
        resource_reservation_protocol.start()

    def schedule_rtup(self):
        #print("---------------rtup--------------" , self.owner.name)

        routing_update=RoutingTableUpdateProtocol(self.owner,self.owner.name)
        protocol_start_time=0
        #process = Process(routing_update, "sendmessage",[])
        #event = Event(protocol_start_time+owner.timeline.now(), process)
        event = Event(protocol_start_time+self.owner.timeline.now(), routing_update, "sendmessage",[])
        #owner.timeline.schedule(event)
        self.owner.timeline.schedule_counter += 1
        self.owner.timeline.events.push(event)
        self.owner.protocols.append(routing_update)