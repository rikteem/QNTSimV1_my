from random import choices

from numpy import random
from qntsim.components.circuit import QutipCircuit
from qntsim.kernel.timeline import Timeline

Timeline.DLCZ=False
Timeline.bk=True
import logging
import time

import numpy as np
from qntsim.topology.topology import Topology

logger = logging.getLogger("main_logger.application_layer." + "ping_pong")

class PingPong():
   
    """print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:\tState:")
    for info in bob.resource_manager.memory_manager:
        print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
                                            str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))
    """

    #I need to request Bell entanglemenets \psi_+ , \psi_-
    alice_key_list, bob_key_list = [], []
    state_key_list=[]
    alice_bob_keys_dict={}
    alice=None
    bob=None
    
    def request_entanglements(self,sender,receiver,n):
        logger.info("Requesting Entanglement...")
        sender.transport_manager.request(receiver.owner.name,5e12,n,20e12,0,.5,5e12)
        source_node_list=[sender.name]
        return sender,receiver,source_node_list

    def roles(self,alice,bob,n):
        sender=alice
        receiver=bob
        print('sender, receiver',sender.owner.name,receiver.owner.name)
        logger.info(f'sender, receiver: {sender.owner.name}, {receiver.owner.name}')
        return self.request_entanglements(sender,receiver,200)
    
    def create_key_lists(self,alice,bob):
        self.alice=alice
        self.bob=bob
        for info in alice.resource_manager.memory_manager:
            alice_key=info.memory.qstate_key
            self.alice_key_list.append(alice_key)
        #print('Alice keys',self.alice_key_list)
        
        for info in bob.resource_manager.memory_manager:
            bob_key=info.memory.qstate_key
            self.bob_key_list.append(bob_key)
        #print('Bob keys',self.bob_key_list)

    def z_measurement(self,qm, key):
        circ=QutipCircuit(1)       #Z Basis measurement
        circ.measure(0)
        output=qm.run_circuit(circ,[key])
        return output

    def check_phi_plus(self,state):
        assert(len(state) == 4)
        if abs(state[0]*np.sqrt(2) - 1)  < 1e-5 and state[1] == 0 and state[2] == 0 and abs(state[3]*np.sqrt(2) - 1)  < 1e-5:
            return True
        elif abs(state[0]*np.sqrt(2) + 1)  < 1e-5 and state[1] == 0 and state[2] == 0 and abs(state[3]*np.sqrt(2) + 1)  < 1e-5:
            return True
        else : return False

    def create_psi_plus_entanglement(self):
        entangled_keys = []
        qm_alice=self.alice.timeline.quantum_manager

        for info in self.bob.resource_manager.memory_manager:

            key=info.memory.qstate_key
            state=qm_alice.get(key)

            #Filtering out unentangeled qubits
            if(len(state.keys) == 1) : continue

            #Filtering out phi_minus, created randomly, from phi_plus
            if(not self.check_phi_plus(state.state)):continue

            #print(state)
            self.state_key_list.append(state.keys)
            #print('state key list', self.state_key_list)
            self.alice_bob_keys_dict[state.keys[0]] = state.keys[1]
            self.alice_bob_keys_dict[state.keys[1]] = state.keys[0]
            self.to_psi_plus(qm_alice, state.keys)
            entangled_keys.append(key)

        return entangled_keys

    def to_psi_plus(self,qm, keys):

        circ=QutipCircuit(2)   
        #change to bell basis
        circ.cx(0,1)
        circ.h(0)   

        #Changing to psi_+
        circ.x(1)

        #back to computational basiss
        circ.h(0) 
        circ.cx(0,1)
        qm.run_circuit(circ, keys)
        #print('to psi plus',keys)
        #return is_psi_plus

    def protocol_c(self,entangled_keys):
        meas_results_alice, meas_results_bob = [] , [] 

        qm_alice=self.alice.timeline.quantum_manager
        for info in self.alice.resource_manager.memory_manager:

            alice_key=info.memory.qstate_key
            state=qm_alice.get(alice_key)
            
            if alice_key not in entangled_keys: continue
            meas_results_alice.append(self.z_measurement(qm_alice, alice_key))
            
        qm_bob=self.bob.timeline.quantum_manager
        for info in self.bob.resource_manager.memory_manager:

            bob_key=info.memory.qstate_key
            state=qm_bob.get(bob_key)
            
            if bob_key not in entangled_keys : continue
            meas_results_bob.append(self.z_measurement(qm_bob, bob_key))

        return meas_results_alice, meas_results_bob

    def encode_and_bell_measure(self,x_n, qm, keys):
        qc=QutipCircuit(2) 
        if(x_n == '1'):
            qc.z(1)
        qc.cx(0,1)
        qc.h(0)
        qc.measure(0)
        qc.measure(1)
        output=qm.run_circuit(qc,keys)
        print("message -> ", x_n)
        logger.info("message -> "+ x_n)
        print(output)
        return output

    def protocol_m(self,x_n, current_keys):

        meas_results_bob = []
        qm_bob=self.bob.timeline.quantum_manager
        #print('protocl m',x_n, current_keys)
        for i,info in enumerate(self.bob.resource_manager.memory_manager):
            bob_key=info.memory.qstate_key
            if bob_key in current_keys:
                if bob_key in self.alice_bob_keys_dict.keys() or bob_key in self.alice_bob_keys_dict.values():
                    #print('new keylist',bob_key,self.alice_bob_keys_dict[bob_key])
                    meas_results_bob.append(self.encode_and_bell_measure(x_n, qm_bob, [bob_key,self.alice_bob_keys_dict[bob_key]]))
        return meas_results_bob


    def get_percentage_accurate(self,bell_results, x_n):
        count = 0
        assert x_n in ['0', '1']

        if x_n == '0':
            for result in bell_results:
                if list(result.values()) == [0, 1]:
                    count+=1
            try:
                return count/len(bell_results)
            except ZeroDivisionError:
                print(f'Error occured , Retry ping_pong again')

        elif x_n == '1':
            for result in bell_results:
                if list(result.values()) == [1, 1]:
                    count+=1
            try:
                return count/len(bell_results)
            except ZeroDivisionError:
                print(f'Error occured , Retry ping_pong again')


    def decode_bell(self,bell_results):
        list_vals = list(bell_results.values())
        if list_vals == [1,1]:
            return '1'
        elif list_vals == [0,1]:
            return '0'
        else : return '#'

    def one_bit_ping_pong(self,x_n, c, sequence_length, entangled_keys, round_num):
        #print("round_num ", round_num)
        self.impurities=[False]
        self.eve_present=False
        memory_size = 10

        current_keys = entangled_keys[round_num*sequence_length : (round_num + 1)*sequence_length]

        draw = random.uniform(0, 1)
        while (draw < c):
            #print("Switching to protocol c ")
            meas_results_alice, meas_results_bob = self.protocol_c(current_keys)

            for i in range(len(meas_results_alice)):
                if not (list(meas_results_alice[i].values())[0] == 1 - list(meas_results_bob[i].values())[0]):
                    #print("Alice and Bob get same states -> Stop Protocol!")
                    self.eve_present=True
                    return -1

            print("Protocol c passes through without trouble! No Eve detected yet")
            logger.info("Protocol c passes through without trouble! No Eve detected yet")
            draw = random.uniform(0, 1)
            #print("meas_results_alice : ", meas_results_alice)
            #print("meas_results_bob : ", meas_results_bob)
            round_num = round_num + 1
            current_keys = entangled_keys[round_num*sequence_length : (round_num + 1)*sequence_length]

        if (draw > c) : 
            bell_results = self.protocol_m(x_n, current_keys)
            round_num = round_num + 1
            #print("HERE", bell_results)
            accuracy = self.get_percentage_accurate(bell_results, x_n)
            #print(accuracy)
            if accuracy == 1 :
                return self.decode_bell(bell_results[0]), round_num

            else : 
                print("protocol m has some impurities; accuracy of transmission is ", accuracy)
                self.impurities=[True,accuracy]
                return -1


    def run(self,sequence_length,message):
        n = 0
        c = 0.2
        #sequence_length = 4
        
        bob_message = ""
        entangled_keys = self.create_psi_plus_entanglement()
        print("entangled_keys",entangled_keys)
        round_num = 0
        
        

        while(n < len(message)):
            n = n+1
            print(" whil n",n,len(message))

            result, round_num = self.one_bit_ping_pong(message[n-1], c,1, entangled_keys, round_num)

            if(result == -1): 
                print("Protocol doesn't run because of the aforesaid mistakes!")

            bob_message = bob_message + result

        print(f"Message transmitted : {message}")
        logger.info(f"Message transmitted : {message}")
        print(f"Message recieved : {bob_message}")
        logger.info(f"Message recieved : {bob_message}")

        res = {
            "Eve_presence":self.eve_present,
            "Impurities_presence":self.impurities,
            "message_transmitted": message,
            "message_received": bob_message
        }
        print(res)
        return res
    #start = time.time()
    #run_ping_pong(alice,bob,sequence_length,message = "010110100")
    #end = time.time()
    #print("time took : ",  end - start)

    # In the request if the runtime is till the simulation, then memory will be sequentially allotted 
    # For quantum router , you can directly change memory size

    # Ask if we can divide task for different slots
    # Ask if we can increase memory for each node (currently it is 100)
    # Ask how to take care of phi plus vs phi minus generation
    # generalize to multiple bits


    # if (aliceMeasurementChoices[i] == 2 and bobMeasurementChoices[i] == 1) or (aliceMeasurementChoices[i] == 3 and bobMeasurementChoices[i] == 2):
    #         aliceKey.append(aliceResults[i]) # record the i-th result obtained by Alice as the bit of the secret key k

    ## Initilize new state as required, and you get key corresponding to these states
    # key = qm_alice.new([amp1, amp2])


