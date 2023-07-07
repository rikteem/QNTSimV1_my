"""Code for entanglement swapping.
This module defines code for entanglement swapping.
Success is pre-determined based on network parameters.
The entanglement swapping protocol is an asymmetric protocol:
* The EntanglementSwappingA instance initiates the protocol and performs the swapping operation.
* The EntanglementSwappingB instance waits for the swapping result from EntanglementSwappingA.
The swapping results decides the following operations of EntanglementSwappingB.
Also defined in this module is the message type used by these protocols.
"""

from enum import Enum, auto
from typing import TYPE_CHECKING
from functools import lru_cache

import numpy as np
from random import random

if TYPE_CHECKING:
    from ..components.DLCZ_memory import Memory
    from ..topology.node import Node

from ..message import Message
from .entanglement_protocol import EntanglementProtocol
from ..utils import log
from ..components.circuit import BaseCircuit
from ..topology.message_queue_handler import ManagerType, ProtocolType, MsgRecieverType

class SwappingMsgType(Enum):
    """Defines possible message types for entanglement generation."""

    SWAP_RES = auto()


class Message():
    """Message used by entanglement swapping protocols.
    This message contains all information passed between swapping protocol instances.
    Attributes:
        msg_type (SwappingMsgType): defines the message type.
        receiver (str): name of destination protocol instance.
        fidelity (float): fidelity of the newly swapped memory pair.
        remote_node (str): name of the distant node holding the entangled memory of the new pair.
        remote_memo (int): index of the entangled memory on the remote node.
        expire_time (int): expiration time of the new memory pair.
    """

    def __init__(self, receiver_type: Enum, receiver: Enum, msg_type, **kwargs) -> None:

        self.receiver_type = receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs

   

    def __str__(self):
        if self.msg_type == SwappingMsgType.SWAP_RES:
            return "EntanglementSwappingMessage: msg_type: %s; local_memo: %d; fidelity: %.2f; " \
                   "remote_node: %s; remote_memo: %d; " % (self.msg_type, self.local_memo,
                                                           self.fidelity, self.remote_node,
                                                           self.remote_memo)


