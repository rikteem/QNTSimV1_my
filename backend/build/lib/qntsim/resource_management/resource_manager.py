"""Definition of resource managemer.
This module defines the resource manager, which composes the SeQUeNCe resource management module.
The manager uses a memory manager and rule manager to track memories and control entanglement operations, respectively.
This module also defines the message type used by the resource manager.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Callable, List
if TYPE_CHECKING:
    from ..topology.node import QuantumRouter
    from .rule_manager import Rule
from ..kernel.timeline import Timeline
if Timeline.DLCZ:
    from ..components.DLCZ_memory import Memory
elif Timeline.bk:
    from ..components.bk_memory import Memory

from ..entanglement_management.entanglement_protocol import EntanglementProtocol
from ..message import Message
from .rule_manager import RuleManager
from .memory_manager import MemoryManager
from ..topology.message_queue_handler import ManagerType, ProtocolType,MsgRecieverType
import logging
logger = logging.getLogger("main_logger.resource_management"+"resource_manager")

class ResourceManagerMsgType(Enum):
    """Available message types for the ResourceManagerMessage."""

    REQUEST = auto()
    RESPONSE = auto()
    RELEASE_PROTOCOL = auto()
    RELEASE_MEMORY = auto()
    ABORT = auto()


class Message():
    """Message for resource manager communication.
    There are four types of ResourceManagerMessage:
    * REQUEST: request eligible protocols from remote resource manager to pair entanglement protocols.
    * RESPONSE: approve or reject received request.
    * RELEASE_PROTOCOL: release the protocol on the remote node
    * RELEASE_MEMORY: release the memory on the remote node
    Attributes:
        ini_protocol (str): name of protocol that creates the original REQUEST message.
        request_fun (func): a function using ResourceManager to search eligible protocols on remote node (if `msg_type` == REQUEST).
        is_approved (bool): acceptance/failure of condition function (if `msg_type` == RESPONSE).
        paired_protocol (str): protocol that is paired with ini_protocol (if `msg-type` == RESPONSE).
    """

    def __init__(self, receiver_type: Enum, receiver: Enum, msg_type, **kwargs) -> None:

        self.id = None
        self.receiver_type = receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs




class ResourceManager():
    """Class to define the resource manager.
    The resource manager uses a memory manager to track memory states for the entanglement protocols.
    It also uses a rule manager to direct the creation and operation of entanglement protocols.
    Attributes:
        name (str): label for manager instance.
        owner (QuantumRouter): node that resource manager is attached to.
        memory_manager (MemoryManager): internal memory manager object.
        rule_manager (RuleManager): internal rule manager object.
        pending_protocols (List[Protocol]): list of protocols awaiting a response for a remote resource request.
        waiting_protocols (List[Protocol]): list of protocols awaiting a request from a remote protocol.
    """

    def __init__(self, owner: "QuantumRouter"):
        """Constructor for resource manager.
        
        Args:
            owner (QuantumRouter): node to attach to.
        """

        self.name = "resource_manager"
        self.owner = owner
        self.memory_manager = MemoryManager(owner.memory_array)
        self.memory_manager.set_resource_manager(self)
        # self.rule_manager = RuleManager()
        # self.rule_manager.set_resource_manager(self)
        # protocols that are requesting remote resource
        self.pending_protocols = []
        # protocols that are waiting request from remote resource
        self.waiting_protocols = []
        self.memory_to_protocol_map = {}
        self.reservation_to_memory_map={}
        self.reservation_id_to_memory_map={}
        self.reservation_to_events_map = {}

    # def load(self, rule: "Rule") -> bool:
    #     """Method to load rules for entanglement management.
    #     Attempts to add rules to the rule manager.
    #     Will automatically execute rule action if conditions met.
    #     Args:
    #         rule (Rule): rule to load.
    #     Returns:
    #         bool: if rule was loaded successfully.
    #     """
    #     #print("This is the rule------", rule)
    #     # print(rule.action, rule.get_reservation().initiator, "----------------->", rule.get_reservation().responder)
    #     self.rule_manager.load(rule)
        
    #     for memory_info in self.memory_manager:            
    #         memories_info = rule.is_valid(memory_info)
    #         if len(memories_info) > 0:

    #             rule.do(memories_info)    

    #             #if type(rule.protocols[0]).__name__ == 'EntanglementSwappingB':
    #             #    print(f'Found memory indices for Ent EntanglementSwappingB for the node: {self.owner.name}')           

    #             for info in memories_info:
    #                 #print('type of rule: ', type(rule.protocols[0]).__name__)
    #                 #print('Rule name is: ', rule.protocols)
    #                 #print('Update to Occupied from load() method')
    #                 #print(f'Shifting state to OCCUPIED for memory index  inside load() :{info.index} for the node: {self.owner.name}')
        
    #                 #Only change the status of memory to occupied if it is not an instance of ESB
    #                 #if type(rule.protocols[0]).__name__ != 'EntanglementSwappingB':
    #                 info.to_occupied()                

    #     return True

    # def expire(self, rule: "Rule") -> None:
    #     """Method to remove expired rule.
    #     Will update rule in rule manager.
    #     Will also update and modify protocols connected to the rule (if they have already been created).
    #     Args:
    #         rule (Rule): rule to remove.
    #     """
    #     # print('Expiree')
    #     created_protocols = self.rule_manager.expire(rule)
    #     while created_protocols:
    #         protocol = created_protocols.pop()
    #         if protocol in self.waiting_protocols:
    #             self.waiting_protocols.remove(protocol)
    #         elif protocol in self.pending_protocols:
    #             self.pending_protocols.remove(protocol)
    #         elif protocol in self.owner.protocols:
    #             self.owner.protocols.remove(protocol)
    #         else:
    #             raise Exception("Unknown place of protocol")

    #         for memory in protocol.memories:
    #             self.update(protocol, memory, "RAW")

    def update(self, protocol: "EntanglementProtocol", memory: "Memory", state: str) -> None:
        """Method to update state of memory after completion of entanglement management protocol.
        Args:
            protocol (EntanglementProtocol): concerned protocol.
            memory (Memory): memory to update.
            state (str): new state for the memory.
        Side Effects:
            May modify memory state, and modify any attached protocols.
        """
        # #print('Memory label',memory.name)
        self.memory_manager.update(memory, state)
        #if self.owner.name == 'd':
        ##print(f'Updated status at node: {self.owner.name} to {state}')
        #    #print('Size of rule_manager: ', len(self.rule_manager))
        if protocol:
            memory.detach(protocol)
            memory.attach(memory.memory_array)
            #if protocol in protocol.rule.protocols:
            if protocol in protocol.subtask.protocols:
                #protocol.rule.protocols.remove(protocol)
                protocol.subtask.protocols.remove(protocol)

        if protocol in self.owner.protocols:
            self.owner.protocols.remove(protocol)

        if protocol in self.waiting_protocols:
            self.waiting_protocols.remove(protocol)

        if protocol in self.pending_protocols:
            self.pending_protocols.remove(protocol)

         # check if any rules have been met
        currentreqid,estate=0,0
        flag=False
        temp=False
        memo_info = self.memory_manager.get_info_by_memory(memory)
        ##print(memo_info.state)
        ##print('lllllll',self.reservation_id_to_memory_map)


        # currentreqid  is reqid when update is called 

        
        #for ReqId,memlist in self.reservation_id_to_memory_map.items():
            ##print('Res to mem', self.reservation_id_to_memory_map[ReqId],memo_info.index)
            #time_now = self.owner.timeline.now()
            #self.owner.vmemory_list
            #if memo_info.index in memlist:
                #self.owner.vmemory_list(memo_info.index).reservations[]
                #currentreqid1=ReqId
                ##print("resource manager current req id",currentreqid)
                ##print('Resss',memo_info.index, memlist, currentreqid)"""
        ##print("resource manager current req id",currentreqid1)
        for req in self.owner.vmemory_list[memo_info.index].reservations:
            #print("resource manager current req id",self.owner.name,memo_info.index,req.id)  
            time_now = self.owner.timeline.now()
            if req.start_time<= time_now and req.end_time>=time_now:

                currentreqid=req.id 
                #print("check current req id ",currentreqid ,self.owner.name,req.initiator)
                #break

        #print("check current req id ",currentreqid,self.owner.name,req.initiator)

            
        # #print(f'Entanglement genereated for {currentreqid} at memory index {memo_info.index}')
        ##print(self.reservation_to_memory_map[currentreqid])
        ##print('Memory map', self.owner.network_manager)
        ##print(" mem map",self.reservation_id_to_memory_map[currentreqid])
        for mem in self.reservation_id_to_memory_map[currentreqid]:
            # #print('Remote memory state',self.memory_manager.__getitem__(mem).state)
            if self.memory_manager.__getitem__(mem).state == 'ENTANGLED':
                ##print('Entagngle count',len(self.reservation_id_to_memory_map[currentreqid]))
                ##print('Entagngle count',estate)
                estate +=1
                ##print('Entagngle count',estate)
                temp=True
                
                if estate==len(self.reservation_id_to_memory_map[currentreqid]):
                    ##print('ESuccess', estate,len(self.reservation_id_to_memory_map[currentreqid]),currentreqid)
                    flag=True
        if flag:
            # #print('current id',currentreqid,self.owner.timeline.now()*1e-12)
            # self.owner.network_manager.notify(status='APPROVED')
            ##print("approved",self.owner.network_manager.requests)
            for ReqId,ResObj in self.owner.network_manager.requests.items():
                if ReqId == currentreqid:
                    ResObj.status='APPROVED' 
                    #print("ResObj.tp_id",self.owner.network_manager.requests,ResObj.tp_id) 
                    # if ResObj.isvirtual:
                    self.owner.network_manager.notify_nm('APPROVED',ReqId,ResObj)
                    # #print('Res status',ResObj.initiator,ResObj.responder)
            #resobj=self.owner.network_manager.requests['currentreqid']
            ##print('Res status',resobj.initiator)
            #resobj.status='APPROVED'
            ##print('jjjj',self.owner.network_manager.requests.get(currentreqid))
          
            
            #if resobj in self.owner.network_manager.requests[currentreqid]:
             #   resobj.status='APPROVED'
              #  #print('STatsu',resobj.status)
            
        #if state == 'ENTANGLED':
            ##print(f'To entangled called for the memory index {memo_info.index} at the node {self.owner.name}')

        #if memo_info in reservation_to_memory_map:

        else:
                t=0
                for ReqId,ResObj in self.owner.network_manager.requests.items():
                    
                    #if ReqId!= currentreqid:
                        ##print("resource manager reqid ,cuurentid ,node",currentreqid,ReqId,self.owner.name,self.owner.network_manager.requests.items())
                    if ReqId == currentreqid:
                        t=1
                        if temp:
                            ##print("resource manager status pc",ReqId,currentreqid,ResObj.initiator,ResObj.status)
                            ResObj.status='PARTIALCOMPLETE' 
                            ##print("ResObj.tp_id",self.owner.network_manager.requests,ResObj.tp_id) 
                            # if ResObj.isvirtual:
                            self.owner.network_manager.notify_nm('PARTIALCOMPLETE',ReqId,ResObj)
                #if t==0:
                    #print(" resource manager not satisfy")

        """
        # check if any rules have been met
        memo_info = self.memory_manager.get_info_by_memory(memory)
        for rule in self.rule_manager:
            ##print('Called from update method in resource manager ---- rule---- from  node: ', self.owner.name)
            if self.owner.name == 'd' and memo_info.remote_node == 'e':
                ##print('Inside update method with remote node e')
            memories_info = rule.is_valid(memo_info)
            if len(memories_info) > 0:
                rule.do(memories_info)
                
                for info in memories_info:
                    ##print('Update to Occupied')
                    ##print(f'Shifting state to OCCUPIED for memory index inside update :{info.index} for the node: {self.owner.name}')
                    info.to_occupied()
                
                return
        self.owner.get_idle_memory(memo_info)
        """

    def get_memory_manager(self):
        return self.memory_manager

    def send_request(self, protocol: "EntanglementProtocol", req_dst: str,
                     req_condition_func: Callable[[List["EntanglementProtocol"]], "EntanglementProtocol"]):
        """Method to send protocol request to another node.
        Send the request to pair the local 'protocol' with the protocol on the remote node 'req_dst'.
        The function `req_condition_func` describes the desired protocol.
        Args:
            protocol (EntanglementProtocol): protocol sending the request.
            req_dst (str): name of destination node.
            req_condition_func (Callable[[List[EntanglementProtocol]], EntanglementProtocol]): function used to evaluate condition on distant node.
        """

        protocol.own = self.owner
        if req_dst is None:
            self.waiting_protocols.append(protocol)
            return
        if not protocol in self.pending_protocols:
            self.pending_protocols.append(protocol)
        msg = Message(MsgRecieverType.MANAGER, ManagerType.ResourceManager, ResourceManagerMsgType.REQUEST, protocol=protocol,
                                     req_condition_func=req_condition_func)

        """if self.owner.name == 'a' or self.owner.name == 'b':
            #print('Send Protocol Request at node: ', self.owner.name)
            #print('Requested Destination: ', req_dst)
            #print('protocol name: ', protocol.name)
            #print('ResourceManagerMsgType.REQUEST')"""
        msg.id = 2

        ##print("waiting protocols and pending protocols", self.waiting_protocols,self.pending_protocols)
        self.owner.message_handler.send_message(req_dst, msg)

    def received_message(self, src: str, msg: "Message") -> None:
        """Method to receive resoruce manager messages.
        Messages come in 4 types, as detailed in the `ResourceManagerMessage` class.
        Args:
            src (str): name of the node that sent the message.
            msg (ResourceManagerMessage): message received.
        """
        ##print("resource manager receive method",msg.kwargs['protocol'].name,msg.msg_type ,self.owner.name)
        if msg.msg_type is ResourceManagerMsgType.REQUEST:
            #logger.info("Resourcemanager REQUEST received by " + self.owner.name)
            req_condition_func=msg.kwargs.get('req_condition_func')
            protocol = req_condition_func(self.waiting_protocols)
            
            ini_protocol=msg.kwargs['protocol']
            #print('ini_protocol',ini_protocol)
            #print("Resourcemanager request receive",ini_protocol.name,self.owner.name)
            ##print(protocol)
            if protocol is not None:
               
                protocol.set_others(ini_protocol)
                new_msg = Message(MsgRecieverType.MANAGER, ManagerType.ResourceManager, ResourceManagerMsgType.RESPONSE, protocol=ini_protocol,
                                                 is_approved=True, paired_protocol=protocol)
                self.owner.message_handler.send_message(src, new_msg)
                self.waiting_protocols.remove(protocol)
                self.owner.protocols.append(protocol)
                ###print('#######Protocol Start method to be called##########')
                ##print('Protocol Name: Resource manager ',ini_protocol.name,protocol.name,self.owner.name)
                ##print("receive message queue if loop",self.owner.message_handler.manager_queue,self.owner.name )
                protocol.start()
                ##print("receive message queue if loop 2",self.owner.message_handler.manager_queue,self.owner.name )
                self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)
                return
            ##print(" out of loop: ",ini_protocol.name,protocol.name,self.owner.name)
            """##print('######Here we send protocol with approval as false##########')
            ##print('Reply to Protocol Name: ', msg.ini_protocol.name)"""
            new_msg = Message(MsgRecieverType.MANAGER,ManagerType.ResourceManager, ResourceManagerMsgType.RESPONSE, protocol=ini_protocol,
                                             is_approved=False, paired_protocol=None)
            self.owner.message_handler.send_message(src, new_msg)
        elif msg.msg_type is ResourceManagerMsgType.RESPONSE:
            #logger.info("Resource manager RESPONSE message received by " + self.owner.name )
            #print('Resource manager Response')
            ini_protocol=msg.kwargs['protocol']
            is_approved=msg.kwargs['is_approved']
            ##print("is_approved",is_approved,ini_protocol)
            paired_protocol=msg.kwargs['paired_protocol']
            protocol = ini_protocol

            ##print('ini_protocol response',ini_protocol)
            ##print("Resourcemanager response receive",ini_protocol.name,self.owner.name)

            if protocol not in self.pending_protocols:
                if is_approved:
                    self.release_remote_protocol(src, paired_protocol)                  
                self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)
                return

            if is_approved:
                protocol.set_others(paired_protocol)
                if protocol.is_ready():
                    self.pending_protocols.remove(protocol)
                    self.owner.protocols.append(protocol)
                    protocol.own = self.owner
                    ##print('Protocol Name: Resource manager Response ',ini_protocol.name,protocol.name,self.owner.name)
                    ##print("receive message queue elif loop",self.owner.message_handler.manager_queue,self.owner.name )
                    #protocol.start()
                    ##print("receive message queue elif loop 2",self.owner.message_handler.manager_queue,self.owner.name )
                    protocol.start()
            else:
                #print('#######Protocol Not called##########')
                ##print('Protocol Name: ', protocol.name)
                #protocol.rule.protocols.remove(protocol)
                protocol.subtask.protocols.remove(protocol)
                for memory in protocol.memories:
                    # #print('mmmmm')
                    memory.detach(protocol)
                    memory.attach(memory.memory_array)
                    info = self.memory_manager.get_info_by_memory(memory)
                    if info.remote_node is None:
                        self.update(None, memory, "RAW")
                    else:
                        ##print('msg.is_approved: ', msg.is_approved)
                        ##print('memory: Entangled ', memory)
                        self.update(None, memory, "ENTANGLED")
                self.pending_protocols.remove(protocol)
        elif msg.msg_type is ResourceManagerMsgType.RELEASE_PROTOCOL:
            protocol=msg.kwargs['protocol']
            if protocol in self.owner.protocols:
                assert isinstance(protocol, EntanglementProtocol)
                protocol.release()
        elif msg.msg_type is ResourceManagerMsgType.RELEASE_MEMORY:
            #("RELEASE_MEMORY message received by "+ self.owner.name)
            target_id = msg.memory
            for protocol in self.owner.protocols:
                for memory in protocol.memories:
                    if memory.name == target_id:
                        protocol.release()
                        self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)
                        return
        elif msg.msg_type is ResourceManagerMsgType.ABORT:
            # #print('msg res',msg.reservation)
            reservation=msg.kwargs['reservation']
            #print(self.reservation_to_events_map[reservation])
            
            # if an abort message is received, remove all the scheduled events from the queue 
            # containing rules for the preepted reservation 
            for event in self.reservation_to_events_map[reservation]:
                event._is_removed = True
            del self.reservation_to_events_map[reservation]
            
            # update all the memories as RAW after the abort. 
            for memory_index in self.reservation_to_memory_map[reservation]:
                self.update(None, self.memory_manager.memory_array.memories[memory_index], "RAW")
            del self.reservation_to_memory_map[reservation]
            #logger.info("ABORT message received by "+ self.owner.name)

        ##print("resoure man recv queue",self.owner.message_handler.manager_queue,self.owner.name)   
        self.owner.message_handler.process_msg(msg.receiver_type,msg.receiver)
        
        
    def memory_expire(self, memory: "Memory"):
        """Method to receive memory expiration events."""

        self.update(None, memory, "RAW")

    def release_remote_protocol(self, dst: str, protocol: "EntanglementProtocol") -> None:
        """Method to release protocols from memories on distant nodes.
        Release the remote protocol 'protocol' on the remote node 'dst'.
        The local protocol was paired with the remote protocol but local protocol becomes invalid.
        The resource manager needs to notify the remote node to cancel the paired protocol.
        Args:
            dst (str): name of the destination node.
            protocol (EntanglementProtocol): protocol to release on node.
        """

        msg = Message(MsgRecieverType.MANAGER, ManagerType.ResourceManager, ResourceManagerMsgType.RELEASE_PROTOCOL, protocol=protocol)
        self.owner.message_handler.send_message(dst, msg)

    def release_remote_memory(self, init_protocol: "EntanglementProtocol", dst: str, memory_id: str) -> None:
        """Method to release memories on distant nodes.
        Release the remote memory 'memory_id' on the node 'dst'.
        The entanglement protocol of remote memory was paired with the local protocol 'init_protocol', but local
        protocol becomes invalid.
        The resource manager needs to notify the remote node to release the occupied memory.
        Args:
            init_protocol (EntanglementProtocol): protocol holding memory.
            dst (str): name of destination node.
            memory_id (str): name of memory to release.
        """

        msg = Message(MsgRecieverType.MANAGER, ManagerType.ResourceManager, ResourceManagerMsgType.RELEASE_MEMORY, protocol=init_protocol, memory_id=memory_id)
        self.owner.message_handler.send_message(dst, msg)