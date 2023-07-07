from enum import Enum, auto
from math import inf
from collections import defaultdict

from aenum import Enum
# from ..entanglement_management.generation import GenerationMsgType
import logging
logger = logging.getLogger("main_logger." + "bk_swapping")

class MsgRecieverType(Enum):

    PROTOCOL = auto()
    MANAGER = auto()

class GenerationMsgType(Enum):
    """Defines possible message types for entanglement generation."""

    NEGOTIATE = auto()
    NEGOTIATE_ACK = auto()
    MEAS_RES = auto()
    BSM_ALLOCATE = auto()
    CALL_BSM =auto()

class ManagerType(Enum):

    NetworkManager = auto()
    ResourceManager = auto()
    MemoryManager = auto()
    TransportManager = auto()
    VirtualLinkManager = auto()
    ReservationManager = auto()


class ProtocolType(Enum):

    TransportProtocol = auto()
    NewRoutingProtocol = auto()
    RoutingTableUpdateProtocol = auto()
    ResourceReservationProtocol = auto()
    EntanglementGenerationA = auto()
    # EntanglementGenerationB = auto()
    BBPSSW = auto()
    EntanglementSwapping = auto()
    # EntanglementSwappingB = auto()
    # extend_enum(EntanglementGenerationA, )

class MessageQueueHandler():

    def __init__(self,owner) -> None:
        
        self.owner=owner
        self.protocol_queue = {}
        self.manager_queue = {}
        
    def send_message(self, dst:str, msg, priority = inf):
        #logger.info(msg.msg_type)
        if priority == inf:
            priority = self.owner.timeline.schedule_counter
        #print('send message', dst, self.owner.cchannels,self.owner.name)
        self.owner.cchannels[dst].transmit(msg, self.owner, priority)
   
    def push_message(self, src, msg):
        #logger.info(msg.msg_type)
        # self.protocol_queue = defaultdict(tuple)
        # self.manager_queue = defaultdict(tuple)
        #if hasattr(msg, 'id'):
            #if msg.id == 1 or msg.id == 2:
                #print('push message at ', self.owner.name, ' msg.receiver: ',msg.receiver)
                

        if msg.receiver_type == MsgRecieverType.MANAGER:

            # self.manager_queue[msg.receiver.name]=[[msg],0]
            ##print("push msg.receiver",msg.receiver.name)

            if msg.receiver.name in self.manager_queue.keys():

                #self.lock.acquire()

                if self.manager_queue[msg.receiver.name][1]==1 :

                    #if msg.receiver == ManagerType.ResourceManager:

                        #if msg.msg_type==ResourceManagerMsgType.REQUEST:
                        ##print(" Append Recv by resource manager ",msg.kwargs['protocol'].name,msg.msg_type,msg.receiver.name,len(self.manager_queue[msg.receiver.name][0]))

                    #self.manager_queue[msg.receiver.name]=[[(msg,src)],1]
                    self.manager_queue[msg.receiver.name][0].append((msg,src))
                    #self.manager_queue[msg.receiver.name][1]=1
                    ##print(" manager queue in push message",self.manager_queue,self.owner.name)

                else:

                    self.manager_queue[msg.receiver.name][1]=1

                    if msg.receiver == ManagerType.TransportManager:
                        ##print("transprot manager first msg")
                        self.owner.transport_manager.received_message(src, msg)

                    elif msg.receiver == ManagerType.ResourceManager:
                        #if msg.msg_type==ResourceManagerMsgType.REQUEST:
                            ##print(" Recv by resource manager",msg.kwargs['protocol'].name)
                        ##print(" Recv by resource manager",msg.kwargs['protocol'].name,msg.msg_type)
                        
                        self.owner.resource_manager.received_message(src, msg)
                
                    elif msg.receiver == ManagerType.NetworkManager:
                        self.owner.network_manager.received_message(src, msg)
                
                    elif msg.receiver == ManagerType.ReservationManager:
                        ##print('reservation manager', msg.kwargs['request'])
                        for reservation in self.owner.reservation_manager:
                            if reservation.request == msg.kwargs['request']:
                                reservation.receive_message(msg)
                                break
                #self.lock.release()

                #self.manager_queue[msg.receiver.name].append([[msg],0])
            else:
                
                #self.manager_queue[msg.receiver.name]=[[(msg,src)],1]


                self.manager_queue[msg.receiver.name]=[[],1]
                
                if msg.receiver == ManagerType.TransportManager:
                    ##print("transprot manager first msg")
                    self.owner.transport_manager.received_message(src, msg)

                elif msg.receiver == ManagerType.ResourceManager:

                    #if msg.msg_type==ResourceManagerMsgType.REQUEST:
                       # #print(" Recv by resource manager",msg.kwargs['protocol'].name)
                    ##print(" Recv by resource manager",msg.kwargs['protocol'].name,msg.msg_type)
                    self.owner.resource_manager.received_message(src, msg)
                
                elif msg.receiver == ManagerType.NetworkManager:
                    self.owner.network_manager.received_message(src, msg)
                
                elif msg.receiver == ManagerType.ReservationManager:
                    ##print('reservation manager', msg.kwargs['request'])
                    for reservation in self.owner.reservation_manager:
                        if reservation.request == msg.kwargs['request']:
                            reservation.receive_message(msg)
                            break
                #self.lock.release()


            

        if msg.receiver_type == MsgRecieverType.PROTOCOL:
            # #print('Message receiver type',msg.receiver,msg.receiver)
            ##print("push msg.receiver",msg.receiver)

            #print ("protocol received in push message",msg.msg_type)
            # if str(msg.msg_type) == 'GenerationMsgType.MEAS_RES':
                ##print("mmmeasure res message", msg.msg_type,src,self.owner.name)

            if msg.receiver in self.protocol_queue.keys():
                
                #lock start
                #self.lock.acquire()
                ##print("if measure res message", msg.msg_type)
                if self.protocol_queue[msg.receiver][1]==1:
                    ##print('ifif send measure res message', msg.msg_type, msg.receiver)
                    #self.protocol_queue[msg.receiver]=[[(msg,src)],1]

                    ###self.protocol_queue[msg.receiver][0].append((msg,src))

                     
                    
                    self.protocol_queue[msg.receiver][0].append((msg,src))

                   
                    return 



                else :
                    self.protocol_queue[msg.receiver][1]=1

                    for protocol in self.owner.protocols:
                        if protocol.name==msg.receiver:
                            protocol.received_message(src,msg)
                        
            else:
                
                self.protocol_queue[msg.receiver]=[[],1]
                
                for protocol in self.owner.protocols:
                    
                    if protocol.name==msg.receiver:
                        
                        protocol.received_message(src,msg)
                    
    def process_msg(self,receiver_type,receiver):

        receiver_type=receiver_type
        receiver=receiver

       
        if receiver_type == MsgRecieverType.PROTOCOL:
            
            protocol_id=receiver
            ##print("process msg ,",protocol_id,len(self.protocol_queue[protocol_id][0]))
            if len(self.protocol_queue[protocol_id][0])==0 :
                #lock
                #lock.acquire()
                ##print("len 0 process_msg",receiver)
                self.protocol_queue[protocol_id][1]=0
                #lock.release
                #lock end

            
            else :
            
                msg,src=self.protocol_queue[protocol_id][0].pop(0)
                ##print("len >0 process_msg",msg ,src)
                #src=self.protocol_queue[protocol_id][0].pop(0)[1]
                ##print("process msg measure res message", msg.msg_type)
                for protocol in self.owner.protocols: 
                    if protocol.name==receiver:
                        protocol.received_message(src,msg)

        if receiver_type == MsgRecieverType.MANAGER:
                    
            if len(self.manager_queue[receiver.name][0])==0:
                ##print("len 0 process_msg",receiver.name ,self.owner.name)
                self.manager_queue[receiver.name][1]=0
                ##print("manager queue in proc msg len 0",self.manager_queue,self.manager_queue[receiver.name],self.owner.name)
                return
            
            else:

                msg,src=self.manager_queue[receiver.name][0].pop(0)
                #src=self.manager_queue[msg.receiver.name][0].pop(0)
                ##print("len >0 process_msg",msg ,src)
                if receiver == ManagerType.TransportManager:
                    self.owner.transport_manager.received_message(src, msg)

                elif receiver == ManagerType.ResourceManager:
                    self.owner.resource_manager.received_message(src, msg)
                
                elif receiver == ManagerType.NetworkManager:
                    self.owner.network_manager.received_message(src, msg)
                
                elif receiver == ManagerType.ReservationManager:
                    ##print('reservation manager', msg.kwargs['request'])
                    for reservation in self.owner.reservation_manager:
                        if reservation.request == msg.kwargs['request']:
                            reservation.receive_message(msg)
                            break     
                        
 