class EntanglementSwappingA(EntanglementProtocol):
    """Entanglement swapping protocol for middle router.
    The entanglement swapping protocol is an asymmetric protocol.
    EntanglementSwappingA should be instantiated on the middle node, where it measures a memory from each pair to be swapped.
    Results of measurement and swapping are sent to the end routers.
    Variables:
        EntanglementSwappingA.circuit (Circuit): circuit that does swapping operations.
    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        left_memo (Memory): a memory from one pair to be swapped.
        right_memo (Memory): a memory from the other pair to be swapped.
        success_prob (float): probability of a successful swapping operation.
        degradation (float): degradation factor of memory fidelity after the swapping operation.
    """

    #circuit = Circuit(2)
    #circuit.cx(0, 1)
    #circuit.h(0)
    #circuit.measure(0)
    #circuit.measure(1)

    def __init__(self, own: "Node", name: str, left_memo: "Memory", right_memo: "Memory", success_prob=1,
                 degradation=0.95):
        """Constructor for entanglement swapping A protocol.
        Args:
            own (Node): node that protocol is attached to.
            name (str): label for swapping protocol instance.
            left_memo (Memory): memory entangled with a memory on one distant node.
            right_memo (Memory): memory entangled with a memory on the other distant node.
            left_node (str): name of node that contains memory entangling with left_memo.
            left_remote_memo (str): name of memory that entangles with left_memo.
            right_node (str): name of node that contains memory entangling with right_memo.
            right_remote_memo (str): name of memory that entangles with right_memo.
            success_prob (float): probability of a successful swapping operation (default 1).
            degradation (float): degradation factor of memory fidelity after swapping (default 0.95).
            is_success (bool): flag to show the result of swapping
            left_protocol (EntanglementSwappingB): pointer of left protocol (may be removed in the future).
            right_protocol (EntanglementSwappingB): pointer of right protocol (may be removed in the future).
        """

        assert left_memo != right_memo
        EntanglementProtocol.__init__(self, own, name)
        self.memories = [left_memo, right_memo]
        self.left_memo = left_memo
        self.right_memo = right_memo
        self.left_node = left_memo.entangled_memory['node_id']
        self.left_remote_memo = left_memo.entangled_memory['memo_id']
        self.right_node = right_memo.entangled_memory['node_id']
        self.right_remote_memo = right_memo.entangled_memory['memo_id']
        self.success_prob = success_prob
        self.degradation = degradation
        self.is_success = False
        self.left_protocol = None
        self.right_protocol = None
        Circuit =BaseCircuit.create(self.left_memo.timeline.type)
        #print("swap circuit",BaseCircuit.create(self.left_memo.timeline.type))

        self.circuit = Circuit(2)
        self.circuit.cx(0, 1)
        self.circuit.h(0)
        self.circuit.measure(0)
        self.circuit.measure(1)

    def is_ready(self) -> bool:
        return self.left_protocol is not None and self.right_protocol is not None

    def set_others(self, other: "EntanglementSwappingB") -> None:
        """Method to set one other protocol.
        Args:
            other (EntanglementSwappingB): protocol to add to other list.
        """

        if other.own.name == self.left_memo.entangled_memory["node_id"]:
            self.left_protocol = other
        elif other.own.name == self.right_memo.entangled_memory["node_id"]:
            self.right_protocol = other
        else:
            raise Exception("Cannot pair protocol %s with %s" % (self.name, other.name))

    def start(self) -> None:
        # #print("swapping between ", self.left_node,  self.right_node)
        """Method to start entanglement swapping protocol.
        Will run circuit and send measurement results to other protocols.
        Side Effects:
            Will call `update_resource_manager` method.
            Will send messages to other protocols.
        """
        assert self.left_memo.fidelity > 0 and self.right_memo.fidelity > 0
        assert self.left_memo.entangled_memory["node_id"] == self.left_protocol.own.name
        assert self.right_memo.entangled_memory["node_id"] == self.right_protocol.own.name

        # Loging the qmodes and accepted index data at both ends
        # #print("swapping central node at:", self.own.name)
        # #print("number of qmodes at:", self.left_node, "qmode:", len(self.left_memo.qmodes), "accepted index: ", self.left_memo.accepted_index)
        # #print("number of qmodes at:,", self.right_node, "qmode:", len(self.right_memo.qmodes), "accepted index: ", self.right_memo.accepted_index)

        # Reading out the photons in the memory before the accepted photon at both ends. 
        for i in range(self.left_memo.accepted_index-1):
            self.left_memo.read()

        for i in range(self.right_memo.accepted_index-1):
            self.right_memo.read()

        # #print("topmost quantum modes are:", self.left_memo.qmodes[0].is_null, self.right_memo.qmodes[0].is_null)

        # Generate a random no. (<1) to see if swapping is succesful or not
        x_rand = random()

        # See if swapping can be done or not
        if x_rand < self.success_probability():
            
            # If probabilities check out, Find the new fidelity
            fidelity = self.updated_fidelity(self.left_memo.fidelity, self.right_memo.fidelity)
            self.is_success = True

            # Expire the new entanglement at the earliest expiration time of the two memories.
            expire_time = min(self.left_memo.get_expire_time(), self.right_memo.get_expire_time())  

            # Sending messages to both nodes with the new fidelities, and entanglement parters
            msg_l = Message(MsgRecieverType.PROTOCOL, self.left_protocol.name, SwappingMsgType.SWAP_RES, left_protocol=self.left_protocol.name,
                                                fidelity=fidelity,
                                                remote_node=self.right_memo.entangled_memory["node_id"],
                                                remote_memo=self.right_memo.entangled_memory["memo_id"],
                                                expire_time=expire_time,
                                                meas_res=[])
            msg_r = Message(MsgRecieverType.PROTOCOL, self.right_protocol.name ,SwappingMsgType.SWAP_RES, right_protocol=self.right_protocol.name,
                                                fidelity=fidelity,
                                                remote_node=self.left_memo.entangled_memory["node_id"],
                                                remote_memo=self.left_memo.entangled_memory["memo_id"],
                                                expire_time=expire_time,
                                                meas_res=[])
            #print('Entanglement Swapping successful')
            self.subtask.on_complete(1)
        else:
            # if swapping fails, simply return the messages with the updated fidelities as 0 at both ends (set them to raw)
            expire_time = min(self.left_memo.get_expire_time(), self.right_memo.get_expire_time())
            msg_l = Message(MsgRecieverType.PROTOCOL, self.left_protocol.name,SwappingMsgType.SWAP_RES, left_protocol=self.left_protocol.name, fidelity=0,expire_time=expire_time)
            msg_r = Message(MsgRecieverType.PROTOCOL, self.right_protocol.name,SwappingMsgType.SWAP_RES, right_protocol=self.right_protocol.name, fidelity=0,expire_time=expire_time)
            #print('Entanglement Swapping failed')
            self.subtask.on_complete(-1)

        # Sed the messages
        self.own.message_handler.send_message(self.left_node, msg_l)
        self.own.message_handler.send_message(self.right_node, msg_r)

        # Update the middle node's memries to raw
        self.update_resource_manager(self.left_memo, "RAW")
        self.update_resource_manager(self.right_memo, "RAW")

    def success_probability(self) -> float:
        """A simple model for BSM success probability."""

        return self.success_prob

    @lru_cache(maxsize=128)
    def updated_fidelity(self, f1: float, f2: float) -> float:
        """A simple model updating fidelity of entanglement.
        Args:
            f1 (float): fidelity 1.
            f2 (float): fidelity 2.
        Returns:
            float: fidelity of swapped entanglement.
        """

        return f1 * f2 * self.degradation

    def received_message(self, src: str, msg: "Message") -> None:
        """Method to receive messages (should not be used on A protocol)."""
        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)
        raise Exception("EntanglementSwappingA protocol '{}' should not receive messages.".format(self.name))

    def memory_expire(self, memory: "Memory") -> None:
        """Method to receive memory expiration events.
        Releases held memories on current node.
        Memories at the remote node are released as well.
        Args:
            memory (Memory): memory that expired.
        Side Effects:
            Will invoke `update` method of attached resource manager.
            Will invoke `release_remote_protocol` or `release_remote_memory` method of resource manager.
        """

        assert self.is_ready() is False
        if self.left_protocol:
            self.release_remote_protocol(self.left_node)
        else:
            self.release_remote_memory(self.left_node, self.left_remote_memo)
        if self.right_protocol:
            self.release_remote_protocol(self.right_node)
        else:
            self.release_remote_memory(self.right_node, self.right_remote_memo)

        for memo in self.memories:
            if memo == memory:
                self.update_resource_manager(memo, "RAW")
            else:
                self.update_resource_manager(memo, "ENTANGLED")

    def release_remote_protocol(self, remote_node: str):
        self.own.resource_manager.release_remote_protocol(remote_node, self)

    def release_remote_memory(self, remote_node: str, remote_memo: str):
        self.own.resource_manager.release_remote_memory(self, remote_node, remote_memo)


