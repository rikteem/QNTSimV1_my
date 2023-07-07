import qntsim
from qntsim.kernel.timeline import Timeline
from qntsim.kernel._event import Event
from enum import Enum, auto
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..topology.node import QuantumRouter,Node
from ..kernel.timeline import Timeline
if Timeline.DLCZ:
    from ..components.DLCZ_memory import Memory
elif Timeline.bk:
    from ..components.bk_memory import Memory
from ..message import Message
import itertools
from ..topology.message_queue_handler import ManagerType, ProtocolType,MsgRecieverType
from ..network_management.request import Request 

 

class ProtocolMsgType(Enum):

    """Defines possible message types for transport protocol."""

    SYN=auto()
    ACK=auto()
    SYNACK=auto()
    REQ=auto()
    REQACK=auto()
    RETRY=auto()

class CongestionMsgType(Enum):

    SUCCESS=auto()
    FAIL=auto()

 
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
              

    
class TransportManager():
    
    """
    Class to define the transport manager.
    Attributes:
        name (str): label for manager instance.
        owner (QuantumRouter): node that transport manager is attached to.
        
    """
    id=itertools.count()
    def __init__(self,owner):
        
        self.name='transport_manager'
        self.owner=owner
        self.transportprotocolmap={}
        

    def request(self, responder, start_time, size,end_time, priority, target_fidelity,timeout):
        """ 
        Fuction to take request from the application layer. It instanstiate protocol for the source node.
        Sends classical message to instantiate destinate protocol.
       
        Attributes:
        responder (str): name of destination node.
        timeout(int) : Timeout for the request.
        start_time(int) : start time for the request.
        size(int) : size for the request.
        target_fidelity(float) : target fidelity for the request
        end_time(int) : end time for the request
        """
        self.tp_id=next(self.id)
        # print('create request')
        transport_protocol_src=TransportProtocol(self.owner, responder,start_time,size,end_time,priority,target_fidelity, timeout) #Create source protocol instance
        self.owner.protocols.append(transport_protocol_src)         #Adding the protocol to the list of protocols
        self.transportprotocolmap[self.tp_id]=transport_protocol_src
        message=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,ProtocolMsgType.REQ,src_obj=transport_protocol_src) 
        # print('message',self.owner,responder, self.owner.name, responder.name,message.msg_type,message.receiver,message.receiver_type)  #Sending msgtype REQ to start destination protocol
        self.owner.message_handler.send_message(responder,message)


    def received_message(self,src,msg: Message):
        
        """Method to receive messages.
        This method receives messages from transport manager.
        Depending on the message, different actions may be taken by the protocol.
        Args:
            src (str): name of the source node sending the message.
            msg (Message): message received.
        """

        msg_type=msg.msg_type
    

        if msg_type is ProtocolMsgType.REQ:
            # #print('Session between src and dest',self.owner.name,msg.objsrc.owner.name,msg.objsrc.starttime*1e-12,msg.objsrc.size,msg.objsrc.timeout*1e-12)
            ##print('Message passing working')
            src_obj=msg.kwargs.get('src_obj')
            #print('src obj', src_obj.owner.name,src_obj.starttime,src_obj.endtime,src_obj.size,src_obj.priority,src_obj.target_fidelity)
            transport_protocol_dest=TransportProtocol(self.owner, src_obj.owner.name,src_obj.starttime,src_obj.endtime,src_obj.size,src_obj.priority,src_obj.target_fidelity,src_obj.timeout)  #Creating destination protocol
            self.owner.protocols.append(transport_protocol_dest)
            message=Message(MsgRecieverType.MANAGER, ManagerType.TransportManager,ProtocolMsgType.REQACK,dest_obj=transport_protocol_dest,src_obj=src_obj)
            self.owner.message_handler.send_message(src,message)
            

        elif msg_type is ProtocolMsgType.REQACK:
            ##print('REQACK recieved from destination node')
            src_obj=msg.kwargs.get('src_obj')
            dest_obj=msg.kwargs.get('dest_obj')
            src_obj.create_session(dest_obj)  #Call create session of the transport protocol after both protocol instance has been created.
            # self.owner.message_handler.manager_is_over(msg.receiver)
        
        self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)

    def notify_tm(self,fail_time,tp_id,status):
        '''
        Method to recieve the acknowledgements of Reject,Abort and Approved from link layer.
        '''

        #print('failed inside tranport manager',tp_id,fail_time*1e-12,status,self.transportprotocolmap,self.owner.name)
        for tpid,tp in self.transportprotocolmap.items():
            #print('id,protocol',tp_id,tp,status)
            
            if tp_id==tpid and (status == 'REJECT' or status == 'ABORT'):
                #print('tm notify reject',(tp.starttime+self.owner.timeline.now())*1e-12)
                # Creating an event for notify method of transport protocol for retrials.

                #process=Process(tp,'notify_tp',[fail_time,status])
                #event=Event(tp.starttime+self.owner.timeline.now(),process)
                event=Event(tp.starttime+self.owner.timeline.now(),tp,'notify_tp',[fail_time,status])
                self.owner.timeline.events.push(event)
                #self.owner.timeline.schedule(event)
                break
        
    
    def send_reallocation( self , CW ,tpid ,src,responder,start_time,end_time,target_fidelity,priority ,remaining_demand_size):

            
            nm=self.owner.network_manager
            #print("CW for congestion",CW ,remaining_demand_size)
            nm.create_request(src,responder, start_time , end_time,CW, target_fidelity,priority,tpid,1,remaining_demand_size)


    def recv_fail_reallocation(self,CW,request:"Request",remaining_demand_size):
        
        CW=min(int(CW/2),remaining_demand_size)
        if CW!=0:
            #send batch 
            time_now=self.owner.timeline.now()
            ##print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
            #if time_now < self.starttime + self.timeout: #If the current time is less than starttime+timeout go for retriails
            #print("CW/2 for congestion",CW)
            id = request.tp_id
            event=Event(self.owner.timeline.now(),self,'send_reallocation',[CW,id,request.initiator,request.responder,request.start_time,request.end_time,request.fidelity,request.priority,remaining_demand_size])
            self.owner.timeline.events.push(event)
        if CW==0:
            return

    def recv_success_reallocation(self,CW,request:"Request",remaining_demand_size):

                
            #CW=min(CW and original demand size)

            #####min(CW+1,Remaining demand)
            #CW=min(CW+1,10)
            if remaining_demand_size==0:
                return
            
            CW=min(CW+1,remaining_demand_size)
            time_now=self.owner.timeline.now()
            #print("transport manager success message",time_now,request.start_time)
            ##print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
            #if time_now < request.start_time + request.timeout: #If the current time is less than starttime+timeout go for retriails
            id = request.tp_id
            #request.start_time=time_now
            event=Event(self.owner.timeline.now(),self,'send_reallocation',[CW,id,request.initiator,request.responder,time_now+0.01e12,request.end_time,request.fidelity,request.priority,remaining_demand_size])
            self.owner.timeline.events.push(event)


