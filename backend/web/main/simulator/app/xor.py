from qntsim.kernel.timeline import Timeline

Timeline.DLCZ=False
Timeline.bk=True
import json
import logging

from qiskit import *
#from qiskit.ignis.verification import marginal_counts
from qiskit.quantum_info import random_statevector
from qntsim.components.circuit import QutipCircuit
from qntsim.topology.topology import Topology
from qutip.qip.operations import gate_sequence_product
from tabulate import tabulate

logger = logging.getLogger("main_logger.application_layer." + "XOR")


class XOR():

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

    def run(self,alice,bob,charlie,middlenode):

        qm_alice,alice_key,ialicestate=self.alice_keys(alice)
        print('Alicerun',qm_alice,alice_key,ialicestate.state)
        qm_bob,bob_key,ibobstate=self.bob_keys(bob)
        qm_charlie,charlie_key,icharliestate=self.charlie_keys(charlie)
        qm_middle,middle_key,state,middle_entangled_keys=self.middle_keys(middlenode)

        circ = QutipCircuit(3)
        circ.cx(0,2)
        circ.cx(1,2)
        circ.h(0)
        circ.h(1)
        circ.measure(0)
        circ.measure(1)
        circ.measure(2)
        output = qm_middle.run_circuit(circ,middle_entangled_keys)
        print("Output", output)
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
        print(res)
        return res
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