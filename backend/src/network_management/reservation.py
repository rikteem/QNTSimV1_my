"""Definition of Reservation protocol and related tools.

This module provides a definition for the reservation protocol used by the network manager.
This includes the Reservation, MemoryTimeCard, and QCap classes, which are used by the network manager to track reservations.
Also included is the definition of the message type used by the reservation protocol.
"""

from enum import Enum, auto
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ..topology.node import QuantumRouter
    from ..resource_management.memory_manager import MemoryInfo, MemoryManager

from ..resource_management.rule_manager import Rule
from ..kernel.timeline import Timeline
if Timeline.DLCZ:
    from ..entanglement_management.DLCZ_generation import EntanglementGenerationA
    from ..entanglement_management.DLCZ_purification import BBPSSW
    from ..entanglement_management.DLCZ_swapping import EntanglementSwappingA, EntanglementSwappingB
elif Timeline.bk:
    from ..entanglement_management.bk_generation import EntanglementGenerationA
    from ..entanglement_management.bk_purification import BBPSSW
    from ..entanglement_management.bk_swapping import EntanglementSwappingA, EntanglementSwappingB
from ..message import Message
from ..protocol import StackProtocol
from ..kernel._event import Event
import itertools


class RSVPMsgType(Enum):
    """Defines possible message types for the reservation protocol."""

    REQUEST = auto()
    REJECT = auto()
    APPROVE = auto()
    ABORT = auto()
    SKIP_ROUTING=auto()
    


class ResourceReservationMessage(Message):
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

    def __init__(self, msg_type: any, receiver: str, reservation: "Reservation", **kwargs):
        Message.__init__(self, msg_type, receiver)
        self.reservation = reservation
        self.temp_path=kwargs.get("temp_path")
        self.marker=kwargs.get("marker")
        # #print('temp path',self.temp_path)
        #self.qcaps = []
        if self.msg_type is RSVPMsgType.REQUEST:
            self.qcaps = []
        elif self.msg_type is RSVPMsgType.REJECT:
            pass
        elif self.msg_type is RSVPMsgType.APPROVE:
            # #print('Approve kwrags path',kwargs["path"])
            self.path = kwargs["path"]
        elif self.msg_type is RSVPMsgType.ABORT:
            pass
        # elif self.msg_type is RSVPMsgType.SKIP_ROUTING:
        #     #print('inside11')
        #     # self.path = kwargs["path"]
        else:
            raise Exception("Unknown type of message")

    def __str__(self):
        return "ResourceReservationProtocol: \n\ttype=%s, \n\treservation=%s" % (self.msg_type, self.reservation)