class TransportProtocol(TransportManager):

    """Transport protocol for quantum router.
    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        other (str): name of destination node.
        timeout(int) : Timeout for the request.
        starttime(int) : start time for the request.
        size(int) : size for the request.
    """

    def __init__(self,owner , other, starttime,size,endtime,priority,targetfidelity,timeout):
        self.owner=owner
        self.other= other
        self.timeout=timeout
        self.starttime=starttime
        self.size=size
        self.endtime=endtime
        self.priority=priority
        self.name="TransportProtocol"
        self.retry=0
        self.target_fidelity = targetfidelity
        self.reqcount=0

    def create_session(self,dest_obj):

        """ 
        Creates a session between source and destination protocol. Sends classical messgae to start 3 way handshake to decide the timeout of the request.
        """

        ##print('session created',dest_obj.owner.name, self.name)
        message=Message(MsgRecieverType.PROTOCOL,self.name,ProtocolMsgType.SYN,src_obj=self,dest_obj=dest_obj)
        dest_obj.owner.message_handler.send_message(self.owner.name,message)
       
    
    def received_message(self,src,msg: Message):

        """Method to receive messages.
        This method receives messages from transport protocols.
        Depending on the message, different actions may be taken by the protocol.
        Args:
            src (str): name of the source node sending the message.
            msg (Message): message received.
        """


        # #print('source owner',src,self.owner.name)
        msg_type=msg.msg_type
        # #print('mssg type',msg_type)

        #Timeout to be decided between the source and destination protocol
        # After SYNACK is achieved both protocols will be on the same level
        # 
        # Call network manager for entanglement creation.
        # If the request fails, within the timeout time, go fo retrials.
        

        if msg_type is ProtocolMsgType.SYN:
            ##print('SYN between',self.owner.name,src)            
            dest_timer=self.owner.timeline.now()
            src_obj=msg.kwargs.get('src_obj')
            dest_obj=msg.kwargs.get('dest_obj')
            message=Message(MsgRecieverType.PROTOCOL,self.name,ProtocolMsgType.SYNACK,src_obj=src_obj,dest_obj=dest_obj,dest_timer=dest_timer)
            # #print('ccccc',self.owner.name,src)
            self.owner.message_handler.send_message(src,message)
            # msg.src_obj.create_requests()


        elif msg_type is ProtocolMsgType.SYNACK:
            ##print('SYNACK received',self.owner.name,src)
            src_timer=self.owner.timeline.now()
            src_obj=msg.kwargs.get('src_obj')
            dest_obj=msg.kwargs.get('dest_obj')
            dest_time=msg.kwargs.get('dest_timer')
            final_timer=src_obj.starttime*1e-12 + self.timeout*1e-12
            # #print('final timer', final_timer)
           
            message=Message(MsgRecieverType.PROTOCOL,self.name,ProtocolMsgType.ACK,src_obj=src_obj,dest_obj=dest_obj,final_timer=final_timer)
            self.owner.message_handler.send_message(src,message)

        
        
        elif msg_type is ProtocolMsgType.ACK:
            tn=self.owner.timeline.now()
            ##print('ACKs time',self.owner.name,src,tn*1e-12,self)
            self.create_requests()
                 
        # elif msg_type is ProtocolMsgType.RETRY:
        #     #print('Retry Message')
        self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)


    def create_requests(self):
        '''
        Method to create request by calling the network manager.
        '''
        ##print('reqcount',self.reqcount)
        for id,pro in self.owner.transport_manager.transportprotocolmap.items():
            ##print('qq',id,pro,self)
            if self == pro and self.reqcount==0:  # Self.reqcount to stop multiple calls for same request.
                #print('create requestss',self.owner.name,self.other,self.starttime*1e-12,self.endtime*1e-12,self.priority,id)
                nm=self.owner.network_manager
                # process=Process(nm,'request', [self.other,self.starttime,self.endtime,self.size,.5,self.priority,id] )
                # event=Event(8e12,process,0)
                # self.owner.timeline.schedule(event)
                nm.create_request(self.owner.name,self.other, start_time=self.starttime , end_time=self.endtime, memory_size=self.size, target_fidelity=self.target_fidelity,priority=self.priority,tp_id=id,congestion_retransmission=0,remaining_demand_size=self.size)
                
                self.reqcount+=1

    def notify_tp(self,ftime,status):
        '''
        Notify method of the transport protocol called from notify method of transport manager. Checks if the time for retrial is less than timeout time.
        '''
        
        time_now=self.owner.timeline.now()
        #print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
        if time_now < self.starttime + self.timeout: #If the current time is less than starttime+timeout go for retriails
            # #print('for retrials',self.owner.timeline.now()*1e-12)
            self.retrials(status)



    def retrials(self,status):
        '''
        Method to create request for the retrials.
        '''
        #print('Inside retrials',status,self,self.starttime,self.owner.name,self.other)
        #message=Message(ProtocolMsgType.RETRY,None)
        
        #congestion=1
        # self.owner.message_handler.send_message(self.other,message)
        ##print()
        #if status != 'APPROVED' and self.retry < 5:
        #print("retry no.",self.retry ,status)

        if self.retry==3:
        #if retrails fails

            CW=2
            #CW_init = average demand size
            if self.size < CW  :
                CW=self.size
                     
        #self.congestion=1
            time_now=self.owner.timeline.now()
            for id,pro in self.owner.transport_manager.transportprotocolmap.items():
                if self==pro and self.starttime < self.endtime:
                    #print('1st event created for congestion ',id)
                    if time_now < self.starttime+self.timeout:
                        remaining_demand_size=self.size
                        event=Event(self.owner.timeline.now(),self.owner.transport_manager,'send_reallocation',[CW,id,self.owner.name,self.other, time_now+0.01e12,self.endtime, 0.7,self.priority,remaining_demand_size])
                        self.owner.timeline.events.push(event)

        if status == 'REJECT' and self.retry < 3:
           
            self.retry +=1
            self.starttime += 0.2e12 #Added value to starttime to stop assertion error for timeline time less than reservation start time.
            ##print('retry count',self.retry,self.starttime*1e-12,self.endtime*1e-12,self.owner.timeline.now()*1e-12)
            for id,pro in self.owner.transport_manager.transportprotocolmap.items():
                # #print('ww',id,pro)
                if self==pro and self.starttime < self.endtime:
                    
                    #print('retrying',pro.owner,pro.other,self.owner.name,self.other,self.starttime*1e-12,self.owner.timeline.now()*1e-12)
                    nm=self.owner.network_manager
                    nm.create_request(self.owner.name,self.other, start_time=self.starttime , end_time=self.endtime, memory_size=self.size, target_fidelity=.5,priority=self.priority,tp_id=id,congestion_retransmission=0,remaining_demand_size=self.size)
                    # process=Process(nm,'request',[self.other,self.starttime,self.endtime,self.size,.5,self.priority,id])
                    # event=Event(self.starttime+self.owner.timeline.now(),process,0)
                    # self.owner.timeline.schedule(event)"""
        
            ##print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
            #if time_now < self.starttime + self.timeout: #If the current time is less than starttime+timeout go for retriails
            ##print('1st event created for congestion ')
            #event=Event(self.owner.timeline.now(),self.owner.transport_manager,'send_reallocation',[CW,id,self.owner.name,self.other, self.starttime,self.endtime, 0.5,self.priority])
            #self.owner.timeline.events.push(event)
            #self.owner.timeline.schedule(event)     
