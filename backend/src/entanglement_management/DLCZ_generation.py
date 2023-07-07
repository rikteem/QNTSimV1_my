"""Code for Barrett-Kok entanglement Generation protocol
This module defines code to support entanglement generation between single-atom memories on distant nodes.
Also defined is the message type used by this implementation.
Entanglement generation is asymmetric:
* EntanglementGenerationA should be used on the QuantumRouter (with one node set as the primary) and should be started via the "start" method
* EntanglementGeneraitonB should be used on the BSMNode and does not need to be started
"""

from enum import Enum, auto
from math import sqrt
from typing import List, TYPE_CHECKING, Dict, Any
from aenum import Enum
if TYPE_CHECKING:
    from ..components.DLCZ_memory import Memory
    from ..topology.node import Node
    from ..components.DLCZ_bsm import SingleAtomBSM

from .entanglement_protocol import EntanglementProtocol
from ..message import Message
from ..kernel._event import Event
from ..components.circuit import BaseCircuit
from ..utils import log
from ..topology.message_queue_handler import ManagerType, ProtocolType,MsgRecieverType


class GenerationMsgType(Enum):
    """Defines possible message types for entanglement generation."""

    NEGOTIATE = auto()
    NEGOTIATE_ACK = auto()
    MEAS_RES = auto()
    FAILURE = auto()
    RELEASE_BSM = auto()
    REQUEST_BSM = auto()
    BSM_ALLOCATE = auto()
    ENTANGLEMENT_SUCCESS = auto()


class Message():
    """Message used by entanglement generation protocols.
    This message contains all information passed between generation protocol instances.
    Messages of different types contain different information.
    Attributes:
        msg_type (GenerationMsgType): defines the message type.
        receiver (str): name of destination protocol instance.
        qc_delay (int): quantum channel delay to BSM node (if `msg_type == NEGOTIATE`).
        frequency (float): frequency with which local memory can be excited (if `msg_type == NEGOTIATE`).
        emit_time (int): time to emit photon for measurement (if `msg_type == NEGOTIATE_ACK`).
        res (int): detector number at BSM node (if `msg_type == MEAS_RES`).
        time (int): detection time at BSM node (if `msg_type == MEAS_RES`).
        resolution (int): time resolution of BSM detectors (if `msg_type == MEAS_RES`).
    """


    def __init__(self, receiver_type: Enum, receiver: Enum, msg_type, **kwargs) -> None:
        self.id = None
        self.receiver_type = receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs

        #self.protocol_type = EntanglementGenerationA
        """
        if msg_type is GenerationMsgType.NEGOTIATE:
            self.qc_delay = kwargs.get("qc_delay")
            self.frequency = kwargs.get("frequency")
        elif msg_type is GenerationMsgType.NEGOTIATE_ACK:
            self.emit_time_0 = kwargs.get("emit_time_0")
            self.emit_time_1 = kwargs.get("emit_time_1")
        elif msg_type is GenerationMsgType.FAILURE:
            self.time = kwargs.get("time")
        elif msg_type is GenerationMsgType.MEAS_RES:
            self.protocol = kwargs.get("protocol")
            self.res = kwargs.get("res")
            self.time = kwargs.get("time")
            self.accepted_index = kwargs.get("accepted_index")
        elif msg_type is GenerationMsgType.RELEASE_BSM:
            self.protocol = kwargs.get("protocol")
        elif msg_type is GenerationMsgType.REQUEST_BSM:
            self.protocol = kwargs.get("protocol")
        elif msg_type is GenerationMsgType.BSM_ALLOCATE:
            self.protocol = kwargs.get("protocol")
        elif msg_type is GenerationMsgType.ENTANGLEMENT_SUCCESS:
            self.accepted_index = kwargs.get("accepted_index")
        else:
            raise Exception("EntanglementGeneration generated invalid message type {}".format(msg_type)) """