class ResourceReservationProtocol(StackProtocol):
    """ReservationProtocol for  node resources.

    The reservation protocol receives network entanglement requests and attempts to reserve local resources.
    If successful, it will forward the request to another node in the entanglement path and create local rules.
    These rules are passed to the node's resource manager.
    If unsuccessful, the protocol will notify the network manager of failure.

    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        timecards (List[MemoryTimeCard]): list of reservation cards for all memories on node.
        es_succ_prob (float): sets `success_probability` of `EntanglementSwappingA` protocols created by rules.
        es_degredation (float): sets `degredation` of `EntanglementSwappingA` protocols created by rules.
        accepted_reservation (List[Reservation]): list of all approved reservation requests.
    """

    def __init__(self, own: "QuantumRouter", name: str):
        """Constructor for the reservation protocol class.

        Args:
            own (QuantumRouter): node to attach protocol to.
            name (str): label for reservation protocol instance.
        """

        super().__init__(own, name)
        self.timecards = [MemoryTimeCard(i) for i in range(len(own.memory_array))]
        self.es_succ_prob = 1
        self.es_degradation = 0.99
        self.accepted_reservation = []

    def push(self, responder: str, start_time: int, end_time: int, memory_size: int, target_fidelity: float, isvirtual:bool, priority:int):
        """Method to receive reservation requests from higher level protocol.

        Will evaluate request and determine if node can meet it.
        If it can, it will push the request down to a lower protocol.
        Otherwise, it will pop the request back up.

        Args:
            responder (str): node that entanglement is requested with.
            start_time (int): simulation time at which entanglement should start.
            end_time (int): simulation time at which entanglement should cease.
            memory_size (int): number of memories to be entangled.
            target_fidelity (float): desired fidelity of entanglement.

        Side Effects:
            May push/pop to lower/upper attached protocols (or network manager).
        """

        reservation = Reservation(self.own.name, responder, start_time, end_time, memory_size, target_fidelity, isvirtual, priority)
        self.own.network_manager.requests.update({reservation.id:reservation})
        reservation.status='INITIATED'
        # #print('rress',self.own.name,self.own.timeline.now()*1e-12)
        # #print('aa',reservation)
        if self.schedule(reservation):
            msg = ResourceReservationMessage(RSVPMsgType.REQUEST, self.name, reservation)
            qcap = QCap(self.own.name)
            msg.qcaps.append(qcap)
            # #print('--------------------push called ---------------- ', qcap.node,len(msg.qcaps),self.own.name,self.own.timeline.now()*1e-12)
            self._push(dst=responder, msg=msg)
        else:
            # #print('in reject')
            msg = ResourceReservationMessage(RSVPMsgType.REJECT, self.name, reservation)
            self._pop(msg=msg)

    def pop(self, src: str, msg: "ResourceReservationMessage"):
        """Method to receive messages from lower protocols.

        Messages may be of 3 types, causing different network manager behavior:

        1. REQUEST: requests are evaluated, and forwarded along the path if accepted. Otherwise a REJECT message is sent back.
        2. REJECT: any reserved resources are released and the message forwarded back towards the initializer.
        3. APPROVE: rules are created to achieve the approved request. The message is forwarded back towards the initializer.

        Args:
            src (str): source node of the message.
            msg (ResourceReservationMessage): message received.
        
        Side Effects:
            May push/pop to lower/upper attached protocols (or network manager).
        """
        # #print('--------------------pop called ---------------- ', self.own.name,self.own.timeline.now()*1e-12)
        if msg.msg_type == RSVPMsgType.REQUEST:
            assert self.own.timeline.now() < msg.reservation.start_time
            if self.schedule(msg.reservation):
                qcap = QCap(self.own.name)
                # #print('inside pop', msg.reservation.responder )
                msg.qcaps.append(qcap)
                # #print('nnnn', len(msg.qcaps),msg.qcaps)
                if self.own.name == msg.reservation.responder:
                    
                    path = [qcap.node for qcap in msg.qcaps]
                    # #print('apprv',path)
                    rules = self.create_rules(path, reservation=msg.reservation)
                    self.load_rules(rules, msg.reservation)
                    new_msg = ResourceReservationMessage(RSVPMsgType.APPROVE, self.name, msg.reservation, path=path)
                    self._pop(msg=msg)
                    self._push(dst=msg.reservation.initiator, msg=new_msg)
                    # #print('insidepop',msg.reservation.initiator,self.own.name)
                else:
                    # #print('esllssee',msg.reservation.initiator,self.own.name)
                    self._push(dst=msg.reservation.responder, msg=msg)
            else:
                new_msg = ResourceReservationMessage(RSVPMsgType.REJECT, self.name, msg.reservation)
                self._push(dst=msg.reservation.initiator, msg=new_msg)
        elif msg.msg_type == RSVPMsgType.REJECT:
            msg.reservation.status='REJECT'
            # #print('inside reservation reject',self.own.name)
            self.own.network_manager.notify_nm('REJECT',msg.reservation.id,msg.reservation) #Reservation status REJECT
            for card in self.timecards:
                card.remove(msg.reservation)
            if msg.reservation.initiator == self.own.name:
                self._pop(msg=msg)
            else:
                self._push(dst=msg.reservation.initiator, msg=msg)
        elif msg.msg_type == RSVPMsgType.APPROVE:
            rules = self.create_rules(msg.path, msg.reservation)
            self.load_rules(rules, msg.reservation)
            # #print('insd pop',msg.reservation.initiator,self.own.name,msg.path)
            if msg.reservation.initiator == self.own.name:
                # #print('insd pop',msg.reservation.initiator,self.own.name)
                self._pop(msg=msg)
            else:
                self._push(dst=msg.reservation.initiator, msg=msg)
        else:
            raise Exception("Unknown type of message", msg.msg_type)

    def schedule(self, reservation: "Reservation") -> bool:
        """Method to attempt reservation request.

        Args:
            reservation (Reservation): reservation to approve or reject.

        Returns:
            bool: if reservation can be met or not.
        """

        # Check if it is a middle node or end node
        if self.own.name in [reservation.initiator, reservation.responder]:
            counter = reservation.memory_size
        else:
            counter = reservation.memory_size * 2
        cards = []
        
        # #print('###########Adding Reservation#############',self.own.name,self.own.timeline.now()*1e-12)
        # Iterate over every time card to allocate memory
        for card in self.timecards:
            # Check if memory can be allocated to the card or not            
            condition, isCardVirtual = card.add(self.own, reservation)
            if (not isCardVirtual) and condition:
                # if yes, decrease the counter and add the new card to the cards list
                counter -= 1
                cards.append(card)#
                # add reservation to the reservation to memory map
                if reservation.id not in self.own.resource_manager.reservation_id_to_memory_map:
                    self.own.resource_manager.reservation_id_to_memory_map[reservation.id] = []
                self.own.resource_manager.reservation_id_to_memory_map[reservation.id].append(card.memory_index)
                #self.own.resource_manager.reservation_to_memory_map[reservation.id]=card.memory_index
            # if all the reservations are done, move on
            if counter == 0:
                break

        # if all reservations are not done, remove everything from cards and return failure
        if counter > 0:
            # #print('counter >0')
            for card in cards:
                card.remove(reservation)
            return False

        # add reservation to the reservation to memory map
        self.own.resource_manager.reservation_to_memory_map[reservation] = []
        for card in cards:
            self.own.resource_manager.reservation_to_memory_map[reservation].append(card.memory_index)
        return True

    # def set_dependencies():
        #Offset the memory indices used by Virtual links
        # pass
    
    def create_rules(self, path: List[str], reservation: "Reservation") -> List["Rule"]:
        """Method to create rules for a successful request.

        Rules are used to direct the flow of information/entanglement in the resource manager.

        Args:
            path (List[str]): list of node names in entanglement path.
            reservation (Reservation): approved reservation.

        Returns:
            List[Rule]: list of rules created by the method.
        """
        
        rules = []
        # #print('Reservation------', reservation.initiator, reservation.responder)
        self.own.resource_manager.rule_manager.rules = []
        # #print(f'Rules for this node: {self.own.name} are {len(self.own.resource_manager.rule_manager.rules)}')
        memory_indices = []
        virtual_indices = []
        memory_indices_occupied = []
        last_virtual_index = -1
        memories_indices_free=[]

        for card in self.timecards:
            ##print("1")
            ##print('111111', card)
            if reservation in card.reservations:
                memory_indices.append(card.memory_index)
                # #print("To maintain the virtual link indices")
                if card.has_virtual_reservation() and not reservation.isvirtual:
                    virtual_indices.append(card.memory_index)
                    if card.memory_index > last_virtual_index:
                        last_virtual_index= card.memory_index
                # elif card.has_virtual_reservation() and reservation.isvirtual:
                #     #print('Another virtual request arrived')
                
                    
                    
        # #print('last_virtual_index', last_virtual_index)        

        # create rules for entanglement generation
        # #print('Current node in Entanglement generation', self.own.name)
        index = path.index(self.own.name)
        # #print('Path--------', path)
        # #print('Reservation------', reservation.initiator, reservation.responder,reservation.id)
        if index > 0:
            ##print(f"index>0:{index}")
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index - 1] in self.own.neighbors:
                ##print("###",self.own.name)
                #This will run for all nodes barring starting node
                def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                    
                    
                    """if manager.resource_manager.owner.name == 'd' and memory_info.index == 1:
                        ##print('EG for node: ', manager.resource_manager.owner.name)
                        ##print('memory_info.state ', memory_info.state)
                        ##print('memory_info.index: ', memory_info.index)
                        ##print('memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]: ', memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1])
                        ##print('reservation.memory_size', reservation.memory_size)
                    """
                    #memory_list = memory_indices[:reservation.memory_size]
                    #if index < len(path) - 1 and path[index + 1] not in self.own.neighbors:
                    #    memory_list.append(reservation.memory_size)                    

                    memories_indices_free = [x for x in memory_indices if x not in virtual_indices]

                    #if memory_info.state == "RAW" and memory_info.index in memory_indices[:reservation.memory_size]:
                    #begin, end = last_virtual_index + 1 , (last_virtual_index+1) + reservation.memory_size
                    if memory_info.state == "RAW" and memory_info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]:
                        #Check for node B's memory
                        """##print('self.own.name here is : ', self.own.name)
                        if self.own.name == 'd':
                            ##print(f'In rule condition for Entanglement Generation  at node e for d')
                            ##print('memory_info.index: ', memory_info.index)
                            ##print('memory_info.state: ', memory_info.state)
                            ##print('memory_info.remote_node: ', memory_info.remote_node)
                        """
                        return [memory_info]
                    else:
                        return []

                def eg_rule_action(memories_info: List["MemoryInfo"]):
                    # #print('Current node in eg_ruleaction for index>0', self.own.name)
                    memories = [info.memory for info in memories_info]
                    memory = memories[0]
                    mid = self.own.map_to_middle_node[path[index - 1]]
                    # #print('---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index - 1]))
                    ###print('---------Middle node for this----------', mid)
                    protocol = EntanglementGenerationA(None, "EGA." + memory.name, mid, path[index - 1], memory)
                    return [protocol, [None], [None]]
                

                rule = Rule(10, eg_rule_action, eg_rule_condition)
                rules.append(rule)

            #memory_indices_occupied=memory_indices_occupied.append(memories_indices_free)
            #memories_indices_free = [x for x in memory_indices if x not in memory_indices_occupied]
        if index < len(path) - 1:
            ##print(f"index<<{index}")
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index + 1] in self.own.neighbors:
                #Starting node
                # #print("####",self.own.name)
                if index == 0:
                    # #print("index=0")
                    def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                        if memory_info.state == "RAW" and memory_info.index in memory_indices:
                            return [memory_info]
                        else:
                            return []
                #second to second last node
                else:
                    # #print("index!=0")
                    def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                       
                        memories_indices_free = [x for x in memory_indices if x not in memory_indices_occupied]
                        """
                        if self.own.name == 'd':
                                ##print(f'In rule condition for Entanglement Generation  at node d for e')
                                ##print('memory_info.index: ', memory_info.index)
                                ##print('memory_info.state: ', memory_info.state)
                                ##print('memory_info.remote_node: ', memory_info.remote_node)
                                ##print('last_virtual_index, reservation.memory_size: ',last_virtual_index, reservation.memory_size)
                                ##print('acceptable indexes: ', memory_indices[last_virtual_index + reservation.memory_size:])
                        """
                        # #print(f'free memory indices of {self.own.name}', memories_indices_free)
                        #if memory_info.state == "RAW" and memory_info.index in memory_indices[reservation.memory_size:]:
                        if memory_info.state == "RAW" and memory_info.index in memory_indices[(last_virtual_index+1) + reservation.memory_size:]:
                            #Check for node B's memory
                            ##print('self.own.name here is : ', self.own.name)
                            """
                            ##print(f'In rule condition for Entanglement Generation  at node {self.own.name}')
                            ##print('memory_info.index: ', memory_info.index)
                            ##print('memory_info.state: ', memory_info.state)
                            ##print('memory_info.remote_node: ', memory_info.remote_node)
                            """
                            
                            return [memory_info]
                        else:
                            return []

                def eg_rule_action(memories_info: List["MemoryInfo"]):
                    def req_func(protocols):
                        for protocol in protocols:
                            if isinstance(protocol,
                                          EntanglementGenerationA) and protocol.other == self.own.name and protocol.rule.get_reservation() == reservation:
                                return protocol
                    
                    # #print('Current node in eg_ruleaction for indexnot > 0', self.own.name)
                    memories = [info.memory for info in memories_info]
                    memory = memories[0]
                    #memory = memories[-1]
                    mid = self.own.map_to_middle_node[path[index + 1]]
                    # #print('1---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index + 1]))
                    ###print('---------Middle node for this---------- ', mid)
                    protocol = EntanglementGenerationA(None, "EGA." + memory.name, mid, path[index + 1], memory)
                    return [protocol, [path[index + 1]], [req_func]]
                ###print('---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index + 1]))
                rule = Rule(10, eg_rule_action, eg_rule_condition)
                rules.append(rule)
        # #print('last_virtual_index', last_virtual_index)
        ###print(f'For {self.own.name}: --- len(rules): {len(rules)}')


        # create rules for entanglement purification
        if index > 0:
            # #print("adding rules for purification")
            def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                #if (memory_info.index in memory_indices[:reservation.memory_size]

                if (memory_info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]):
                    # #print("purification index satisified")
                    if memory_info.state == "ENTANGLED":
                        # #print("memory info state satisfied")
                        # #print("memory fidelity is", memory_info.fidelity, "reservation fidelity:", reservation.fidelity)
                        if memory_info.fidelity < reservation.fidelity:
                            # #print("fidelity satisfied")
                    # #print("memories found")
                            for info in manager:
                                #if (info != memory_info and info.index in memory_indices[:reservation.memory_size]
                                if (info != memory_info and info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]
                                        and info.state == "ENTANGLED" and info.remote_node == memory_info.remote_node
                                        and info.fidelity == memory_info.fidelity):
                                    assert memory_info.remote_memo != info.remote_memo
                                    return [memory_info, info]
                # else:
                #     #print("no memories found")
                return []

            def ep_rule_action(memories_info: List["MemoryInfo"]):
                memories = [info.memory for info in memories_info]

                def req_func(protocols):
                    _protocols = []
                    for protocol in protocols:
                        if not isinstance(protocol, BBPSSW):
                            continue

                        if protocol.kept_memo.name == memories_info[0].remote_memo:
                            _protocols.insert(0, protocol)
                        if protocol.kept_memo.name == memories_info[1].remote_memo:
                            _protocols.insert(1, protocol)

                    if len(_protocols) != 2:
                        return None

                    protocols.remove(_protocols[1])
                    _protocols[1].rule.protocols.remove(_protocols[1])
                    _protocols[1].kept_memo.detach(_protocols[1])
                    _protocols[0].meas_memo = _protocols[1].kept_memo
                    _protocols[0].memories = [_protocols[0].kept_memo, _protocols[0].meas_memo]
                    _protocols[0].name = _protocols[0].name + "." + _protocols[0].meas_memo.name
                    _protocols[0].meas_memo.attach(_protocols[0])
                    _protocols[0].t0 = _protocols[0].kept_memo.timeline.now()

                    return _protocols[0]

                name = "EP.%s.%s" % (memories[0].name, memories[1].name)
                protocol = BBPSSW(None, name, memories[0], memories[1])
                dsts = [memories_info[0].remote_node]
                req_funcs = [req_func]
                return protocol, dsts, req_funcs

            rule = Rule(10, ep_rule_action, ep_rule_condition)
            rules.append(rule)

        if index < len(path) - 1:
            if index == 0:
                def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                    if (memory_info.index in memory_indices
                            and memory_info.state == "ENTANGLED" and memory_info.fidelity < reservation.fidelity):
                        return [memory_info]
                    return []
            else:
                def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                    if (memory_info.index in memory_indices[reservation.memory_size:]
                    #if (memory_info.index in memory_indices[last_virtual_index + reservation.memory_size:]
                            and memory_info.state == "ENTANGLED" and memory_info.fidelity < reservation.fidelity):
                        return [memory_info]
                    return []

            def ep_rule_action(memories_info: List["MemoryInfo"]):
                memories = [info.memory for info in memories_info]
                name = "EP.%s" % (memories[0].name)
                protocol = BBPSSW(None, name, memories[0], None)
                return protocol, [None], [None]

            rule = Rule(10, ep_rule_action, ep_rule_condition)
            rules.append(rule)

        
        ###print(f'For {self.own.name}: --- len(rules): {len(rules)}')


        # create rules for entanglement swapping
        def es_rule_actionB(memories_info: List["MemoryInfo"]):
            memories = [info.memory for info in memories_info]
            memory = memories[0]
            protocol = EntanglementSwappingB(None, "ESB." + memory.name, memory)
            return [protocol, [None], [None]]

        # #print('Current node in Swapping', self.own.name)
        if index == 0:
            def es_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                #if self.own.name == 'h' and memory_info.state == "ENTANGLED":
                    ##print('memory_info.index', memory_info.index)
                    ##print('memory_info.remote_node', memory_info.remote_node)
                    ##print('path[-1]', path[-1])
                    ##print('path', path)

                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node != path[-1]
                        #and memory_info.remote_node == path[index+1]
                        and memory_info.fidelity >= reservation.fidelity):
                    
                    return [memory_info]
                else:
                    return []

            rule = Rule(10, es_rule_actionB, es_rule_condition)
            rules.append(rule)

        elif index == len(path) - 1:
            def es_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                #if self.own.name == 'h' and memory_info.state == "ENTANGLED":
                    ##print('memory_info.index', memory_info.index)
                    ##print('memory_info.remote_node', memory_info.remote_node)
                    ##print('path[0]', path[0])
                    ##print('path', path)

                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node != path[0]
                        #and memory_info.remote_node == path[index-1]
                        and memory_info.fidelity >= reservation.fidelity):
                    return [memory_info]
                else:
                    return []

            rule = Rule(10, es_rule_actionB, es_rule_condition)
            rules.append(rule)

        else:
            _path = path[:]
            ###print('In middle node for entanglement swapping: ', self.own.name)
            while _path.index(self.own.name) % 2 == 0:
                ###print('Inside new path loop for : ', self.own.name)
                ###print("Path inside reservation---------",_path)
                ###print('_path.index(self.own.name): ' , _path.index(self.own.name))
                new_path = []
                for i, n in enumerate(_path):
                    if i % 2 == 0 or i == len(_path) - 1:
                        new_path.append(n)
                ###print('new_path: ', new_path)
                _path = new_path
            _index = _path.index(self.own.name)
            ###print('new path: ', _path)
            ###print('value of _index at mid swap node: ', _index)
            left, right = _path[_index - 1], _path[_index + 1]
            ###print('(left, right)', (left, right))

            def es_rule_conditionA(memory_info: "MemoryInfo", manager: "MemoryManager"):
                ###print("Node---",)
                ###print("STATE",memory_info.state)
                ###print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
                #for info in [memory_info]:
                #    ##print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                #                         str(info.fidelity), str(info.entangle_time * 1e-12)))
                ###print("INDEX,REMOTE NODE,FIDELITY, RESERVATION FIDELITY ",memory_info.index,memory_info.remote_node,memory_info.fidelity,reservation.fidelity)
                                
                ##print('enter ESA condition check')
                # #print('Current node in Rule conditionA', self.own.name)
                # #print('memory_info.remote_node : ', memory_info.remote_node)
                # #print('memory_info.state : ', memory_info.state)
                # if memory_info.remote_node == 'v2':
                #     #print('condition values for v2------')
                #     #print('memory_info.state == "ENTANGLED" ', memory_info.state == "ENTANGLED")
                #     #print('memory_info.index in memory_indices ', memory_info.index in memory_indices)
                #     #print('memory_info.remote_node == left ', memory_info.remote_node == left)
                #     #print('memory_info.fidelity >= reservation.fidelity ', memory_info.fidelity >= reservation.fidelity)
                #     #print('Ends------')

                # if memory_info.remote_node == 'v1':
                #     #print('condition values for v1------')
                #     #print('memory_info.state == "ENTANGLED" ', memory_info.state == "ENTANGLED")
                #     #print('memory_info.index in memory_indices ', memory_info.index in memory_indices)
                #     #print('memory_info.remote_node == right ', memory_info.remote_node == right)
                #     #print('memory_info.fidelity >= reservation.fidelity ', memory_info.fidelity >= reservation.fidelity)
                #     #print('Ends------')
                
                # #print('Remote node : ', memory_info.remote_node)
                #if ((memory_info.state == "ENTANGLED" or memory_info.state == "OCCUPIED")
                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node == left
                        and memory_info.fidelity >= reservation.fidelity):
                    # #print('gets in left if')
                    for info in manager:
                        """##print('info.remote_node: ', info.remote_node)
                        if info.remote_node == 'e':
                            ##print('condition values for E------')
                            ##print('info.state == "ENTANGLED" ', info.state == "ENTANGLED")
                            ##print()
                            ##print()
                            ##print('info.index: ', info.index)
                            ##print('memory_indices: ', memory_indices)
                            ##print('info.index in memory_indices ', info.index in memory_indices)
                            ##print('info.remote_node == right ', info.remote_node == right)
                            ##print('info.fidelity >= reservation.fidelity ', info.fidelity >= reservation.fidelity)
                            ##print('info.fidelity: ', info.fidelity)
                            ##print('reservation.fidelity: ', reservation.fidelity)
                            ##print()
                            ##print()
                            ##print('Ends------')
                        """
                        #if ((info.state == "ENTANGLED" or info.state == "OCCUPIED")
                        if (info.state == "ENTANGLED"
                                and info.index in memory_indices
                                and info.remote_node == right
                                and info.fidelity >= reservation.fidelity):
                            ###print("ES Condition matched A in IF----",self.own.name)
                            ###print("(PAIR OF NODES)",(left,right))
                            # #print('gets in left of right')
                            return [memory_info, info]
                    
                #elif ((memory_info.state == "ENTANGLED" or memory_info.state == "OCCUPIED")
                if (memory_info.state == "ENTANGLED"
                      and memory_info.index in memory_indices
                      and memory_info.remote_node == right
                      and memory_info.fidelity >= reservation.fidelity):
                    # #print('gets in right if')
                    for info in manager:
                        """if info.remote_node == 'a' and memory_info.remote_node == 'e':
                            ##print('info.state == "ENTANGLED" ' , info.state == "ENTANGLED")
                            ##print('info.index in memory_indices ', info.index in memory_indices)
                            ##print('info.remote_node == left ', info.remote_node == left)
                            ##print('info.fidelity >= reservation.fidelity ', info.fidelity >= reservation.fidelity)
                        """
                        #if ((info.state == "ENTANGLED" or info.state == "OCCUPIED")
                        if (info.state == "ENTANGLED"
                                and info.index in memory_indices
                                and info.remote_node == left
                                and info.fidelity >= reservation.fidelity):
                            """##print('memory_info.remote_node : ', memory_info.remote_node)
                            ##print('info.remote_node : ', info.remote_node)
                            ##print("ES Condition matched A in ELIF----",self.own.name)
                            ##print("(PAIR OF NODES)",(left,right))
                            """
                            # #print('gets in right of left')
                            return [memory_info, info]
                """else:
                    for info in manager:
                        ##print("This else")
                        return [memory_info, info]"""
                # #print("ES Condition in A failed----",self.own.name)
                # #print("(PAIR OF NODES)",(left,right))
                return []

            def es_rule_actionA(memories_info: List["MemoryInfo"]):
                memories = [info.memory for info in memories_info]

                def req_func1(protocols):
                    for protocol in protocols:
                        if (isinstance(protocol, EntanglementSwappingB)
                                and protocol.memory.name == memories_info[0].remote_memo):
                            return protocol

                def req_func2(protocols):
                    for protocol in protocols:
                        if (isinstance(protocol, EntanglementSwappingB)
                                and protocol.memory.name == memories_info[1].remote_memo):
                            return protocol

                protocol = EntanglementSwappingA(None, "ESA.%s.%s" % (memories[0].name, memories[1].name),
                                                 memories[0], memories[1],
                                                 success_prob=.99, degradation=.99)
                dsts = [info.remote_node for info in memories_info]
                req_funcs = [req_func1, req_func2]
                return protocol, dsts, req_funcs
            ###print("Node---",self.own.name)
            ###print("Index A:\tEntangled Node A:\tFidelity A:\tEntanglement Time A:")
            #for info in self.own.resource_manager.memory_manager:
            #    ##print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
            #                             str(info.fidelity), str(info.entangle_time * 1e-12)))
            rule = Rule(10, es_rule_actionA, es_rule_conditionA)
            rules.append(rule)

            def es_rule_conditionB(memory_info: "MemoryInfo", manager: "MemoryManager") -> List["MemoryInfo"]:
                ###print("Node---", self.own.name)
                ###print("In RULE B")
                ###print("STATE",memory_info.state)

                

                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node not in [left, right]
                        and memory_info.fidelity >= reservation.fidelity):
                    ###print("Node---",self.own.name)
                    ###print("Index B:\tEntangled Node:\tFidelity:\tEntanglement Time:")
                    #for info in self.own.resource_manager.memory_manager:
                    #    ##print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                    #                                str(info.fidelity), str(info.entangle_time * 1e-12)))
                    return [memory_info]

                else:
                    return []
            
            rule = Rule(10, es_rule_actionB, es_rule_conditionB)
            rules.append(rule)

        for rule in rules:
            rule.set_reservation(reservation)

        ###print(f'For {self.own.name}: --- len(rules): {len(rules)}')

        return rules

    def load_rules(self, rules: List["Rule"], reservation: "Request") -> None:
        """Method to add created rules to resource manager.

        This method will schedule the resource manager to load all rules at the reservation start time.
        The rules will be set to expire at the reservation end time.

        Args:
            rules (List[Rules]): rules to add.
            reservation (Reservation): reservation that created the rules.
        """
        # cache events that are being scheduled to access them later if the reservations need to be aborted
        scheduled_events = []
        self.accepted_reservation.append(reservation)
        for card in self.vmemorylist:

            # initialise all memories in the reservations by first setting their state to raw and setting their expiry time
            if reservation in card.reservations:
                #if self.own.name == 'b' and card.memory_index == 0:
                #    #print ('Memory 0 in b is in this reservation')
                #process = Process(self.own.resource_manager, "update",
                                 # [None, self.own.memory_array[card.memory_index], "RAW"])
                #event = Event(reservation.end_time, process, 1)
                event = Event(reservation.end_time,self.own.resource_manager, "update",[None, self.own.memory_array[card.memory_index], "RAW"],1)
                scheduled_events.append(event)
                #self.own.timeline.schedule(event)
                self.own.timeline.schedule_counter += 1
                self.own.timeline.events.push(event)


        # for all the rules corresponding to these memories (generation, purification or swapping), create processes
        # for each rule, a load and an expire event is scheduled. 
        for rule in rules:
            #process = Process(self.own.resource_manager, "load", [rule])
            #event = Event(reservation.start_time, process)
            event = Event(reservation.start_time,self.own.resource_manager, "load", [rule] )
            #self.own.timeline.schedule(event)
            self.own.timeline.schedule_counter += 1
            self.own.timeline.events.push(event)
            scheduled_events.append(event)
            #process = Process(self.own.resource_manager, "expire", [rule])
            #event = Event(reservation.end_time, process, 0)
            event = Event(reservation.end_time,self.own.resource_manager, "expire", [rule],0)
            scheduled_events.append(event)
            #self.own.timeline.schedule(event)
            self.own.timeline.schedule_counter += 1
            self.own.timeline.events.push(event)

        # Map the new events to a map with the corresponding reservation stored in the resource manager 
        self.own.resource_manager.reservation_to_events_map[reservation] = scheduled_events

    def received_message(self, src, msg):
        """Method to receive messages directly (should not be used; receive through network manager)."""

        raise Exception("RSVP protocol should not call this function")

    def set_swapping_success_rate(self, prob: float) -> None:
        assert 0 <= prob <= 1
        self.es_succ_prob = prob

    def set_swapping_degradation(self, degradation: float) -> None:
        assert 0 <= degradation <= 1
        self.es_degradation = degradation


