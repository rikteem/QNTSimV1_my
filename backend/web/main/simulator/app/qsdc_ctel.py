from qntsim.kernel.timeline import Timeline

Timeline.DLCZ=False
Timeline.bk=True
import json
import logging

import numpy as np
from qiskit import *
#from qiskit.ignis.verification import marginal_counts
from qiskit.quantum_info import random_statevector
from qntsim.components.circuit import QutipCircuit
from qntsim.topology.topology import Topology
from qutip.qip.operations import gate_sequence_product
from tabulate import tabulate

logger = logging.getLogger("main_logger.application_layer." + "QSDC_CTEL")

def display_quantum_state(state_vector):
    """
    Converts a quantum state vector to Dirac notation and returns it as a string.

    Parameters:
    state_vector (numpy.ndarray): An array representing a quantum state vector.

    Returns:
    str: A string representing the input state vector in Dirac notation.
    """

    # Normalize the state vector to ensure its Euclidean norm is equal to 1.
    norm = np.linalg.norm(state_vector)
    if norm < 1e-15:
        return "Invalid state: zero norm"
    normalized_state = state_vector / norm

    # Determine the number of qubits required to represent the state vector.
    dim = len(normalized_state)
    num_digits = int(np.ceil(np.log2(dim)))

    # Generate a list of all possible basis states and initialize the output string.
    basis_states = [format(i, f"0{num_digits}b") for i in range(dim)]
    output_str = ""

    # Iterate over the basis states and add their contribution to the output string.
    for i in range(dim):
        coeff = normalized_state[i]
        if abs(coeff) > 1e-15:  # Ignore small coefficients that round to 0.
            if abs(coeff.imag) > 1e-15:  # Handle complex coefficients.
                output_str += (f"({coeff.real:.2f}" if coeff.real > 0 else "(") + (
                    "+" if coeff.real > 0 and coeff.imag > 0 else "") + f"{coeff.imag:.2f}j)|"
            else:
                output_str += f"({coeff.real:.2f})|"
            output_str += basis_states[i] + "> + "
    output_str = output_str[:-3]  # Remove the trailing " + " at the end.

    return output_str

