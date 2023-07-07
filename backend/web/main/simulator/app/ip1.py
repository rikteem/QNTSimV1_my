import random

import qntsim
from qntsim.components.circuit import Circuit, QutipCircuit
from qntsim.kernel.timeline import Timeline

Timeline.DLCZ=False
Timeline.bk=True
import logging
import string
import sys

import numpy as np
from qntsim.kernel.quantum_manager import QuantumManager, QuantumManagerKet
from qntsim.protocol import Protocol
# from qntsim.topology.node import QuantumRouter
from qntsim.topology.topology import Topology

logger = logging.getLogger("main_logger.application_layer." + "ip1")


class IP1():

    def request_entanglements(self,sender,receiver,n=50):
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

    def z_measurement(self,qm, keys):
        circ=QutipCircuit(1)       #Z Basis measurement
        circ.measure(0)
        output=qm.run_circuit(circ, keys)
        return list(output.values())[0]

    def print_state_vecs(self,qm, keys):
        for key in keys:
            state=qm.get(key)
            print(state)

    def add_bits_to_pos(self,message, pos, bits):
        assert(len(pos) == len(bits))
        new_message = '0'* (len(message) + len(pos))
        temp = list(new_message)

        c, d = 0, 0
        for i in range(len(new_message)):
            if i in pos:
                temp[i] = str(bits[c])
                c = c + 1
            else : 
                temp[i] = message[d]
                d = d + 1

        return temp

    def generate_Q1A(self,message, c):
        check_bits_pos = random.sample(range(0, len(message) + c), c)
        check_bits_pos.sort()
        check_bits = []

        for i in check_bits_pos:
            random_bit = str(random.randint(0, 1))
            check_bits.append(random_bit)

        new_message = self.add_bits_to_pos(message, check_bits_pos, check_bits)
        logger.info("message by sender: "+ "".join(new_message))
        return new_message, check_bits_pos, check_bits


    def initilize_states(self,qm_alice, message):
        keys = []
        for i in message:
            if i == '0':
                keys.append(qm_alice.new([1, 0]))
            elif i == '1' : 
                keys.append(qm_alice.new([0, 1]))
        return keys

    def apply_theta(self,qm, keys, theta = None):
        if theta == None : 
            theta = random.randint(0, 8)
        for key in keys:
            circ = QutipCircuit(1)
            circ.ry(0, 2*theta/360*np.pi)
            qm.run_circuit(circ, [key])
        return theta

    def get_IDs(self):
        sender_id = "0011"
        receiver_id = "0110"
        logger.info("sender_id: "+str( sender_id))
        logger.info("receiver_id: "+str(receiver_id))
        return sender_id, receiver_id
        

    def hadamard_transform(self,qm, keys):
        circ = QutipCircuit(len(keys))
        for i in range(len(keys)):
            circ.h(i)
        qm.run_circuit(circ, keys)

    def get_IA(self,qm, IdA):
        IA_keys = []
        for i in range(0, len(IdA), 2):
            keys = self.initilize_states(qm, IdA[i + 1])
            assert(len(keys) == 1)
            if IdA[i] == '1':
                self.hadamard_transform(qm, keys)
            IA_keys.append(keys[0])
        return IA_keys

    def add_random_keys(self,keys_to_add, original_keys):
        new_list = ['0' for i in range(len(keys_to_add) + len(original_keys))]
        random_pos = random.sample(range(0, len(new_list)), len(keys_to_add))
        random_pos.sort()
        c, d = 0, 0 
        for i in range(len(new_list)):
            if i in random_pos:
                new_list[i] = keys_to_add[c]
                c = c + 1
            else : 
                new_list[i] = original_keys[d]
                d = d + 1
        # loggger.info("random keys ge
        # : " + "".join(new_list))
        return new_list, random_pos

    def generate_Q2A(self,qm, IdA, Q1A_keys):
        IA_keys = self.get_IA(qm, IdA)
        Q2A_keys, random_pos = self.add_random_keys(IA_keys, Q1A_keys)
        
        return Q2A_keys, random_pos, IA_keys

    def get_IdB1(self,IdB):
        r = ['0' for i in range(len(IdB))]
        for i in range(len(IdB)):
            r[i] = str(random.randint(0,1))

        temp = [str(int(IdB[i])^int(r[i])) for i in range(len(r))]
        IdB1 = ''.join(temp)
        return IdB1, r

    def get_IB(self,qm, IdB1, IdB):
        IB_keys = []

        for i in range(len(IdB1)):
            keys = self.initilize_states(qm, IdB1[i])
            assert len(keys) == 1
            IB_keys.append(keys[0])
            if (IdB[i] == '1'):
                self.hadamard_transform(qm, keys)

        return IB_keys

    def generate_Q3A(self,qm, IdB, Q2A_keys):
        IdB1, r = self.get_IdB1(IdB)
        IB_keys = self.get_IB (qm, IdB1, IdB)
        Q3A_keys, random_pos = self.add_random_keys(IB_keys, Q2A_keys)
        return Q3A_keys, random_pos, IdB1, IB_keys, r

    def get_theta_keys(self,qm, theta, IdB1):
        theta_keys = []
        binary_theta = format(theta, "b")
        for i in range(len(binary_theta)):
            keys = self.initilize_states(qm, binary_theta[i])
            theta_keys.append(keys[0])
            if (IdB1[i] == '1'):
                self.hadamard_transform(qm, keys)

        return theta_keys

    def generate_Q4A(self,qm, theta, Q3A_keys, IdB1):
        theta_keys = self.get_theta_keys(qm, theta, IdB1)
        Q4A_keys, random_pos =self. add_random_keys(theta_keys, Q3A_keys)
        return Q4A_keys, random_pos, theta_keys

    # There's one subtelety in the way decoy qubits work
    # I am putting them in anywhere randomly, yet their results that I save I save in an ordered fashion
    # Thus results and positions do not have a 1-1 correspondance necessarily
    # To change this, I make the random assignment sorted.
    def generate_decoy_qubits(self,qm, m):
        decoy_keys = []
        decoy_results = []
        for i in range(m):
            random_bit = random.randint(0, 1)
            keys = self.initilize_states(qm, str(random_bit))
            decoy_results.append(str(random_bit))
            random_bit = random.randint(0, 1)
            if (random_bit == 1):
                self.hadamard_transform(qm, keys)
            decoy_keys.append(keys[0])
            decoy_results[i] += str(random_bit)
        logger.info("Decoy photons generated: "+ "".join(decoy_results))
        return decoy_keys, decoy_results

    def generate_Q5A(self,qm, Q4A_keys, m):
        decoy_keys, decoy_results = self.generate_decoy_qubits(qm, m)
        Q5A_keys, random_pos = self.add_random_keys(decoy_keys, Q4A_keys)
        return Q5A_keys, random_pos, decoy_results

    def run_encoding_process(self,alice,message, IdA, IdB):
        logger.info("message encoded into the network :" + str(message))
        qm_alice=alice.timeline.quantum_manager
        Q1A, check_bits_pos, check_bits = self.generate_Q1A(message, 3)
        Q1A_keys = self.initilize_states(qm_alice, Q1A)
        theta = self.apply_theta(qm_alice, Q1A_keys)
        
        Q2A_keys, IA_pos, IA_keys = self.generate_Q2A(qm_alice, IdA, Q1A_keys)
        Q3A_keys, IB_pos, IdB1, IB_keys, r = self.generate_Q3A(qm_alice, IdB, Q2A_keys)
        Q4A_keys, theta_keys_pos, theta_keys = self.generate_Q4A(qm_alice, theta, Q3A_keys, IdB1)
        Q5A_keys, decoy_pos, decoy_results =self.generate_Q5A(qm_alice, Q4A_keys, m = 3)
        return Q5A_keys, decoy_pos, decoy_results, IA_keys, IB_keys, r, theta_keys, Q1A_keys, check_bits_pos, check_bits

    def run_security_check(self,qm, Q5A_keys, decoy_pos, decoy_results):
        to_remove = []
        for i, pos in enumerate(decoy_pos):
            if decoy_results[i][1] == '1':
                self.hadamard_transform(qm, [Q5A_keys[pos]])
            output = self.z_measurement(qm, [Q5A_keys[pos]])
            logger.info("key : "+ str(Q5A_keys[pos])+ " output : "+ str(output)+ " expected output : "+ str( decoy_results[i][0]))
            #assert(output == int(decoy_results[i][0])), "Security check did not pass!"
            if output == int(decoy_results[i][0]):
                self.security_msg="Security check passed"  #Security check did not pass!
            else :
                self.security_msg="Security check did not pass" 
            to_remove.append(Q5A_keys[pos])

        logger.info("Security check successful!")
        return list(set(Q5A_keys) - set(to_remove))


    def authenticate_IdA(self,qm, IA_keys, Q5A_keys, IdA):
        c = 0
        for key in Q5A_keys:
            if key not in IA_keys:
                continue

            if IdA[c] == '1':
                self.hadamard_transform(qm, [key])

            output = self.z_measurement(qm, [key])
            if output == int(IdA[c + 1]):
                self.IdA_msg="IdA authenticated"
            else:
                
                self.IdA_msg="IdA authentication did not pass"
               

            #assert(output == int(IdA[c + 1])), "IdA authentication did not pass!"
            c = c + 2
        logger.info("IdA authenticated!")

    def Bobs_IdB1(self,qm, IB_keys, Q5A_keys, IdB):

        local_IdB1 = []

        assert(len(IB_keys) == len(IdB)), " Mismatch in IB_keys and IdB! "
        for i, key in enumerate(IB_keys):
            if IdB[i] == '1':
                self.hadamard_transform(qm, [key])

            local_IdB1.append(self.z_measurement(qm, [key]))

        return local_IdB1

    def check_r(self,IdB, Bobs_IdB1, r):
        Bobs_r = [str(int(IdB[i])^int(Bobs_IdB1[i])) for i in range(len(IdB))]
        logger.info("Bobs_r that he gets : "+ "".join(Bobs_r))
        logger.info("Alice's encoded r : "+ str(r))
        assert (Bobs_r == r), "Bob's r is different from Alice's r! Some error!"
        logger.info("Bob's r is same as Alice's r! Authentication procedure passed")
        ##for output
        return Bobs_r,r

    def authenticate_r(self,qm, IB_keys, Q5A_keys, IdB, r):
        local_IdB1 = self.Bobs_IdB1(qm, IB_keys, Q5A_keys, IdB)
        Bobs_r,r=self.check_r(IdB, local_IdB1, r)
        return Bobs_r,r

    def run_authentication_procedure(self,qm, IdA, IdB, IA_keys, IB_keys, Q5A_keys, r):
        self.authenticate_IdA(qm, IA_keys, Q5A_keys, IdA)
        Bobs_r,r=self.authenticate_r(qm, IB_keys, Q5A_keys, IdB, r)
        return Bobs_r,r

    def Bob_get_theta(self,qm, IdB, theta_keys):
        bin_theta = []
        for i, key in enumerate(theta_keys):
            if IdB[i] == '1':
                self.hadamard_transform(qm, [key])

            bin_theta.append(str(self.z_measurement(qm, [key])))
        str_bin_theta = str("".join(bin_theta))
        theta = int(str_bin_theta, 2)
        return theta

    def Bob_decode_theta(self,qm, Q1A_keys, Bob_theta):
        self.apply_theta(qm, Q1A_keys, -1*Bob_theta)
        Bob_message = []
        for key in Q1A_keys:
            Bob_message.append(str(self.z_measurement(qm, [key])))

        return "".join(Bob_message)

    def Bob_remove_check_bits(self,message, check_bits_pos, check_bits):
        final_message = []
        c = 0
        for pos in range(len(message)):
            if pos in check_bits_pos:
                assert(message[pos] == check_bits[c]), "Check bits not the same!"
                c = c + 1
                continue
            final_message.append(message[pos])

        logger.info("Check bits protocol passed!")
        return final_message

    def run_decoding_process(self,qm, IdB, theta_keys, Q5A_keys, Q1A_keys, check_bits_pos, check_bits):
        Bob_theta = self.Bob_get_theta(qm, IdB, theta_keys)
        Bob_message_with_check_bits = self.Bob_decode_theta(qm, Q1A_keys, Bob_theta)
        Bob_final_message = self.Bob_remove_check_bits(Bob_message_with_check_bits, check_bits_pos, check_bits)
        return "".join(Bob_final_message)


    # TODO: qd_sp transmission
    def copy_Q5A(self,Q5A_keys, alice, bob):
        qm_alice = alice.timeline.quantum_manager
        qm_bob = bob.timeline.quantum_manager
        bob_keys = []
        alice_to_bob_dict = {}

        for alice_key in Q5A_keys:
            state=qm_alice.get(alice_key)
            new_key = qm_bob.new(state.state)
            bob_keys.append(new_key)
            alice_to_bob_dict[alice_key] = new_key

        return alice_to_bob_dict


    def update_keys(self,alice_to_bob_dict, Q5A_keys, IA_keys, IB_keys, theta_keys, Q1A_keys):
        keys_to_update = [Q5A_keys, IA_keys, IB_keys, theta_keys, Q1A_keys]
        new_keys = [[], [], [], [], []]
        for i, batch in enumerate(keys_to_update):
            for key in batch:
                new_keys[i].append(alice_to_bob_dict[key])

        return new_keys



    def run(self,alice,bob,message ):
        print("IP1")
        qm_alice=alice.timeline.quantum_manager
        qm_bob=bob.timeline.quantum_manager
        IdA, IdB = self.get_IDs()
        Q5A_keys, decoy_pos, decoy_results, IA_keys, IB_keys, r, theta_keys, Q1A_keys, check_bits_pos, check_bits =self.run_encoding_process(alice,message, IdA, IdB)
        
        ## Sends qubits to bobs node
        alice_to_bob_dict = self.copy_Q5A(Q5A_keys, alice, bob)
        Q5A_keys, IA_keys, IB_keys, theta_keys, Q1A_keys = self.update_keys(alice_to_bob_dict, Q5A_keys, IA_keys, IB_keys, theta_keys, Q1A_keys)
        ## Maybe use identity gates. Currently simulating it by copying keys

        self.run_security_check(qm_bob, Q5A_keys, decoy_pos, decoy_results)
        Bobs_r,r=self.run_authentication_procedure(qm_bob, IdA, IdB, IA_keys, IB_keys, Q5A_keys, r)
        

        Bob_message = self.run_decoding_process(qm_bob, IdB, theta_keys, Q5A_keys, Q1A_keys, check_bits_pos, check_bits)
        logger.info(f"input message : {message}")
        logger.info(f"Bob_message : {Bob_message}")
        
        if Bobs_r == r : 
            display_msg="Bob's r is same as Alice's r! Authentication procedure passed"
            
        else:
            display_msg="Bob's r is different from Alice's r! Authentication procedure failed!"
        logger.info(display_msg)
        #Bobs_r : Bobs_r that he gets 
        #Alice_r: Alice's encoded r
        res ={
            "Security_msg":self.security_msg,
            "IdA_msg":self.IdA_msg,
            "Bobs_r": Bobs_r,
            "Alice_r ": r,
            "display_msg":display_msg,
            "input_message": message,
            "bob_message" : Bob_message
        }
        # logger.info(res)
        return res
    # One question - technically all of this is happening on Alice's nodes. How do 
    # I send everything to Bob's nodes
    # I don't know
    #run_ip_protocol(message = "010010")