class Reservation():
    """Tracking of reservation parameters for the network manager.

    Attributes:
        initiator (str): name of the node that created the reservation request.
        responder (str): name of distant node with witch entanglement is requested.
        start_time (int): simulation time at which entanglement should be attempted.
        end_time (int): simulation time at which resources may be released.
        memory_size (int): number of entangled memory pairs requested.
    """
    newid=itertools.count()
    allreservations=[]
    def __init__(self, initiator: str, responder: str, start_time: int, end_time: int, memory_size: int,
                 fidelity: float, isvirtual:bool, priority: int):#$$
        """Constructor for the reservation class.

        Args:
            initiator (str): node initiating the request.
            responder (str): node with which entanglement is requested.
            start_time (int): simulation start time of entanglement.
            end_time (int): simulation end time of entanglement.
            memory_size (int): number of entangled memories requested.
            fidelity (float): desired fidelity of entanglement.
        """
        
        self.initiator = initiator
        self.responder = responder
        self.start_time = start_time
        self.end_time = end_time
        self.memory_size = memory_size
        self.fidelity = fidelity
        self.isvirtual=isvirtual#$$
        self.id=next(self.newid)
        self.status=None
        self.priority = priority
        assert self.start_time < self.end_time
        assert self.memory_size > 0
        # #print('@@@',self.id)
    def __str__(self):
        return "Reservation: initiator=%s, responder=%s, start_time=%d, end_time=%d, memory_size=%d, target_fidelity=%.2f, isvirtual=%d" % (
            self.initiator, self.responder, self.start_time, self.end_time, self.memory_size, self.fidelity, self.isvirtual)#$$Not sure if need to add in return stmt


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
        for res in self.reservations:
            if res.isvirtual:
                return True
        return False

    def add(self, owner, reservation: "Reservation") -> bool:
        """Method to add reservation.

        Will use `schedule_reservation` method to determine index to insert reservation.

        Args:
            reservation (Reservation): reservation to add.

        Returns:
            bool: whether or not reservation was inserted successfully.
        """
        
        pos, isCardVirtual = self.schedule_reservation(owner, reservation)
        if pos >= 0:
            self.reservations.insert(pos, reservation)
            return True, isCardVirtual
        else:
            return False, isCardVirtual
        
    def remove(self, reservation: "Reservation") -> bool:
        """Method to remove a reservation.

        Args:
            reservation (Reservation): reservation to remove.

        Returns:
            bool: if reservation was already on the memory or not.
        """

        try:
            pos = self.reservations.index(reservation)
            self.reservations.pop(pos)
            return True
        except ValueError:
            return False

    def schedule_reservation(self, owner, resv: "Reservation") -> int:
        """Method to add reservation to a memory.

        Will return index at which reservation can be inserted into memory reservation list.
        If no space found for reservation, will raise an exception.

        

        Args:
            resv (Reservation): reservation to schedule.

        Returns:
            int: index to insert reservation in reservation list.

        Raises:
            Exception: no valid index to insert reservation.
        """
        flag = False
        isCardVirtual = False
        physical_reservations=[]
        for res in self.reservations:
            if res.isvirtual:#$ or self.reservation.isvirtual
                isCardVirtual = True
                pass
            else:
                physical_reservations.append(res)
        
        if isCardVirtual and resv.isvirtual:
            return -1, isCardVirtual
        
        # Look for an empty posuition to put the new reservation using binary search
        start, end = 0, len(physical_reservations) - 1
        while start <= end:
            mid = (start + end) // 2
            if physical_reservations[mid].start_time > resv.end_time:
                end = mid - 1
            elif physical_reservations[mid].end_time < resv.start_time:
                start = mid + 1
            elif max(physical_reservations[mid].start_time, resv.start_time) <= min(physical_reservations[mid].end_time,
                                                                                resv.end_time):
                # Sucesfully found a position to place the reservation
                flag = True
                break
            else:
                raise Exception("Unexpected status")
        if not flag:
            return start, isCardVirtual

        # Preemptive search because provious search failed to produce a result
        i = 0
        preempted = []
        out_index=0

        # Looking for a big enough slot with only low priority reservations partially or fully occupying the slot 
        for i in range(len(self.reservations)):
            # case where the low priority reservation is fully inside the new reservation
            if self.reservations[i].start_time <= resv.start_time and self.reservations[i].end_time >= resv.start_time:
                if self.reservations[i].priority > resv.priority and owner.timeline.now() < self.reservations[i].start_time:
                    # preempt any low priority reservatio in the required time slot of the new reservation
                    preempted.append(self.reservations[i])
                    continue
                else:
                    # if a higher priority request exists here, return failure since it cannot be preempted
                    return -1, isCardVirtual