class QSDC_CTEL():

    

    #Requesting transport manager for entanglements
    def request_entanglements(self,endnode1,endnode2,endnode3,middlenode):
        logger.info("Requesting three two-party entanglements")
        endnode1.transport_manager.request(middlenode.owner.name, 5e12,1, 20e12, 0 , 0.5,2e12) 
        endnode2.transport_manager.request(middlenode.owner.name, 5e12,1, 20e12, 0 , 0.5,2e12) 
        endnode3.transport_manager.request(middlenode.owner.name, 5e12,1, 20e12, 0 , 0.5,2e12) 
        source_node_list=[endnode1.name,endnode2.name,endnode3.name]
        return endnode1,endnode2,endnode3,middlenode,source_node_list

    # set's alice , bob ,charlie and middlenode 
    def roles(self,alice,bob,charlie,middlenode):
        endnode1=alice
        endnode2=bob
        endnode3=charlie
        logger.info('endnode1 , endnode2, endnode3, middlenode are '+endnode1.owner.name+ ", "+endnode2.owner.name+ ", "+endnode3.owner.name+ ", "+middlenode.owner.name)
        
        return self.request_entanglements(endnode1,endnode2,endnode3,middlenode)

    # Gets alice's entangled memory state
    def alice_keys(self,alice):
        qm_alice = alice.timeline.quantum_manager
        for mem_info in alice.resource_manager.memory_manager:
            if mem_info.state == 'ENTANGLED':
                key=mem_info.memory.qstate_key
                state= qm_alice.get(key)
                print("alice state ",key, state.state)
                return qm_alice,key,state
    # Gets bob's entangled memory state
    def bob_keys(self,bob):
        qm_bob = bob.timeline.quantum_manager
        for mem_info in bob.resource_manager.memory_manager:
            if mem_info.state == 'ENTANGLED':
                key=mem_info.memory.qstate_key
                state= qm_bob.get(key)
                print("bob state",key,state.state)
                return qm_bob,key,state

    # Gets charlie's entangled memory state
    def charlie_keys(self,charlie):
        qm_charlie = charlie.timeline.quantum_manager
        for mem_info in charlie.resource_manager.memory_manager:
            if mem_info.state == 'ENTANGLED':
                key=mem_info.memory.qstate_key
                state= qm_charlie.get(key)
                print("charlie state",key,state.state)
                return qm_charlie,key,state
    
    #Gets middlenode's entangled memory state
    def middle_keys(self,middlenode):

        qm_middle = middlenode.timeline.quantum_manager
        middle_entangled_keys=[]
        for mem_info in middlenode.resource_manager.memory_manager:
            # print('middle memory info', mem_info)
            if mem_info.state == 'ENTANGLED':
                key=mem_info.memory.qstate_key
                state= qm_middle.get(key)
                middle_entangled_keys.append(key)
                print("middlenode state",key,state.state,middle_entangled_keys)
        return qm_middle,key,state,middle_entangled_keys


    #alice_keys()
    #bob_keys()
    #charlie_keys()
    #middle_keys()

    #Prepare XOR state
    def xor_state(self,alice,bob,charlie,middlenode):

        qm_alice,alice_key,ialicestate=self.alice_keys(alice)
        print('Alicerun',qm_alice,alice_key,ialicestate.state)
        qm_bob,bob_key,ibobstate=self.bob_keys(bob)
        qm_charlie,charlie_key,icharliestate=self.charlie_keys(charlie)
        qm_middle,middle_key,state,middle_entangled_keys=self.middle_keys(middlenode)
        
        '''
        #Before XOR creation, when only EPR pair is shared

        #Printing keys
        print(f'CHARLIEs KEY{charlie_key}')
        print(f'ALICEs KEY{alice_key}')
        print(f'BOBs KEY{bob_key}')

        #printing charlie_state
        charlie_state=qm_charlie.get(charlie_key).state
        print(f'CHARLIEs STATE in Ket Vectors{display_quantum_state(charlie_state)}')
        # print(f'Charlies states in Complex notation{charlie_state}')

        #printing alice_state
        alice_state=qm_alice.get(alice_key).state
        print(f'ALICEs STATE in Ket Vectors{display_quantum_state(alice_state)}')
        # print(f'Alices states in Complex notation{alice_state}')

        #printing charlie_state
        bob_state=qm_bob.get(bob_key).state
        print(f'BOBs STATE in Ket Vectors{display_quantum_state(bob_state)}')
        # print(f'Bobs states in Complex notation{bob_state}')
        '''

        circ = QutipCircuit(3)
        circ.cx(0,2)
        circ.cx(1,2)
        circ.h(0)
        circ.h(1)
        
        circ.measure(0)
        circ.measure(1)
        circ.measure(2)
        output = qm_middle.run_circuit(circ,middle_entangled_keys)  #mesurement at middle node
        print("Output due to meas at Middle node", output)
        '''
        #After XOR creation by middle node

        #Printing keys
        print(f'CHARLIEs KEY{charlie_key}')
        print(f'ALICEs KEY{alice_key}')
        print(f'BOBs KEY{bob_key}')

        #printing charlie_state
        charlie_state=qm_charlie.get(charlie_key).state
        print(f'CHARLIEs KEY{charlie_key}')
        print(f'CHARLIEs STATE in Ket Vectors{display_quantum_state(charlie_state)}')
        # print(f'Charlies states in Complex notation{charlie_state}')

        #printing alice_state
        alice_state=qm_alice.get(alice_key).state
        print(f'ALICEs STATE in Ket Vectors{display_quantum_state(alice_state)}')
        # print(f'Alices states in Complex notation{alice_state}')

        #printing charlie_state
        bob_state=qm_bob.get(bob_key).state
        print(f'BOBs STATE in Ket Vectors{display_quantum_state(bob_state)}')
        # print(f'Bobs states in Complex notation{bob_state}')

        '''


        XOR_state = qm_middle.get(middle_key).state
        print("\nXOR State\n",  qm_middle.get(middle_key).state)
        logger.info("obtained XOR state: " + str(qm_middle.get(alice_key).state))
        print("\nXOR State alice\n",  qm_middle.get(alice_key).state)
        print("\nXOR State bob\n",  qm_middle.get(bob_key).state)
        print("\nXOR State charlie\n",  qm_middle.get(charlie_key).state)
        res = {
            "initial_alice_state":ialicestate.state,          
            "initial_bob_state":ibobstate.state,
            "initial_charlie_state":icharliestate.state,          
            "final_alice_state":qm_alice.get(alice_key).state ,
            "final_bob_state": qm_bob.get(bob_key).state,
            "final_charlie_state":qm_charlie.get(charlie_key).state,
            
            "alice_state":qm_middle.get(alice_key).state ,
            "bob_state": qm_middle.get(bob_key).state,
            "charlie_state":qm_middle.get(charlie_key).state,
            "XOR_state" : XOR_state
        }
        # print(res)
        return res
    
    #Sender prepares Random qubit to be teleported. Note: This should be connected to the encoding logic replacing the random qubit with |+> and |-> state.
   
    def random_qubit(self,alice,bob, charlie, middlenode, amplitude1,amplitude2):
        qm_alice = alice.timeline.quantum_manager
        print(type(qm_alice))
        key_0=qm_alice.new([amplitude1,amplitude2])
        random_qubit=qm_alice.get(key_0).state
        print(f'Random Qubit state{random_qubit}')
        output={}
        output["random_qubit"]=random_qubit
        return output                              #Do not re-assign output as other variable 
    
    #Initialise state
    def initialise_state(self,alice,qm_alice,message):
        print("Inside Initialise_state")
        qm_alice=alice.timeline.quantum_manager
        keys=[]
        message='10010011'
        for i in message:
            if i=='0':
                keys.append(qm_alice.new([1,0]))
            if i=='1':
                keys.append(qm_alice.new([0,1]))
        return keys
    
    #Apply hadamard
    def apply_hadamard(self,qm_alice,keys):
        circ=QutipCircuit(len(keys))
        for i in range(len(keys)):
            circ.h(i)
            h_out=qm_alice.run_circuit(circ,keys)
            print(f'Hadamard_outputs{h_out}')

    def charlie_state(self,charlie):
        qm_charlie=charlie.timeline.quantum_manager
        for mem_info in charlie.resource_manager.memory_manager:
            key=mem_info.memory.qstate_key
            state=qm_charlie.get(key)
            print('Charlie Entangled state',state.state)
            return qm_charlie,key,state

    #Charlie measures her qubit (Note: The final protocol will have all this steps under run method, QutipCircuits will be only made once inside Run Method)
    def charlie_measure(self,alice,charlie,keys):
        for key in range(len(keys)):
            
            circ=QutipCircuit(3)     #it is a redundant pseudo code where we are making XOR again instead of using the previously prepared XOR
            circ.cx(0,2)
            circ.cx(1,2)
            circ.h(0)
            circ.h(1)
        
        # circ.measure(0)
        # circ.measure(1)
        circ.measure(2)







    #Protocol
    def run(self,alice,bob, charlie, middlenode, amplitude1,amplitude2):
        qm_alice=alice.timeline.quantum_manager
        qm_bob=bob.timeline.quantum_manager
        qm_charlie=charlie.timeline.quantum_manager
        qm_middlenode=middlenode.timeline.quantum_manager
        message='101101'
        list=[]
        for i in range(len(message)):
            print(len(message))
            
            if message[i]=='0':
                # key_0=qm_alice.new([amplitude1,amplitude2])
                # random_qubit=qm_alice.get(key_0).state
                # print(f'Random Qubit state{random_qubit}')
                # output={}
                # output["random_qubit"]=random_qubit
                # list.append(output)
                # for mem_info in alice.resource_manager.memory_manager:
                #     key=mem_info.memory.qstate_key

                circ=QutipCircuit(len(message))
                circ.h(i)
                # circ.measure(i)
                # output=qm_alice.run_circuit(circ,key)
                # list.append(output)
                list.append(circ)
            elif message[i]=='1':
                # key_0=qm_alice.new([amplitude2,amplitude1])
                # random_qubit=qm_alice.get(key_0).state
                # print(f'Random Qubit state{random_qubit}')
                # output={}
                # output["random_qubit"]=random_qubit
                # list.append(output)
                # for mem_info in alice.resource_manager.memory_manager:
                #     key=mem_info.memory.qstate_key

                circ=QutipCircuit(len(message))
                circ.x(i)
                circ.h(i)
                # circ.measure(i)
                # output=qm_alice.run_circuit(circ,key)
                # list.append(output)
                list.append(circ)
        # print(f'LIST{list2}')    
        print(f'LIST{list}')

        qm_alice = alice.timeline.quantum_manager
        # print(type(qm_alice))
        for info in alice.resource_manager.memory_manager:
            if info.state!="RAW":
                key=info.memory.qstate_key
                state=qm_alice.get(key)
                print(f'STATE{state}')
        
        #checking initial state prepared
        print("Inside Initialise_state")
        qm_alice=alice.timeline.quantum_manager
        keys=[]
        message='10010011'
        for i in message:
            if i=='0':
                keys.append(qm_alice.new([1,0]))
            if i=='1':
                keys.append(qm_alice.new([0,1]))
        print(f'Keys{keys}')
        #States corresponding to keys
        state=[]
        for key in keys:
            state.append(qm_alice.get(key).state)
        print(f'State corresponding to keys{state}')           #Print this instead of Random Qubit
        # print(f'Initial state keys{keys}')
        # print(f'States corresponding to keys{state}')


        #Printing XOR state & Calling in method xor_state
        xor_out=self.xor_state(alice,bob,charlie,middlenode)
        #Printing Random Qubit
        key_0=qm_alice.new([amplitude1,amplitude2])
        random_qubit=qm_alice.get(key_0).state
        #Printing equivalent single Qubit state based on classical bit string
        keys=[]
        # message='10010011'
        for i in message:
            if i=='0':
                keys.append(qm_alice.new([1,0]))
            if i=='1':
                keys.append(qm_alice.new([0,1]))
        print(f'Keys{keys}')
        '''States corresponding to keys'''
        state=[]
        for key in keys:
            state.append(qm_alice.get(key).state)
        print(f'State corresponding to SingleQ keys{state}') 
        #Printing Hadamard transform encoded Single qubit state
        keys2=[]       #I have to define new keys because I cannot use the memories in alice's node (they will be entangled ones!!may be?)
        for i in message:
            if i=='0':
                keys2.append(qm_alice.new([1,0]))
            if i=='1':
                keys2.append(qm_alice.new([0,1]))
        print(f'KEYS2{keys2}')
        hdm_states=[]
        '''
        To check the list of keys alloted for dummy_state_list

        # dummy_state_list=[]
        # for i in keys2:
        #     dummy_state_list.append(qm_alice.get(i).state)
        # print(f'dummy_state_list{dummy_state_list}')
        '''
        for key2 in keys2:
            dummy_state=qm_alice.get(key2).state
            print(f'Dummy state: {dummy_state}')
            if np.array_equal(dummy_state,np.array([0.+0.j, 1.+0.j])):
                print(f'DUMMY state: {dummy_state}')
                circ=QutipCircuit(1)
                circ.x(0)
                circ.h(0)
                # circ.measure(0)   #Use this to check whether H gate is applied propoerly, if it is then you will get 50-50 collapse of 0 or 1.
                # print(circ)  #Prints "Qutip circuit object at 0x000..."
                out=qm_alice.run_circuit(circ,[key2])
                print('OUTPUT',{out})
                hdm_states.append(out)
           
            if np.array_equal(dummy_state,np.array([1.+0.j, 0.+0.j])):
                print(f'DUMMY state: {dummy_state}')
                circ=QutipCircuit(1)
                circ.h(0)
                # circ.measure(0)
                out=qm_alice.run_circuit(circ,[key2])
                hdm_states.append(out)
        # print(f'State corresponding to HadamardQ keys{hdm_states}')

        # print(f'Random Qubit state{random_qubit}')
        output={}
        output["random_qubit"]=random_qubit
        output["XOR_output"]=xor_out
        output["Single qubit state"]=state
        output["Hadamard Transformed qubit state"]=hdm_states
        return output


    
    # def run(self,sender,receiver,A_0,A_1):



        # print("Output", output, qm_middle.get(alice_key))

