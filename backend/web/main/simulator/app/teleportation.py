
from qntsim.kernel.timeline import Timeline
Timeline.DLCZ=False
Timeline.bk=True

from tabulate import tabulate
from qntsim.components.circuit import Circuit,QutipCircuit
from qiskit import *
from qutip.qip.circuit import QubitCircuit, Gate
from qutip.qip.operations import gate_sequence_product
from qiskit.extensions import Initialize
#from qiskit.ignis.verification import marginal_counts
from qiskit.quantum_info import random_statevector
import math

import logging
logger = logging.getLogger("main_logger.application_layer." + "teleportation")






class Teleportation():

    def request_entanglements(self,sender,receiver):
        sender.transport_manager.request(receiver.owner.name,5e12,1,20e12,0,.5,5e12)
        source_node_list=[sender.name]
        return sender,receiver,source_node_list

    def roles(self,alice,bob):
        sender=alice
        receiver=bob
        print('sender, receiver',sender.owner.name,receiver.owner.name)
        logger.info('sender, receiver: '+sender.owner.name+ " " + receiver.owner.name)
        return self.request_entanglements(sender,receiver)



    def alice_keys(self,alice):
        qm_alice = alice.timeline.quantum_manager
        for mem_info in alice.resource_manager.memory_manager:
            key=mem_info.memory.qstate_key
            state= qm_alice.get(key)
            print("alice entangled state",state.state)          #alice entangled state
            return qm_alice,key,state

    def bob_keys(self,bob):
        qm_bob = bob.timeline.quantum_manager
        for mem_info in bob.resource_manager.memory_manager:
            key=mem_info.memory.qstate_key
            state= qm_bob.get(key)
            #print("bob keys",key,state)
            return qm_bob,key,state
        

    def alice_measurement(self,A_0,A_1,alice):

        case="psi"
        qm_alice,key,alice_state=self.alice_keys(alice)
        #key_0=qm_alice.new([complex(1/math.sqrt(2)), complex(1/math.sqrt(2))])
        key_0=qm_alice.new([A_0, A_1])      #Key for random qubit
        if (alice_state.state[1]==0 and alice_state.state[2]==0):
            if (alice_state.state[0].real>0 and alice_state.state[3].real>0):
                case="psi+"
                print("00+11")
            elif (alice_state.state[0].real<0 and alice_state.state[3].real<0):
                case="-psi+"
                print("-(00+11)")
            elif (alice_state.state[0].real>0 and alice_state.state[3].real<0):
                case="psi-"
                print("00-11")  
            elif (alice_state.state[0].real<0 and alice_state.state[3].real>0):
                case="-psi-"
                print("-00+11")  
        if (alice_state.state[0]==0 and alice_state.state[3]==0):
            if (alice_state.state[1].real>0 and alice_state.state[2].real>0):
                case="phi+"
                print("01+10")
            elif (alice_state.state[1].real>0 and alice_state.state[2].real<0):
                case="phi-"
                print("01-10") 
            elif (alice_state.state[1].real<0 and alice_state.state[2].real<0):
                case="-phi+"
                print("-01-10") 
            elif (alice_state.state[1].real<0 and alice_state.state[2].real>0):
                case="-phi-"
                print("-01+10") 
            
        print("random qubit alice sending",qm_alice.get(key_0).state)
        random_qubit = qm_alice.get(key_0).state   #Random Qubit state
        circ=QutipCircuit(2)
        circ.cx(0,1)
        circ.h(0)
        circ.measure(0)
        circ.measure(1)
        output=qm_alice.run_circuit(circ,[key_0,key])
        # print('OUTPUT',{output})
        crz=output.get(key_0)
        print(f'CRZ{crz}')
        crx=output.get(key)
        print(f'CRX{crx}')
        # circ.measure(1)
        # qm_alice,key,alice_state=alice_keys()
        # alice_state.append()
        print('output',key_0,key,output,crz,crx)
        return crz,crx,case, random_qubit,alice_state
        

    def bob_gates(self,crz,crx,case,bob):
        
        gatesl=[]
        qm_bob,key,state=self.bob_keys(bob)
        if case=="psi+":
            circ=QutipCircuit(1)
            if crx==1:
                circ.x(0)
                gatesl.append('x')
            if crz==1:
                circ.z(0)
                gatesl.append('z')
                #circ.measure(0)
            
        if case=="-psi+":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['z','x','z','x']

                #circ.measure(0)
            elif crz==0 and crx==1:
                circ.z(0)
                circ.x(0)
                circ.z(0)  
                gatesl=['z','x','z']

            elif crz==1 and crx==0:
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['x','z','x']

            elif crz==1 and crx==1:
                circ.z(0)
                circ.x(0)
                gatesl=['z','x']

        if case=="psi-":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                circ.z(0)
                gatesl=['z']

            elif crz==0 and crx==1:  
                circ.z(0)
                circ.x(0)
                gatesl=['z','x']

            elif crz==1 and crx==0:
                gatesl=[]
                pass

            elif crz==1 and crx==1:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                gatesl=['z','x','z']

        if case=="-psi-":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                circ.x(0)
                circ.z(0)
                circ.x(0)
                #circ.measure(0)
                gatesl=['x','z','x']

            elif crz==0 and crx==1:
                circ.x(0)
                circ.z(0)
                gatesl=['x','z']

            elif crz==1 and crx==0:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['z','x','z','x']

            elif crz==1 and crx==1:
                circ.x(0)
                gatesl=['x']

        if case=="phi+":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                circ.x(0)
                gatesl=['x']    
            elif crz==0 and crx==1:
                gatesl=[]
                pass
            elif crz==1 and crx==0:
                circ.x(0)
                circ.z(0)
                gatesl=['x','z']
            elif crz==1 and crx==1:
                circ.z(0)
                gatesl=['z']
        
        if case=="-phi+":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:

                circ.z(0)
                circ.x(0)
                circ.z(0)
                gatesl=['z','x','z']
                
            elif crz==0 and crx==1:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['z','x','z','x']

            elif crz==1 and crx==0:
                circ.z(0)
                circ.x(0)
                gatesl=['z','x']

            elif crz==1 and crx==1:
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['x','z','x']
                
        if case=="-phi-":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                print('crz 1')
                circ.x(0)
                circ.z(0)
                gatesl=['x','z']
                    
            elif crz==0 and crx==1:
                print('crz 1')
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['x','z','x']

            elif crz==1 and crx==0:
                circ.x(0)
                gatesl=['x']
                
            elif crz==1 and crx==1:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                circ.x(0)
                gatesl=['z','x','z','x']
        
        if case=="phi-":
            circ=QutipCircuit(1)
            if crz==0 and crx==0:
                print('crz 1') 
                circ.z(0)
                circ.x(0)
                gatesl=['z','x']
                #circ.measure(0)
            elif crz==0 and crx==1:
                print('crz 1')
                circ.z(0)
                gatesl=['z']

            elif crz==1 and crx==0:
                circ.z(0)
                circ.x(0)
                circ.z(0)
                gatesl=['z','x','z']

            elif crz==1 and crx==1:
                gatesl=[]
                pass
        #circ.measure(0)
        
        output=qm_bob.run_circuit(circ,[key])
        print("Bob's state before corrective measures",state.state)
        print('bob final state after corrective measures',qm_bob.get(key).state)
        return state.state, qm_bob.get(key).state,gatesl

    def run(self,alice,bob,A_0,A_1):
        crz,crx,case, random_qubit,alice_state=self.alice_measurement(A_0,A_1,alice)
        print("Measurement result of random qubit crz",crz)
        logger.info(alice.owner.name + " sent measurement results")
        #print("Measurement result of random qubit crz",crz)
        print("Measurement result of alice qubit crx",crx)
        bob_initial_state, bob_final_state,gatesl = self.bob_gates(crz,crx,case,bob)
        logger.info(bob.owner.name + " received the final state")
        
        # initial entanglement alice_bob_entanglement: alice_bob_entangled_state
        # measurement_result_of_random_qubit near alice's end : meas_rq
        # measurement_result_of_alice_qubit  near alice's end :meas_r1
        # bob_initial_state_before_corrective_measures: bob_initial_state
        # bob_final_state_after_corrective_measures:bob_final_state
        res = {
            "alice_bob_entanglement": alice_state.state,
            "random_qubit" : random_qubit,
            "meas_rq":crz,
            "meas_alice":crx,
            "Corrective_operation":gatesl,
            "bob_initial_state" : bob_initial_state,
            "bob_final_state" : bob_final_state
        }
        print(res)
        return res

