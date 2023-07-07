
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

if TYPE_CHECKING:
    from ..components.bk_memory import Memory
    from ..topology.node import Node
    from ..components.bk_bsm import SingleAtomBSM

from .entanglement_protocol import EntanglementProtocol
from ..message import Message
from ..kernel._event import Event
#from ..kernel.process import Process
from ..components.circuit import BaseCircuit
from ..utils import log
from ..topology.message_queue_handler import ManagerType, ProtocolType,MsgRecieverType
import logging
logger = logging.getLogger("main_logger.link_layer." + "bk_generation")
class GenerationMsgType(Enum):
    """Defines possible message types for entanglement generation."""

    NEGOTIATE = auto()
    NEGOTIATE_ACK = auto()
    MEAS_RES = auto()
    BSM_ALLOCATE = auto()
    RELEASE_BSM = auto()
    REQUEST_BSM = auto()
    
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


    def __init__(self, receiver_type: Enum, receiver: Enum, msg_type:GenerationMsgType, **kwargs) -> None:

        self.receiver_type = receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs

# class Message(Message):
#     """Message used by entanglement generation protocols.
#     This message contains all information passed between generation protocol instances.
#     Messages of different types contain different information.
#     Attributes:
#         msg_type (GenerationMsgType): defines the message type.
#         receiver (str): name of destination protocol instance.
#         qc_delay (int): quantum channel delay to BSM node (if `msg_type == NEGOTIATE`).
#         frequency (float): frequency with which local memory can be excited (if `msg_type == NEGOTIATE`).
#         emit_time (int): time to emit photon for measurement (if `msg_type == NEGOTIATE_ACK`).
#         res (int): detector number at BSM node (if `msg_type == MEAS_RES`).
#         time (int): detection time at BSM node (if `msg_type == MEAS_RES`).
#         resolution (int): time resolution of BSM detectors (if `msg_type == MEAS_RES`).
#     """

#     def __init__(self, msg_type: GenerationMsgType, receiver: str, **kwargs):
#         super().__init__(msg_type, receiver)
#         self.protocol_type = EntanglementGenerationA

#         if msg_type is GenerationMsgType.NEGOTIATE:
#             self.qc_delay = kwargs.get("qc_delay")
#             self.frequency = kwargs.get("frequency")

#         elif msg_type is GenerationMsgType.NEGOTIATE_ACK:
#             self.emit_time_0 = kwargs.get("emit_time_0")
#             self.emit_time_1 = kwargs.get("emit_time_1")

#         elif msg_type is GenerationMsgType.MEAS_RES:
#             self.res = kwargs.get("res")
#             self.time = kwargs.get("time")
#             self.resolution = kwargs.get("resolution")