#########################################################################################################################


# sender and receiver (Type :string)-nodes in network 
# backend (Type :string) Qutip (Since entanglements are filtered out based on EPR state)
# message (Type: String)--a bit string
# Todo Support on qiskit
# no.of entanglements=50

# path (Type : String) -Path to config Json file
"""
def ip1(path,sender,receiver,message):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config(path)
    
    alice=network_topo.nodes[sender]
    bob = network_topo.nodes[receiver]
    ip1=IP1()
    alice,bob=ip1.roles(alice,bob,n=50)
    tl.init()
    tl.run()  
    res = ip1.run(alice,bob,message)
    print(res)
"""
# jsonConfig (Type : Json) -Json Configuration of network 
"""
def ip1(jsonConfig,sender,receiver,message):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(jsonConfig)
    
    alice=network_topo.nodes[sender]
    bob = network_topo.nodes[receiver]
    ip1=IP1()
    alice,bob,source_node_list=ip1.roles(alice,bob,n=50)
    tl.init()
    tl.run()  
    ip1.run(alice,bob,message)
conf= {"nodes": [], "quantum_connections": [], "classical_connections": []}
memo = {"frequency": 2e3, "expiry": 0, "efficiency": 1, "fidelity": 1}
node1 = {"Name": "N1", "Type": "end", "noOfMemory": 50, "memory":memo}
node2 = {"Name": "N2", "Type": "end", "noOfMemory": 50, "memory":memo}
node3 = {"Name": "N3", "Type": "service", "noOfMemory": 50, "memory":memo}
conf["nodes"].append(node1)
conf["nodes"].append(node2)
conf["nodes"].append(node3)
qc1 = {"Nodes": ["N1", "N3"], "Attenuation": 1e-5, "Distance": 70}
qc2 = {"Nodes": ["N2", "N3"], "Attenuation": 1e-5, "Distance": 70}
conf["quantum_connections"].append(qc1)
conf["quantum_connections"].append(qc2)
cc1 = {"Nodes": ["N1", "N1"], "Delay": 0, "Distance": 0}
cc1 = {"Nodes": ["N2", "N2"], "Delay": 0, "Distance": 0}
cc1 = {"Nodes": ["N3", "N3"], "Delay": 0, "Distance": 0}
cc12 = {"Nodes": ["N1", "N2"], "Delay": 1e9, "Distance": 1e3}
cc13 = {"Nodes": ["N1", "N3"], "Delay": 1e9, "Distance": 1e3}
cc23 = {"Nodes": ["N2", "N3"], "Delay": 1e9, "Distance": 1e3}
conf["classical_connections"].append(cc12)
conf["classical_connections"].append(cc13)
conf["classical_connections"].append(cc23)
ip1( conf, "N1", "N2", "010010")
"""