class EntanglementSwappingB(EntanglementProtocol):
    """Entanglement swapping protocol for middle router.
    The entanglement swapping protocol is an asymmetric protocol.
    EntanglementSwappingB should be instantiated on the end nodes, where it waits for swapping results from the middle node.
    Variables:
            EntanglementSwappingB.x_cir (Circuit): circuit that corrects state with an x gate.
            EntanglementSwappingB.z_cir (Circuit): circuit that corrects state with z gate.
            EntanglementSwappingB.x_z_cir (Circuit): circuit that corrects state with an x and z gate.
    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        hold_memory (Memory): quantum memory to be swapped.
    """

    #x_cir = Circuit(1)
    #x_cir.x(0)

    #z_cir = Circuit(1)
    #z_cir.z(0)

    #x_z_cir = Circuit(1)
    #x_z_cir.x(0)
    #x_z_cir.z(0)

    def __init__(self, own: "Node", name: str, hold_memo: "Memory"):
        """Constructor for entanglement swapping B protocol.
        Args:
            own (Node): node protocol is attached to.
            name (str): name of protocol instance.
            hold_memo (Memory): memory entangled with a memory on middle node.
        """

        EntanglementProtocol.__init__(self, own, name)

        self.memories = [hold_memo]
        self.memory = hold_memo
        self.another = None
        Circuit =BaseCircuit.create(self.memory.timeline.type)
        #print("swap circuit",BaseCircuit.create(self.memory.timeline.type))
        self.x_cir = Circuit(1)
        self.x_cir.x(0)

        self.z_cir = Circuit(1)
        self.z_cir.z(0)

        self.x_z_cir = Circuit(1)
        self.x_z_cir.x(0)
        self.x_z_cir.z(0)

    def is_ready(self) -> bool:
        return self.another is not None

    def set_others(self, another: "EntanglementSwappingA") -> None:
        """Method to set one other protocol.
        Args:
            other (EntanglementSwappingA): protocol to set as other.
        """

        self.another = another

    def received_message(self, src: str, msg: "Message") -> None:
        """Method to receive messages from EntanglementSwappingA.
        Args:
            src (str): name of node sending message.
            msg (EntanglementSwappingMesssage): message sent.
        Side Effects:
            Will invoke `update_resource_manager` method.
        """
        #print('Swapping message kwargs', msg.msg_type, msg.kwargs)
        fidelity=msg.kwargs['fidelity']
        expire_time=msg.kwargs['expire_time']
        remote_node=msg.kwargs['remote_node']
        remote_memo=msg.kwargs['remote_memo']
        log.logger.debug(
            self.own.name + " protocol received_message from node {}, fidelity={}".format(src, fidelity))

        assert src == self.another.own.name

        # The only message the end nodes get is to update the memories on the end nodes with the respective outcomes. 
        
        if fidelity > 0 and self.own.timeline.now() < expire_time:
            # case if fideliies are not 0 (swapping succesful)
            self.memory.fidelity = fidelity
            self.memory.entangled_memory["node_id"] = remote_node
            self.memory.entangled_memory["memo_id"] = remote_memo
            self.memory.update_expire_time(expire_time)
            self.update_resource_manager(self.memory, "ENTANGLED")
            #print(f'Entanglement swap successful between {self.own.name, msg.kwargs["remote_memo"]}')
            self.subtask.on_complete(1)
            dst=self.subtask.task.get_reservation().responder
            src=self.subtask.task.get_reservation().initiator
            if (self.own.name==src and msg.kwargs["remote_node"]==dst) or (self.own.name==dst and msg.kwargs["remote_node"]==src) :
                print(f'Entanglement successful between {src,dst}')

        else:
            # case if swapping fails
            self.update_resource_manager(self.memory, "RAW")
            self.subtask.on_complete(-1)
            
        self.own.message_handler.process_msg(msg.receiver_type,msg.receiver)

    def start(self) -> None:
        log.logger.info(self.own.name + " end protocol start with partner {}".format(self.another.own.name))

    def memory_expire(self, memory: "Memory") -> None:
        """Method to deal with expired memories.
        Args:
            memory (Memory): memory that expired.
        Side Effects:
            Will update memory in attached resource manager.
        """

        self.update_resource_manager(self.memory, "RAW")

    def release(self) -> None:
        self.update_resource_manager(self.memory, "ENTANGLED")