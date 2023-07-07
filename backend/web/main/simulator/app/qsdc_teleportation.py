from random import choices
import random
from qntsim.kernel.timeline import Timeline
Timeline.DLCZ=False
Timeline.bk=True
from qntsim.topology.topology import Topology
from qntsim.components.circuit import QutipCircuit
import numpy as np
import math

import logging
logger = logging.getLogger("main_logger.application_layer." + "qsdc_teleportation")


class QSDCTeleportation():
    
    def request_entanglements(self,sender,receiver,n):
        logger.info(sender.owner.name+" requesting entanglement with "+receiver.owner.name)
        sender.transport_manager.request(receiver.owner.name,5e12,n,20e12,0,.5,5e12)
        source_node_list=[sender.name]
        return sender,receiver,source_node_list

    def roles(self,alice,bob,n):
        sender=alice
        receiver=bob
        print('sender, receiver',sender.owner.name,receiver.owner.name)
        logger.info('sender, receiver are '+sender.owner.name+" "+receiver.owner.name)    
        return self.request_entanglements(sender,receiver,n)
    
    def filter_entanglements(self, nodes, correlated=False):
        print('filter entanglement')
        for node in nodes[:len(nodes)-1]:
            node_qm = node.timeline.quantum_manager
            print("check0")
            for info in node.resource_manager.memory_manager:
                print('info', info)
                try:
                    index = info.memory.qstate_key
                    pos = node_qm.get(index)
                    states = pos.state
                    qtc = QutipCircuit(2)
                    if correlated:
                        print('check1')
                        if states[0]==states[3]==0:
                            qtc.x(1)
                            if states[1]==(2*int(relative_phase)-1)*states[2]:
                                qtc.z(0)
                        elif states[0]==(2*int(relative_phase)-1)*states[3]:
                            qtc.z(0)
                    else:
                        print('check2')
                        if states[1]==states[2]==0:
                            qtc.x(1)
                            if states[0]==(2*int(relative_phase)-1)*states[3]:
                                qtc.z(0)
                        elif states[1]==(2*int(relative_phase)-1)*states[2]:
                            qtc.z(0)
                    node_qm.run_circuit(qtc, pos.keys)
                except:
                    print('except')
                    break
        
    
    
    def teleport(self, a, message="01001"):
        """
        Method to perform the teleportation protocol based on the Yan-Zhang protocol
        
        Parameters:
        a : <EndNode>
            This is the sender node which performs the teleportation
        message : str
            This is the bit string which needs to be teleported over the channels
        
        Returns:
        indices : list
            List of indices respective to which bell measurements have been done
        crx : list
            List of bell measurements for Pauli-X corrections
        crz : list
            List of bell measurements for Pauli-Z corrections
        """
    
        a_qm = a.timeline.quantum_manager # quantum manager of the node 'a'
        indices, crz, crx = [], [], []
        # Qutip Circuit for performing Bell measurement
        qtc = QutipCircuit(2)
        qtc.cx(0, 1)
        qtc.h(0)
        qtc.measure(0)
        qtc.measure(1)
        # The loop travles throughout the whole message extracting 1-bit at a time
        # and, teleporting it over the channels
        for i in range(len(message)):
            m = message[i]
            info = a.resource_manager.memory_manager[i]
            index = info.memory.qstate_key
            state = a_qm.get(index)
            keys = state.keys.copy()
            keys.remove(index)
            indices.append(keys[0])
            if m=="0" or m==0:
                new_index = a_qm.new([complex(1/math.sqrt(2)), complex(1/math.sqrt(2))])
            else:
                new_index = a_qm.new([complex(1/math.sqrt(2)), complex(-1/math.sqrt(2))])
            result = a_qm.run_circuit(qtc, [new_index, index])
            crz.append(result.get(new_index))
            crx.append(result.get(index))
        
        return indices, crx, crz


    # ## Decoding the message
    # 
    # This function decodes the message received at the other end node.
    # 
    # The function takes the other end node, list of the bell states at the end node and, the list of the x and z measurements for each bit of message and, returns the message that the block has decoded from the inputs it got.


    def decode(self,b, indices, crx, crz):
        """
        Method to decode the message at the receiver node
        
        Parameters:
        b : <EndNode>
            The reciver node
        indices : list
            List of indices respective to which bell measurements have been done
        crx : list
            List of bell measurements for Pauli-X corrections
        crz : list
            List of bell measurements for Pauli-Z corrections
        
        Returns:
        message : str
            This is the bit string which was decoded after performing local Pauli
            corrections.
        """
        
        message = ''
        b_qm = b.timeline.quantum_manager # quantum manager of node 'b'
        # The loop travels through the list of indices and applies Pauli
        # corrections to the respective key, one at a time
        for index in indices:
            stb = b_qm.get(index)
            i = indices.index(index)
            qtc = QutipCircuit(1)
            if crx[i]==1:
                qtc.x(0)
            if crz[i]==1:
                qtc.z(0)
            qtc.h(0)
            qtc.measure(0)
            result = b_qm.run_circuit(qtc, [index])
            print('decode result', result)
            message = message+str(result.get(index))
        message = ''.join(chr(int(message[i:i+7], 2)) for i in range(0, len(message), 7))
        print("Received: ", message)
        return message
        
        
    def run(self, alice, bob, message, attack):
        
        words = message.split()
        msg = ''
        for word in words:
            msg += ''.join(bin(ord(w))[2:] for w in word)
            msg += '0'+bin(ord(' '))[2:]
        print('alice bob', alice, bob)
        self.filter_entanglements([alice,bob])
        indices, crx, crz = self.teleport(alice, message=message)
        print("indices",indices, crx, crz)
        decoded_msg = self.decode(bob,indices,crx,crz)
        logger.info("message decoded")
        error =0
        res = {
            "input_message":message,
            "output_message":decoded_msg,
            "attack":"DoS",
            "error" : error 
        }
        return res