####################################################################################

#endnode1, endnode2 , endnode3 , middlenode (Type :string)- nodes in topology 
#backend (Type :String) is Qutip (since state vectors are returned in output)
#TODO: Support on Qiskit

# path (Type : String) -Path to config Json file
"""
def XOR(path,endnode1,endnode2,endnode3,middlenode):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    report,graph={},{}
    
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config(path)
    alice=network_topo.nodes[endnode1]
    bob = network_topo.nodes[endnode2]
    charlie=network_topo.nodes[endnode3]
    middlenode=network_topo.nodes[middlenode]
    XOR= XOR()
    alice,bob,charlie,middlenode,source_node_list=XOR.roles(alice,bob,charlie,middlenode)
    tl.init()
    tl.run()
    res = XOR.run(alice,bob,charlie,middlenode)
    
    t=1
    timel ,fidelityl,latencyl,fc_throughl,pc_throughl,nc_throughl=[],[],[],[],[],[]
    while t < 20:
        fidelityl= utils.calcfidelity (network_topo,source_node_list,t*1e12,fidelityl)
        
        latencyl= utils.calclatency(network_topo,source_node_list,t*1e12,latencyl)
        fc_throughl,pc_throughl,nc_throughl= utils.throughput(network_topo,source_node_list,t*1e12,fc_throughl,pc_throughl,nc_throughl)
        t=t+2
        timel.append(t)
    
    graph["latency"]    = latencyl
    graph["fidelity"]   = fidelityl
    graph["throughput"] ={fc_throughl,pc_throughl,nc_throughl}
    graph["time"] = timel
    
    report["application"]=res
    report["graph"]=graph
    
    print(report)
# jsonConfig (Type : Json) -Json Configuration of network 
"""
"""
def XOR(jsonConfig,endnode1,endnode2,endnode3,middlenode):
    from qntsim.kernel.timeline import Timeline 
    Timeline.DLCZ=False
    Timeline.bk=True
    from qntsim.topology.topology import Topology
    
    report,graph={},{}
    tl = Timeline(20e12,"Qutip")
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(jsonConfig)
    alice=network_topo.nodes[endnode1]
    bob = network_topo.nodes[endnode2]
    charlie=network_topo.nodes[endnode3]
    middlenode=network_topo.nodes[middlenode]
    XOR= XOR()
    alice,bob,charlie,middlenode,source_node_list=XOR.roles(alice,bob,charlie,middlenode)
    tl.init()
    tl.run()  
    res = XOR.run(alice,bob,charlie,middlenode)
    
    return res
conf= {"nodes": [], "quantum_connections": [], "classical_connections": []}
memo = {"frequency": 2e3, "expiry": 0, "efficiency": 1, "fidelity": 1}
node1 = {"Name": "N1", "Type": "end", "noOfMemory": 50, "memory":memo}
node2 = {"Name": "N2", "Type": "end", "noOfMemory": 50, "memory":memo}
node3 = {"Name": "N3", "Type": "end", "noOfMemory": 50, "memory":memo}
node4 = {"Name": "N4", "Type": "service", "noOfMemory": 50, "memory":memo}
conf["nodes"].append(node1)
conf["nodes"].append(node2)
conf["nodes"].append(node3)
conf["nodes"].append(node4)
qc1 = {"Nodes": ["N1", "N4"], "Attenuation": 1e-5, "Distance": 70}
qc2 = {"Nodes": ["N2", "N4"], "Attenuation": 1e-5, "Distance": 70}
qc3 = {"Nodes": ["N3", "N4"], "Attenuation": 1e-5, "Distance": 70}
conf["quantum_connections"].append(qc1)
conf["quantum_connections"].append(qc2)
conf["quantum_connections"].append(qc3)
cc1 = {"Nodes": ["N1", "N1"], "Delay": 0, "Distance": 0}
cc1 = {"Nodes": ["N2", "N2"], "Delay": 0, "Distance": 0}
cc1 = {"Nodes": ["N3", "N3"], "Delay": 0, "Distance": 0}
cc1 = {"Nodes": ["N4", "N4"], "Delay": 0, "Distance": 0}
cc12 = {"Nodes": ["N1", "N2"], "Delay": 1e9, "Distance": 1e3}
cc13 = {"Nodes": ["N1", "N3"], "Delay": 1e9, "Distance": 1e3}
cc14 = {"Nodes": ["N1", "N4"], "Delay": 1e9, "Distance": 1e3}
cc23 = {"Nodes": ["N2", "N3"], "Delay": 1e9, "Distance": 1e3}
cc24 = {"Nodes": ["N2", "N4"], "Delay": 1e9, "Distance": 1e3}
cc34 = {"Nodes": ["N3", "N4"], "Delay": 1e9, "Distance": 1e3}
conf["classical_connections"].append(cc12)
conf["classical_connections"].append(cc13)
conf["classical_connections"].append(cc14)
conf["classical_connections"].append(cc23)
conf["classical_connections"].append(cc24)
conf["classical_connections"].append(cc34)
XOR(conf,"N1","N2","N3","N4")
"""