#         else:
#             raise Exception("EntanglementGeneration generated invalid message type {}".format(msg_type))


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
        """
        Constructor for entanglement generation A class.
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
        self.expected_times = [-1, -1]

        # memory internal info
        self.ent_round = 1  # keep track of current stage of protocol
        self.bsm_res = [-1, -1]  # keep track of bsm measurements to distinguish Psi+ and Psi-

        self.scheduled_events = []

        # misc
        self.primary = False  # one end node is the "primary" that initiates negotiation
        self.debug = False

        self._qstate_key = self.memory.qstate_key
        
        Circuit =BaseCircuit.create(self.memory.timeline.type)
        #print("gen circuit",BaseCircuit.create(self.memory.timeline.type))
        self._plus_state = [sqrt(1/2), sqrt(1/2)]
        self._flip_circuit = Circuit(1)
        self._flip_circuit.x(0)
        self._z_circuit = Circuit(1)
        self._z_circuit.z(0)
        

    def set_others(self, other: "EntanglementGenerationA") -> None:
        
        
        #Method to set other entanglement protocol instance.
        #Args:
        #other (EntanglementGenerationA): other protocol instance.
        

        assert self.other_protocol is None
        assert self.fidelity == other.fidelity
        if other.other_protocol is not None:
            assert self == other.other_protocol
        self.other_protocol = other
        self.remote_memo_id = other.memories[0].name
        self.primary = self.own.name > self.other

    def start(self) -> None:
        
        
        # Method to start entanglement generation protocol.
        # Will start negotiations with other protocol (if primary).
        # Side Effects:
        #     Will send message through attached node.
        
        
        

        log.logger.info(self.own.name + " protocol start with partner {}".format(self.other))
        #logger.info(self.own.name + " protocol start with partner {}".format(self.other))
        # print(self.own.name + " Generation protocol start with partner {}".format(self.other),self.name, self.middle)
        ####print('start protocol',self.other_protocol.name,self.name)
        # to avoid start after remove protocol
        if self not in self.own.protocols:
            return
        bsm_protocol=self.middle + "_eg"
        ####print('bsm protocol', bsm_protocol)
        # start negotiations
        if self.primary:
            #print("primary",self.own.name)
            receiver=self.middle+"_eg"
            message = Message(MsgRecieverType.PROTOCOL, receiver, GenerationMsgType.REQUEST_BSM, protocol = self,other_protocol = self.other_protocol)
            self.own.message_handler.send_message(self.middle, message)
        
       
    def release_bsm(self):
        # Send release bsm message to the BSM
        ##message change
        #print("release_bsm",self.name)
        receiver=self.middle+"_eg"
        #message = Message(MsgRecieverType.PROTOCOL, self.name, GenerationMsgType.RELEASE_BSM, protocol = self)
        message = Message(MsgRecieverType.PROTOCOL, receiver, GenerationMsgType.RELEASE_BSM, protocol = self,other_protocol = self.other_protocol)
        self.own.message_handler.send_message(self.middle, message)
       
            
    def end(self) -> None:
        #print("ENDDDDDDDDDDDDDDDDDDDDDDDD")
        """Method to end entanglement generation protocol.
        Checks the measurement results received to determine if valid entanglement achieved, and what the state is.
        If entanglement is achieved, the memory fidelity will be increased to equal the `fidelity` field.
        Otherwise, it will be set to 0.
        Also performs corrections to map psi+ and psi- states to phi+.
        Side Effects:
            Will call `update_resource_manager` method of base class.
        """

        """if self.bsm_res[0] == -1:
            self.bsm_res[0] = 1
        if self.bsm_res[1] == -1:
            self.bsm_res[1] = 1"""
        ####print('end called',self.name,self.own.name,self.own.timeline.now()*1e-12,self.bsm_res[0],self.bsm_res[1])
        if self.bsm_res[0] != -1 and self.bsm_res[1] != -1:
            # successful entanglement            
            # state correction
            if self.primary:
                self.own.timeline.quantum_manager.run_circuit(self._flip_circuit, [self._qstate_key])
            elif self.bsm_res[0] != self.bsm_res[1]:
                self.own.timeline.quantum_manager.run_circuit(self._z_circuit, [self._qstate_key])
            # #print("Entanglement succes frome end", self.bsm_res[0],self.bsm_res[1])
            self._entanglement_succeed()
            
        else:
            # entanglement failed
            #print('Entanglement failed called from end()')
            self._entanglement_fail()

    def next_round(self) -> None:
        """Sets entanglement generation to next round."""
        self.ent_round += 1

    def emit_event(self) -> None:
        """Method to setup memory and emit photons.
        If the protocol is in round 1, the memory will be first set to the \|+> state.
        Otherwise, it will apply an x_gate to the memory.
        Regardless of the round, the memory `excite` method will be invoked.
        Side Effects:
            May change state of attached memory.
            May cause attached memory to emit photon.
        """

        if self.ent_round == 1:
            self.memory.update_state(self._plus_state)
            # #####print('Emit event plus state',EntanglementGenerationA._plus_state)
        else:
            self.own.timeline.quantum_manager.run_circuit(self._flip_circuit, [self._qstate_key])
            # print('flip circuit', self._qstate_key)
        self.memory.excite(self.middle)

    def received_message(self, src: str, msg: Message) -> None:
        """Method to receive messages.
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

        msg_type = msg.msg_type
        #print('msg_type',msg_type,self.name)
        ####print('self.other',self.other, self.name)
        log.logger.debug(self.own.name + " EG protocol received_message of type {} from node {}, round={}".format(msg.msg_type, src, self.ent_round + 1))

        if  msg_type is GenerationMsgType.BSM_ALLOCATE:
            #logger.info("BSM Allocation message recieved by " + self.own.lightsource.name)

            self.qc_delay = self.own.qchannels[self.middle].delay
            frequency = self.memory.frequency
            ###message
            message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.NEGOTIATE, other_protocol=self.other_protocol.name,
                                                    qc_delay=self.qc_delay, frequency=frequency,protocol=self)
            self.own.message_handler.send_message(self.other, message)
            # print("Message Here", message)
            
            

        elif msg_type is GenerationMsgType.NEGOTIATE:
            #logger.info("Negotiation  message recieved by " + self.own.lightsource.name)
            # configure params
            #####print('negotiate starts')
            qc_delay=msg.kwargs["qc_delay"]
            frequency=msg.kwargs["frequency"]
            another_delay = qc_delay
            self.qc_delay = self.own.qchannels[self.middle].delay
            cc_delay = int(self.own.cchannels[src].delay)
            total_quantum_delay = max(self.qc_delay, another_delay)

            # get time for first excite event
            memory_excite_time = self.memory.next_excite_time
            min_time = max(self.own.timeline.now(), memory_excite_time) + total_quantum_delay - self.qc_delay + cc_delay
            emit_time_0 = self.own.schedule_qubit(self.middle, min_time)
            self.expected_times[0] = emit_time_0 + self.qc_delay

            # get time for second excite event
            local_frequency = self.memory.frequency
            other_frequency = frequency
            total = min(local_frequency, other_frequency)
            min_time = min_time + int(1e12 / total)
            emit_time_1 = self.own.schedule_qubit(self.middle, min_time)
            self.expected_times[1] = emit_time_1 + self.qc_delay

            # schedule emit
            # process = Process(self, "emit_event", [])
            event = Event(emit_time_0, self, "emit_event", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # process = Process(self, "next_round", [])
            event = Event(int((emit_time_0 + emit_time_1) / 2), self, "next_round", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # process = Process(self, "emit_event", [])
            event = Event(emit_time_1, self, "emit_event", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # schedule end of protocol
            end_time = self.expected_times[1] + self.own.cchannels[self.middle].delay + 10
            # process = Process(self, "end", [])
            event = Event(end_time, self, "end", [])
            ####print('negotiate end time',end_time*1e-12,self.own.timeline.now()*1e-12)
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # send negotiate_ack
            another_emit_time_0 = emit_time_0 + self.qc_delay - another_delay
            another_emit_time_1 = emit_time_1 + self.qc_delay - another_delay
            message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.NEGOTIATE_ACK, other_protocol=self.other_protocol.name,
                                                    emit_time_0=another_emit_time_0, emit_time_1=another_emit_time_1,total=total)
            self.own.message_handler.send_message(src, message)
            ####print('Negotiate ends')
            
            
        elif msg_type is GenerationMsgType.NEGOTIATE_ACK:
            #logger.info("Negotiation Acknowledgement message recieved by " + self.own.lightsource.name)
            # configure params
            msg_emit_time_0=msg.kwargs["emit_time_0"]
            msg_emit_time_1=msg.kwargs["emit_time_1"]
            total=msg.kwargs["total"]
            self.expected_times[0] = msg_emit_time_0 + self.qc_delay
            self.expected_times[1] = msg_emit_time_1 + self.qc_delay

            if msg_emit_time_0 < self.own.timeline.now():
                msg_emit_time_0 = self.own.timeline.now()

            # schedule emit
            emit_time_0 = self.own.schedule_qubit(self.middle, msg_emit_time_0)
            assert emit_time_0 == msg_emit_time_0, "%d %d %d" % (emit_time_0, msg_emit_time_0, self.own.timeline.now())
            emit_time_1 = self.own.schedule_qubit(self.middle, msg_emit_time_1)

            # process = Process(self, "emit_event", [])
            event = Event(msg_emit_time_0, self, "emit_event", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # process = Process(self, "next_round", [])
            event = Event(int((msg_emit_time_0 + msg_emit_time_1) / 2), self, "next_round", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # process = Process(self, "emit_event", [])
            event = Event(msg_emit_time_1, self, "emit_event", [])
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)

            # schedule end of protocol
            end_time = self.expected_times[1] + self.own.cchannels[self.middle].delay + 10
            # process = Process(self, "end", [])
            
            #print("end time and offset",msg_emit_time_1+int(1e12 /total),end_time)
            event = Event(msg_emit_time_1+int(1e12 /total), self, "release_bsm", [])
            self.own.timeline.events.push(event)
            # self.own.timeline.schedule(event)
            self.scheduled_events.append(event)

            event = Event(end_time, self, "end", [])
            ###print('negotiate ack end time',end_time*1e-12,self.own.timeline.now()*1e-12)
            self.own.timeline.events.push(event)
            self.scheduled_events.append(event)
            ###print('Negotiate ack ends')
            

            ### scheduling at end of protocol
            
        elif msg_type is GenerationMsgType.MEAS_RES:
            #print('At meas',self.own.name)
            res = msg.kwargs["res"]
            time = msg.kwargs["time"]
            resolution = msg.kwargs["resolution"]

            log.logger.debug(self.own.name + " received MEAS_RES {} at time {}, expected {}, round={}".format(res, time, self.expected_times, self.ent_round))

            def valid_trigger_time(trigger_time, target_time, resolution):
                upper = target_time + resolution
                lower = 0
                if resolution % 2 == 0:
                    upper = min(upper, target_time + resolution // 2)
                    lower = max(lower, target_time - resolution // 2)
                else:
                    upper = min(upper, target_time + resolution // 2 + 1)
                    lower = max(lower, target_time - resolution // 2 + 1)
                if (upper / resolution) % 1 >= 0.5:
                    upper -= 1
                if (lower / resolution) % 1 < 0.5:
                    lower += 1
                return lower <= trigger_time <= upper

            count = 0
            # temp_valid_trigger_time=True
            for i, expected_time in enumerate(self.expected_times):
                ###print(f'Detection time: {time} , Expected Time: {expected_time}',self.expected_times)
                ###print(f'For node: {self.own.name} with node: {src}')
                temp_valid_trigger_time = valid_trigger_time(time, expected_time, resolution)
                ###print('temp_valid_trigger_time: ', temp_valid_trigger_time)
                if temp_valid_trigger_time:
                    ###print(f'For node: {self.own.name} with node: {src} count: {count} and round: {self.ent_round}')
                    count += 1
                    # record result if we don't already have one
                    if self.bsm_res[i] == -1:
                        ###print(f'Setting up the value: {res} at i={i}',self.bsm_res)
                        self.bsm_res[i] = res
                        #if self.primary:
                            #print(f' primary After Setting up the value: {res} at i={i}',self.name,self.own.timeline.now()*1e-12,self.own.name,self.bsm_res)
                        #else:
                            #print(f' secondary After Setting up the value: {res} at i={i}',self.name,self.own.timeline.now()*1e-12,self.own.name,self.bsm_res)
                        #self._entanglement_succeed()
                    else:
                        # entanglement failed
                        ###print('bsm_res', self.bsm_res)
                        #####print('self.expected_times', self.expected_times)
                        ###print('Entanglement failed called from "elif msg_type is GenerationMsgType.MEAS_RES:"')
                        self._entanglement_fail()

        else:
            raise Exception("Invalid message {} received by EG on node {}".format(msg_type, self.own.name))

        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)
        #logger.info("bk_generation message recieved")
        return True

    def is_ready(self) -> bool:
        return self.other_protocol is not None

    def memory_expire(self, memory: "Memory") -> None:
        """Method to receive expired memories."""

        assert memory == self.memory

        self.update_resource_manager(memory, 'RAW')
        for event in self.scheduled_events:
            if event.time >= self.own.timeline.now():
                self.own.timeline.remove_event(event)

    def _entanglement_succeed(self):
        log.logger.info(self.own.name + " successful entanglement of memory {}".format(self.memory))
        #print(self.own.name + " successful entanglement of memory with the node: ",self.other," {} ".format(self.memory))
        
        self.memory.entangled_memory["node_id"] = self.other
        self.memory.entangled_memory["memo_id"] = self.remote_memo_id
        self.memory.fidelity = self.memory.raw_fidelity

        self.update_resource_manager(self.memory, 'ENTANGLED')
        # #print(self.own.name + " entanglement success ",self.other, self.name, self.other_protocol.name)
        self.update_resource_manager(self.memory, 'ENTANGLED')
        #print('_entanglement_succeed:  len(self.subtask.protocols): ', len(self.subtask.protocols))
        dst=self.subtask.task.get_reservation().responder
        src=self.subtask.task.get_reservation().initiator
        # print(f'Entanglement 
        # between (generation) {src,dst} between indices: {self.memory.name, self.remote_memo_id}')
        # if (self.own.name==src and self.other==dst) or (self.own.name==dst and self.other==src) :
        #     print(f'Entanglement successful between (generation) {src,dst}')
        #     logger.info(f'Entanglement successful between {src,dst}')   
        self.subtask.on_complete(1)
        logger.info(f'Entanglement successful between {self.own.name,self.other}')
        if (self.own.name==src and self.other==dst) or (self.own.name==dst and self.other==src) :
            print(f'Entanglement successful between (generation) {src,dst}')
            logger.info(f'Entanglement successful between {self.own.name,self.other}')


    def _entanglement_fail(self):
        for event in self.scheduled_events:
            # ###print('Nemtamgle fieldb ent')
            self.own.timeline.events.remove(event)
        # print(self.own.name + " entanglement fail  ",self.other, self.name, self.other_protocol.name)
        log.logger.info(self.own.name + " failed entanglement of memory {}".format(self.memory))
        
        # #print(self.own.name + " failed entanglement of memory with the node: ",self.other," {} ".format(self.memory.name))
        # ####print(f'Time of entanglement failure: {self.own.timeline.now()}')
        self.update_resource_manager(self.memory, 'RAW')
        #print('_entanglement_fail:  len(self.subtask.protocols): ', len(self.subtask.protocols))
        logger.info(f'Entanglement failed between {self.own.name,self.other}')
        self.subtask.on_complete(-1)


class EntanglementGenerationB(EntanglementProtocol):
    """
    Entanglement generation protocol for BSM node.
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
        self.others = others  # end nodes
        self.other_protocol = []
        #self.protocol= None
        self.own.protocols.append(self)
        self.current_protocol = None
        self.current_primary = None
        self.secondary_protocol=None
        self.reservations = []

    def bsm_update(self, bsm: 'SingleAtomBSM', info: Dict[str, Any]):
        """Method to receive detection events from BSM on node.
        Args:
            bsm (SingleAtomBSM): bsm object calling method.
            info (Dict[str, any]): information passed from bsm.
        """

        assert info['info_type'] == "BSM_res"

        res = info["res"]
        time = info["time"]
        resolution = self.own.bsm.resolution
        
        #message = Message(MsgRecieverType.PROTOCOL, self.other_protocol.name, GenerationMsgType.MEAS_RES, res=res, time=time,
                                                #resolution=resolution,protocol_type=type(self.other_protocol))
        ##print('If Message sent to',self.others[0],self.other_protocol)
        #self.own.message_handler.send_message(self.others[0], message)

        #message = Message(MsgRecieverType.PROTOCOL, self.protocol.name, GenerationMsgType.MEAS_RES, res=res, time=time,
                                                #resolution=resolution,protocol_type=type(self.protocol))
        ##print('If Message sent to',self.others[1], self.protocol)
        #self.own.message_handler.send_message(self.others[1], message)
        message = Message(MsgRecieverType.PROTOCOL, self.current_protocol.name, GenerationMsgType.MEAS_RES, res=res, time=time,
                                                    resolution=resolution)
        self.own.message_handler.send_message(self.current_primary, message)
        message = Message(MsgRecieverType.PROTOCOL, self.secondary_protocol.name, GenerationMsgType.MEAS_RES, res=res, time=time,
                                                    resolution=resolution)
        self.own.message_handler.send_message(self.secondary_protocol.own.name, message)
   
    def received_message(self, src: str, msg: Message):
        msg_type = msg.msg_type
        #print("egb ",msg.receiver,msg.receiver_type,self.name,msg_type)

        # If new request comes for access to BSM, check if some process already blocking the BSM. 
        # if yes, append this process to self.reservations, else, allocate it right away. 
        if msg_type is GenerationMsgType.REQUEST_BSM:
            protocol=msg.kwargs['protocol']
            other_protocol=msg.kwargs['other_protocol']
            if len(self.reservations) == 0:
                message = Message(MsgRecieverType.PROTOCOL, protocol.name, GenerationMsgType.BSM_ALLOCATE, protocol = protocol)
                #print('BSM allocate', protocol.name, self.name)
                self.own.message_handler.send_message(protocol.own.name, message)
                self.current_protocol = protocol
                self.current_primary = protocol.own.name
                self.secondary_protocol=other_protocol
                #print("MESAGE SENT TO NODE")
            #else:
                #for res in self.reservations:
                    #print("res protocol deatails name ",protocol,protocol.name)
            self.reservations.append(protocol)

            #print("protocol appended: ", protocol.name)

        # Once attempt to entanglement generation is complete, the BSM is released. Check if other process exist
        # in reservations queue. If yes, start one on top. Else, return 
        elif msg_type is GenerationMsgType.RELEASE_BSM:
            protocol=msg.kwargs['protocol']
            other_protocol=msg.kwargs['other_protocol']
            #print("protocol removed:", protocol,self.reservations)
            self.reservations.remove(protocol)
            self.accepted_indices = 0
            self.previous_detection_time = None
            if len(self.reservations) > 0:
                message = Message(MsgRecieverType.PROTOCOL, self.reservations[0].name, GenerationMsgType.BSM_ALLOCATE, protocol = self.reservations[0])
                self.own.message_handler.send_message(self.reservations[0].own.name, message)
                self.current_protocol = self.reservations[0]
                self.current_primary = self.reservations[0].own.name
                self.secondary_protocol=self.reservations[0].other_protocol
        #print("egb",msg.receiver)       
        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)

    def start(self) -> None:
        pass

    def set_others(self, other: "EntanglementProtocol") -> None:
        pass

    def is_ready(self) -> bool:
        return True

    def memory_expire(self) -> None:
        raise Exception("EntanglementGenerationB protocol '{}' should not have memory_expire".format(self.name))