class EntanglementGenerationA(EntanglementProtocol):
    """Entanglement generation protocol for quantum router.
    The EntanglementGenerationA protocol should be instantiated on a quantum router node.
    Instances will communicate with each other (and with the B instance on a BSM node) to generate entanglement.
    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        middle (str): name of BSM measurement node where emitted photons should be directed.
        other (str): name of distant QuantumRouter node, containing a memory to be entangled with local memory.
        memory (Memory): quantum memory object to attempt entanglement for.
    """
    
    # TODO: use a function to update resource manager

    #_plus_state = [sqrt(1/2), sqrt(1/2)]
    #_flip_circuit = Circuit(1)
    #_flip_circuit.x(0)
    #_z_circuit = Circuit(1)
    #_z_circuit.z(0)


    def __init__(self, own: "Node", name: str, middle: str, other: str, memory: "Memory"):
        """Constructor for entanglement generation A class.
        Args:
            own (Node): node to attach protocol to.
            name (str): name of protocol instance.
            middle (str): name of middle measurement node.
            other (str): name of other node.
            memory (Memory): memory to entangle.
        """

        super().__init__(own, name)
        self.middle = middle
        self.other = other  # other node
        self.other_protocol = None  # other EG protocol on other node

        # memory info
        self.memory = memory

        self.memories = [memory]
        self.remote_memo_id = ""  # memory index used by corresponding protocol on other node

        # network and hardware info
        self.fidelity = memory.raw_fidelity
        self.qc_delay = 0
        self.expected_times = -1

        self.scheduled_events = []

        # misc
        self.primary = False  # one end node is the "primary" that initiates negotiation
        self.debug = False

        self.frequency = 2e3
        self.isSuccess = False

        self.state = 0
        Circuit =BaseCircuit.create(self.memory.timeline.type)
        # #print("gen circuit",BaseCircuit.create(self.memory.timeline.type))
        self._plus_state = [sqrt(1/2), sqrt(1/2)]
        self._flip_circuit = Circuit(1)
        self._flip_circuit.x(0)
        self._z_circuit = Circuit(1)
        self._z_circuit.z(0)

    def received_message(self):
        pass

    def set_others(self, other: "EntanglementGenerationA") -> None:
        """Method to set other entanglement protocol instance.
        Args:
            other (EntanglementGenerationA): other protocol instance.
        """

        assert self.other_protocol is None
        assert self.fidelity == other.fidelity
        if other.other_protocol is not None:
            assert self == other.other_protocol
        self.other_protocol = other
        self.remote_memo_id = other.memories[0].name
        self.primary = self.own.name > self.other
        # print("primray is set")
        # print('other protocol name: ', self.other_protocol.name)

    def start(self) -> None:
        """Method to start entanglement generation protocol.
        Will start negotiations with other protocol (if primary).
        Side Effects:
            Will send message through attached node.
        """
        
        log.logger.info(self.own.name + " protocol start with partner {}".format(self.other))
        #print(" GENERATION START generatin between ", self.name, self.other_protocol.name)
        if self not in self.own.protocols:
            return
        
        # If the node is primary, start the entanglement by sending 1st request bsm message
        if self.primary:
            self.received_message = self.primary_received_message
            #print("request sent",self.middle,self.own.name, type(self))
            ###message change
            receiver=self.middle+"_eg"
            #message = Message(MsgRecieverType.PROTOCOL, self.name, GenerationMsgType.REQUEST_BSM, protocol = self)
            message = Message(MsgRecieverType.PROTOCOL, receiver, GenerationMsgType.REQUEST_BSM, protocol = self)
            self.own.message_handler.send_message(self.middle, message)
        else:

            self.received_message = self.secondary_received_message



    def emit_event(self) -> None:
        """Method to setup memory and emit photons.
        If the protocol is in round 1, the memory will be first set to the \|+> state.
        Otherwise, it will apply an x_gate to the memory.
        Regardless of the round, the memory `excite` method will be invoked.
        Side Effects:
            May change state of attached memory.
            May cause attached memory to emit photon.
        """
        #print("!!!!!!!!!!!!!!!! emit event", self.own.name)

        # Assign light sources
        self.own.lightsource.assign_middle(self.middle)
        self.own.lightsource.assign_memory(self.memory)

        # emit photons from lightsources
        # #print("memory index is", self.memory.memory_array.memories.index(self.memory))
        self.own.lightsource.emit()

    def schedule_and_emit_event(self,  min_time) -> None:
        """Method to setup memory and emit photons.
        If the protocol is in round 1, the memory will be first set to the \|+> state.
        Otherwise, it will apply an x_gate to the memory.
        Regardless of the round, the memory `excite` method will be invoked.
        Side Effects:
            May change state of attached memory.
            May cause attached memory to emit photon.
        """
        # #print("!!!!!!!!!!!!!!!! emit event", self.own.name)

        # Assign light sources
        self.own.lightsource.assign_middle(self.middle)
        self.own.lightsource.assign_memory(self.memory)

        # schedule a qubit 
        # #print("memory index is", self.memory.memory_array.memories.index(self.memory))
        previous_time = self.own.schedule_qubit(self.middle, min_time)
        
        # emit the photon
        status = self.own.lightsource.emit()
        # #print("emit status node:", self.own.name, "mamory:", self.memory.memory_array.memories.index(self.memory), "status:", status)

    def release_bsm(self):
        # Send release bsm message to the BSM
        ##message change
        receiver=self.middle+"_eg"
        #message = Message(MsgRecieverType.PROTOCOL, self.name, GenerationMsgType.RELEASE_BSM, protocol = self)
        message = Message(MsgRecieverType.PROTOCOL, receiver, GenerationMsgType.RELEASE_BSM, protocol = self)
        self.own.message_handler.send_message(self.middle, message)

    def primary_received_message(self, src: str, msg: Message) -> None: ##message
        """Method to receive messages.
        This method receives messages from other entanglement generation protocols.
        Depending on the message, different actions may be taken by the protocol.
        Args:
            src (str): name of the source node sending the message.
            msg (Message): message received.
        Side Effects:
            May schedule various internal and hardware events.
        """

        if src not in [self.middle, self.other]:
            return

        msg_type = msg.msg_type
        #print('Enta gen msg_type, state  ',msg_type,self.state ,self.name)
        # If BSM has been allocated by the BSM
        #print("bug check",msg_type is GenerationMsgType.MEAS_RES,self.state)
        if self.state == 3:

            return
        
        #print("bug check",msg_type is GenerationMsgType.MEAS_RES,self.state)
        if self.state==0 and msg_type is GenerationMsgType.BSM_ALLOCATE:
            self.qc_delay = self.own.qchannels[self.middle].delay
            frequency = self.memory.frequency
            ###message
            message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.NEGOTIATE, other_protocol=self.other_protocol.name,
                                                    qc_delay=self.qc_delay, frequency=frequency,protocol=self)
            self.own.message_handler.send_message(self.other, message)
            #print("BSM ALLOCATED, STARTING PROTOCOL -owner , other , state ,memindex",  self.own.name, self.other, self.state,self.memory ,self.name )

            
        
        elif self.state==1 and msg_type is GenerationMsgType.NEGOTIATE_ACK:

            # configure params
            
            #print('Negociate AcK start -owner , other,state,memindex',self.own.name, self.other,self.state,self.memory,self.name)
            emit_time_0=msg.kwargs['emit_time_0']
            self.expected_times = emit_time_0 + self.qc_delay

            if emit_time_0 < self.own.timeline.now():
                emit_time_0 = self.own.timeline.now()

            # schedule emit
            previous_time = self.own.schedule_qubit(self.middle, emit_time_0)
            assert previous_time == emit_time_0, "%d %d %d" % (emit_time_0, emit_time_0, self.own.timeline.now())

            # process = Process(self, "emit_event", [])
            event = Event(emit_time_0, self, "emit_event", [])
            # self.own.timeline.schedule(event)
            ####bug
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # In a batch, schedule all qubits for forming entanglement
            for i in range(400):
                next_time = previous_time + int(1e12 / self.frequency)
                # #print("time of ", i, "th emission at", self.own.name,"is :", next_time)
                # process = Process(self, "schedule_and_emit_event", [next_time])
                event = Event(next_time, self, "schedule_and_emit_event", [next_time])
                # self.own.timeline.schedule(event)
                self.own.timeline.events.push(event)
                self.scheduled_events.append(event)
                previous_time = next_time
            # #print("PREVIOUS TIME WAS:", previous_time)

            # Let go of the BSM
            # process = Process(self, "release_bsm", [])
            event = Event(next_time + int(1e12 / self.frequency), self, "release_bsm", [])
            self.own.timeline.events.push(event)
            # self.own.timeline.schedule(event)
            self.scheduled_events.append(event)
            #print('Negotiate Ack end',self.own.name, self.other)
        # When the BSM returns a measurement result
        
        

        elif self.state==2 and msg_type is GenerationMsgType.MEAS_RES:

            #print('Meas result start owner , other,state,memindex',self.own.name, self.other,self.state,self.memory,self.name)
            accepted_index=msg.kwargs['accepted_index']
            if not self.isSuccess:
                # #print("running entanglement success")
                self._entanglement_succeed(accepted_index)
                self.isSuccess = True
                # #print("primary Accepted index :", msg.accepted_index, "qmodes:", len(self.memory.qmodes))
                #change message
                message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.ENTANGLEMENT_SUCCESS, other_protocol=self.other_protocol.name, accepted_index = accepted_index,protocol=self)
                self.own.message_handler.send_message(self.other, message)
            #print('Meas result end',self.own.name, self.other)
            """    
            # Success message received
            elif msg_type is GenerationMsgType.ENTANGLEMENT_SUCCESS:
            #print('Enatanglement success start')
            accepted_index=msg.kwargs['accepted_index']
            self._entanglement_succeed(accepted_index)
            # #print("secondary Accepted index :", msg.accepted_index, "qmodes:", len(self.memory.qmodes))
            self.isSuccess = True
            #print('Enatanglement success end')"""
        else:
            #print("Invalid message {} received by EG on node {} to state {}".format(msg_type, self.own.name,self.state))
            raise Exception("Invalid message {} received by EG on node {} to state {}".format(msg_type, self.own.name,self.state))
        
        self.state += 1
        
        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)

        return True

    def secondary_received_message(self, src: str, msg: Message) -> None:
        """Method to receive messages on the secondary node.
        This method receives messages from other entanglement generation protocols.
        Depending on the message, different actions may be taken by the protocol.
        Args:
            src (str): name of the source node sending the message.
            msg (EntanglementGenerationMessage): message received.
        Side Effects:
            May schedule various internal and hardware events.
        """

        if src not in [self.middle, self.other]:
            return

        if self.state == 2:
            return

        msg_type = msg.msg_type


        if self.state==0 and msg_type is GenerationMsgType.NEGOTIATE:
            # configure params
            #print('BSM negotiate - owner , other , state , memory ,name ',self.own.name, self.other,self.state,self.memory,self.name)
            qc_delay=msg.kwargs['qc_delay']
            another_delay = qc_delay
            self.qc_delay = self.own.qchannels[self.middle].delay
            cc_delay = int(self.own.cchannels[src].delay)
            total_quantum_delay = max(self.qc_delay, another_delay)

            # get time for first excite event
            min_time = self.own.timeline.now() + total_quantum_delay - self.qc_delay + cc_delay
            previous_time = self.own.schedule_qubit(self.middle, min_time)
            # #print("min_time:", min_time, "previous_time", previous_time)

            another_emit_time_0 = previous_time + self.qc_delay - another_delay
            message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.NEGOTIATE_ACK, other_protocol=self.other_protocol.name,
                                                    emit_time_0=another_emit_time_0,protocol=self)
            self.own.message_handler.send_message(src, message)

            # schedule emit
            # process = Process(self, "emit_event", [])
            event = Event(previous_time,self, "emit_event", [])
            self.own.timeline.events.push(event)
            # self.own.timeline.schedule(event)
            self.scheduled_events.append(event)

            # In a batch, schedule all qubits for forming entanglement
            for i in range(100):
                next_time = previous_time + int(1e12 / self.frequency)
                # #print("time of ", i, "th emission at", self.own.name,"is :", next_time)
                # process = Process(self, "schedule_and_emit_event", [next_time])
                event = Event(next_time, self, "schedule_and_emit_event", [next_time])
                # self.own.timeline.schedule(event)
                self.own.timeline.events.push(event)
                self.scheduled_events.append(event)
                previous_time = next_time
            #print(' BSM negotiate end')

        
        elif self.state==1 and msg_type is GenerationMsgType.ENTANGLEMENT_SUCCESS:
            #print('Enatanglement success start-owner , other , state , memory ,name',self.own.name, self.other,self.state,self.memory,self.name)
            accepted_index=msg.kwargs['accepted_index']
            self._entanglement_succeed(accepted_index)
            # #print("secondary Accepted index :", msg.accepted_index, "qmodes:", len(self.memory.qmodes))
            self.isSuccess = True
            #print('Enatanglement success end')
        
        else:
            #print("message type:", msg_type, "state:", self.state, "is_primary:", self.primary)
            #print("EGA exception")
            raise Exception("Invalid message {} received by EG on node {} at state {}".format(msg_type, self.own.name,self.state))

        self.state += 1

        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)
        return True
 

    def is_ready(self) -> bool:
        return self.other_protocol is not None

    def memory_expire(self, memory: "Memory") -> None:
        """Method to receive expired memories."""

        assert memory == self.memory

        self.update_resource_manager(memory, 'RAW')
        for event in self.scheduled_events:
            if event.time >= self.own.timeline.now():
                self.own.timeline.events.remove(event)
                #self.own.timeline.remove_event(event)

    def _entanglement_succeed(self, accepted_index):
        #print("!!!!!!!!!!!!!!!!!!!SUCCEEDED!!!!!!!!!!!!!!!!!!!!!!!!",self.own.name,self.other)
        log.logger.info(self.own.name + " successful entanglement of memory {}".format(self.memory))
        self.memory.entangled_memory["node_id"] = self.other
        self.memory.entangled_memory["memo_id"] = self.remote_memo_id
        self.memory.fidelity = self.memory.raw_fidelity
        self.memory.accepted_index = accepted_index

        self.update_resource_manager(self.memory, 'ENTANGLED')
        #print('_entanglement_succeed:  len(self.subtask.protocols): ', len(self.subtask.protocols))
        self.subtask.on_complete(1)
        dst=self.subtask.task.get_reservation().responder
        src=self.subtask.task.get_reservation().initiator
        if (self.own.name==src and self.other==dst) or (self.own.name==dst and self.other==src) :
            print(f'Entanglement successful between {src,dst}')


    def _entanglement_fail(self):
        #print("Entanglement fail",self.own.name,self.other)
        for event in self.scheduled_events:
            self.own.timeline.events.remove(event)
            #self.own.timeline.remove_event(event)
        log.logger.info(self.own.name + " failed entanglement of memory {}".format(self.memory))
        
        self.update_resource_manager(self.memory, 'RAW')
        self.subtask.on_complete(-1)