"""

    def send_reallocation( self , CW ,tpid  ):

        for id,pro in self.owner.transport_manager.transportprotocolmap.items():

            if self==pro and id==tpid and self.starttime < self.endtime:

                nm=self.owner.network_manager

                nm.create_request(self.owner.name,self.other, start_time=self.starttime , end_time=self.endtime, memory_size=CW, target_fidelity=self.target_fidelity,priority=self.priority,tp_id=id,congestion_retransmission=1)
                
                break


    def recv_reallocation(msg):


        if msg.msg_type==FAIL:
            CW=CW/2
            if CW!=0:
                #send batch 
                time_now=self.owner.timeline.now()
        ##print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
                if time_now < self.starttime + self.timeout: #If the current time is less than starttime+timeout go for retriails
                    id = msg.request.tp_id
                    event=Event(pro.starttime+self.owner.timeline.now(),pro,'send_reallocation',[CW,id])
                    self.owner.timeline.events.push(event)

                    
        elif msg.msg_type==SUCCESS:

            CW=min(CW+1,msg.request.demand_size)

            time_now=self.owner.timeline.now()
            ##print('protocol notify',ftime*1e-12,self.starttime*1e-12,self.timeout*1e-12,time_now*1e-12)
                if time_now < self.starttime + self.timeout: #If the current time is less than starttime+timeout go for retriails
                    id = msg.request.tp_id
                    event=Event(pro.starttime+self.owner.timeline.now(),pro,'send_reallocation',[CW,id])
                    self.owner.timeline.events.push(event)

            #sendbatch
"""
# reallocation of resources:
# ocurrs at later time in timeline scheduler as an event 
# Triggered when FAIL_RESOURCE is triggered 
"""
######FLOW OF RETRYING AT CONGESTION :

    ##Receives FAIL_ACK after retrails by source of request

    #CW_init=avg demand size
    
    #send reserve resources of size CW msg to request.source

    #on receive message 

    #if fail to to reserve resources :
       #CW=CW/2
       #send reserve resources msg to request.source

    #if success:
        #CW=CW+1
        #send reserve resources msg to request.source
    
    # untill demand completes or CW =0 

    # each window iteration of request should be made as event 
"""