import numpy as np
from typing import Any, Callable
from functools import partial
from enum import Enum
from numpy import pi
from numpy.random import randint, uniform
from joblib import Parallel, delayed, wrap_non_picklable_objects

from .network import Network
from ..components.circuit import QutipCircuit

class Attack:
    @staticmethod
    def implement(network:Network, returns:Any, attack:Callable):
        """Implements the mentioned attack based on <ATTACK_TYPE> to the 'network'

        Args:
            network (Network): The network on which the attack is to be applied
            returns (Any): Returns from the previous function
            attack (Callable): Attack to be implemented
        
        Returns:
            returns (Any): Returns from the previous function
        """
        node_indices = range(1, len(network.nodes)) if len(network.nodes)>1 else [0]
        _ = [attack(i=node, network=network) for node in node_indices]
        # Parallel(n_jobs=-1, prefer=None)(attack(i=node, network=network, manager=network.manager) for node in node_indices)
        
        return returns

    @staticmethod
    # @delayed
    # @wrap_non_picklable_objects
    def denial_of_service(i:int, network:Network):
        """Denial of Service

        Args:
            i (int): Index of a node in network
            network (Network): <Network> object on which the attack is implemented
        """
        node = network.nodes[i]
        for info in node.resource_manager.memory_manager:
            if randint(2):
                key = info.memory.qstate_key
                qtc = QutipCircuit(1)
                qtc.rx(0, 2*uniform()*pi)
                qtc.rz(0, 2*uniform()*pi)
                network.manager.run_circuit(qtc, [key])
            # if info.index>network.size-1: break
    
    @staticmethod
    # @delayed
    # @wrap_non_picklable_objects
    def entangle_and_measure(i:int, network:Network):
        """Entangle and Measure

        Args:
            i (int): Index of a node in network
            network (Network): <Network> object on which the attack is implemented
        """
        qtc = QutipCircuit(2)
        qtc.cx(0, 1)
        qtc.measure(1)
        
        node = network.nodes[i]
        network._lk_msg = []
        for info in node.resource_manager.memory_manager:
            key = info.memory.qstate_key
            new_key = network.manager.new([1, 0])
            network._lk_msg.append(network.manager.run_circuit(qtc, [key, new_key]))
            # if info.index>network.size-1: break
    
    @staticmethod
    # @delayed
    # @wrap_non_picklable_objects
    def intercept_and_resend(i:int, network:Network):
        """Intercept and Resend

        Args:
            i (int): Index of a node in network
            network (Network): <Network> object on which the attack is implemented
        """
        node = network.nodes[i]
        network._lk_msg = []
        for info in node.resource_manager.memory_manager:
            key = info.memory.qstate_key
            basis = randint(2)
            qtc = QutipCircuit(1)
            if basis: qtc.h(0)
            qtc.measure(0)
            network._lk_msg.append((result:=network.manager.run_circuit(qtc, [key])))
            new_key = network.manager.new([1-result.get(key), result.get(key)])
            if basis:
                qtc = QutipCircuit(1)
                qtc.h(0)
                network.manager.run_circuit(qtc, [new_key])
                network.manager.get(key).state = network.manager.get(new_key).state
                network.manager.get(new_key).state = np.ndarray([1, 0])
            # if info.index>network.size-1: break
    
class ATTACK_TYPE(Enum):
    DoS = partial(Attack.denial_of_service)
    EM = partial(Attack.entangle_and_measure)
    IR = partial(Attack.intercept_and_resend)