class EntanglementGenerationB(EntanglementProtocol):
    """Entanglement generation protocol for BSM node.
    The EntanglementGenerationB protocol should be instantiated on a BSM node.
    Instances will communicate with the A instance on neighboring quantum router nodes to generate entanglement.
    Attributes:
        own (BSMNode): node that protocol instance is attached to.
        name (str): label for protocol instance.
        others (List[str]): list of neighboring quantum router nodes
    """

    def __init__(self, own: "Node", name: str, others: List[str]):
        """Constructor for entanglement generation B protocol.
        Args:
            own (Node): attached node.
            name (str): name of protocol instance.
            others (List[str]): name of protocol instance on end nodes.
        """

        super().__init__(own, name)
        assert len(others) == 2
        self.own.protocols.append(self)
        self.others = others  # end nodes
        self.previous_detection_time = None
        self.frequency = int(1e12 / 2e2)
        self.accepted_indices = 0
        self.current_protocol = None
        self.current_primary = None
        self.reservations = []
        self.first_received = False


    def bsm_update(self, bsm: 'SingleAtomBSM', info: Dict[str, Any]):
        """Method to receive detection events from BSM on node.
        Args:
            bsm (SingleAtomBSM): bsm object calling method.
            info (Dict[str, any]): information passed from bsm.
        """
        #print('Inside BSM update')
        res = info["res"]
        time = info["time"]
        # #print("got photon at", time)
        resolution = self.own.bsm.resolution

        # If this is the first detection
        if self.previous_detection_time == None:
            self.first_received = True
            self.previous_detection_time = time
            return

        # If detection after intermediate cases of no detections from both sources
        elif not self.first_received and (time > (self.previous_detection_time + self.frequency)):
            self.first_received = True
            self.accepted_indices += (time - self.previous_detection_time) // self.frequency
            self.previous_detection_time = time
            return

        # Default case for first received photon
        elif not self.first_received:
            self.first_received = True
            self.accepted_indices += 1
            self.previous_detection_time = time
            return

        # if only one photon received in the window, entanglement success, send message
        elif time > self.previous_detection_time + self.frequency:
            #print("!!!!!!!!!!!!!!!Entanglement SUCESS!!!!!!!!!!!!!!!!!!!")
            ###bug
            #for i, node in enumerate(self.others):
            # #print("sneding accepted indices: ", self.accepted_indices)
            #print("Sending Gen msg type MEAS_RES to ", self.current_protocol,self.current_primary,self.current_protocol.state,self.name ,self.current_protocol.name)
            message = Message(MsgRecieverType.PROTOCOL, self.current_protocol.name, GenerationMsgType.MEAS_RES, protocol = self.current_protocol, res=res, time=time,
                                                    accepted_index=self.accepted_indices)
            self.own.message_handler.send_message(self.current_primary, message)
            self.first_received = False

        # if 2 photons received, entnaglement failure, move to next one
        else:
            # #print("!!!!!!!!!!!!!!!Entanglement FAILURE!!!!!!!!!!!!!!!!!!!")
            self.first_received = False
            self.accepted_indices += 1
            # #print("Others are:", self.others, "present accepted index = ", self.accepted_indices)
            
    def received_message(self, src: str, msg: Message):
        msg_type = msg.msg_type
        ##print("egb ",msg.receiver,msg.receiver_type,self.name,msg_type)

        # If new request comes for access to BSM, check if some process already blocking the BSM. 
        # if yes, append this process to self.reservations, else, allocate it right away. 
        if msg_type is GenerationMsgType.REQUEST_BSM:
            protocol=msg.kwargs['protocol']
            if len(self.reservations) == 0:
                message = Message(MsgRecieverType.PROTOCOL, protocol.name, GenerationMsgType.BSM_ALLOCATE, protocol = protocol)
                #print('BSM allocate', protocol.name, self.name)
                self.own.message_handler.send_message(protocol.own.name, message)
                self.current_protocol = protocol
                self.current_primary = protocol.own.name
                #print("MESAGE SENT TO NODE")
            # else:
            #     for res in self.reservations:
            #         #print("res protocol deatails name ",protocol,protocol.name)
            self.reservations.append(protocol)

            #print("protocol appended: ", protocol)

        # Once attempt to entanglement generation is complete, the BSM is released. Check if other process exist
        # in reservations queue. If yes, start one on top. Else, return 
        elif msg_type is GenerationMsgType.RELEASE_BSM:
            protocol=msg.kwargs['protocol']
            #print("protocol removed:", protocol,self.reservations)
            self.reservations.remove(protocol)
            self.accepted_indices = 0
            self.previous_detection_time = None
            if len(self.reservations) > 0:
                message = Message(MsgRecieverType.PROTOCOL, self.reservations[0].name, GenerationMsgType.BSM_ALLOCATE, protocol = self.reservations[0])
                self.own.message_handler.send_message(self.reservations[0].own.name, message)
                self.current_protocol = self.reservations[0]
                self.current_primary = self.reservations[0].own.name
        ##print("egb",msg.receiver)       
        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)

    def start(self) -> None:
        pass

    def set_others(self, other: "EntanglementProtocol") -> None:
        pass

    def is_ready(self) -> bool:
        return True

    def memory_expire(self) -> None:
        raise Exception("EntanglementGenerationB protocol '{}' should not have memory_expire".format(self.name))