#########################################################################################
# sender and receiver (Type :string)-nodes in network 
# backend (Type :string) Qutip (Since entanglements are filtered out based on EPR state)
# Todo support on Qiskit
# message (Type: String)--a bit string
# message length should be less than 9
# sequence length (Type:Integr) should be less than 5


# path (Type : String) -Path to config Json file
"""
def ping_pong1(path,sender,receiver,sequence_length,message):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config(path)
    if len(message)<=9:
        n=int(sequence_length*len(message))
        alice=network_topo.nodes[sender]
        bob = network_topo.nodes[receiver]
        pp=PingPong()
        alice,bob,source_node_list=pp.roles(alice,bob,n)
        tl.init()
        tl.run() 
        pp.create_key_lists(alice,bob)
        res = pp.run(sequence_length,message)
        print(res)
#ping_pong("/home/bhanusree/Desktop/QNTv1/QNTSim-Demo/QNTSim/example/4node.json","a","b",1,"0101")
# jsonConfig (Type : Json) -Json Configuration of network 
def ping_pong(jsonConfig,sender,receiver,sequence_length,message):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(jsonConfig)
    
    n=int(sequence_length)*len(message)
    alice=network_topo.nodes[sender]
    bob = network_topo.nodes[receiver]
    pp=PingPong()
    alice,bob,source_node_list=pp.roles(alice,bob,2*n)
    tl.init()
    tl.run() 
    pp.create_key_lists(alice,bob)
    res = pp.run(sequence_length,message)
    print(res)
   
    
conf= {"nodes": [], "quantum_connections": [], "classical_connections": []}
memo = {"frequency": 2e3, "expiry": 0, "efficiency": 1, "fidelity": 1}
node1 = {"Name": "N1", "Type": "end", "noOfMemory": 500, "memory":memo}
node2 = {"Name": "N2", "Type": "end", "noOfMemory": 500, "memory":memo}
node3 = {"Name": "N3", "Type": "service", "noOfMemory": 500, "memory":memo}
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
ping_pong( conf, "N1", "N2", 4 ,"010010100000111000010001111111")
"""