#MemoryTimeCard
            # case where the low priority reservation only partially occupies the required time slot.
            if self.reservations[i].end_time >= resv.start_time and self.reservations[i].end_time <= resv.end_time:
                if self.reservations[i].priority > resv.priority and owner.timeline.now() < self.reservations[i].start_time:
                    preempted.append(self.reservations[i])
                    continue
                else:
                    return -1, isCardVirtual
        
        # Reaching here implies that a slot where only low priority reservations occupy the required slot is found
        # #print('inside prempt',preempted)
        for i in preempted:
            # find the index of the new reservation
            if i == preempted[0]:
                out_index = self.reservations.index(i)
            
            # send the initialtors of reservations of all the preempted reservations messages notifying the preemption  
            msg = ResourceReservationMessage(RSVPMsgType.ABORT, "network_manager", i)
            if i.initiator == owner.name:
                owner.network_manager.received_message(i.initiator, msg)
            else:
                owner.send_message(i.initiator, msg)
            self.reservations.remove(i)
        return out_index, isCardVirtual

        # Previous code below for your reference
        """
        start, end = 0, len(self.reservations) - 1
        while start <= end:
            mid = (start + end) // 2
            if self.reservations[mid].start_time > resv.end_time:
                end = mid - 1
            elif self.reservations[mid].end_time < resv.start_time:
                start = mid + 1
            elif max(self.reservations[mid].start_time, resv.start_time) <= min(self.reservations[mid].end_time,
                                                                                resv.end_time):
                return -1
            else:
                raise Exception("Unexpected status")
        return start
        """


class QCap():
    """Class to collect local information for the reservation protocol

    Attributes:
        node (str): name of current node.
    """

    def __init__(self, node: str):
        self.node = node