#################################################################################################


# sender and receiver (Type :string)-nodes in network 
# backend (Type : String)is Qutip (since state vectors are returned in output)
# Todo support on Qiskit
# A_0 (Type : Complex)
# A_1 (Type : Complex)
# A_0 amplitude of |0> and A_1 amplitude of |1> 
# (abs(A_0)**2 + abs(A_1)**2 ==1) sum of absoulte values of amplitude's squares should be 1

# path (Type : String) -Path to config Json file
"""
def tel(path,sender,receiver,A_0,A_1):

    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config(path)
    
    alice=network_topo.nodes[sender]
    bob = network_topo.nodes[receiver]
    tel= Teleportation()
    alice,bob=tel.roles(alice,bob)
    tl.init()
    tl.run()  
    tel.run(alice,bob,A_0,A_1)
"""

# jsonConfig (Type : Json) -Json Configuration of network 
"""
def tel(jsonConfig,sender,receiver,A_0,A_1):

    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(jsonConfig)
    
    alice=network_topo.nodes[sender]
    bob = network_topo.nodes[receiver]
    tel= Teleportation()
    alice,bob,source_node_list=tel.roles(alice,bob)
    tl.init()
    tl.run()  
    res = tel.run(alice,bob,A_0,A_1)
    print(res)

conf= {"nodes": [], "quantum_connections": [], "classical_connections": []}

memo = {"frequency": 2e3, "expiry": 0, "efficiency": 1, "fidelity": 1}
node1 = {"Name": "N1", "Type": "end", "noOfMemory": 50, "memory":memo}
node2 = {"Name": "N2", "Type": "end", "noOfMemory": 50, "memory":memo}
node3 = {"Name": "N3", "Type": "service", "noOfMemory": 50, "memory":memo}
conf["nodes"].append(node1)
conf["nodes"].append(node2)
conf["nodes"].append(node3)

qc1 = {"Nodes": ["N1", "N2"], "Attenuation": 1e-5, "Distance": 70}
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

tel( conf, "N1", "N2", complex(0.70710678118+0j), complex(0-0.70710678118j))
"""

