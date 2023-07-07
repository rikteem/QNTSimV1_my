from qntsim.kernel.timeline import Timeline 
Timeline.DLCZ=False
Timeline.bk=True
from qntsim.topology.topology import Topology
from tabulate import tabulate
import pandas as pd

def load_topo(path,backend):

   tl = Timeline(20e12,backend)
   network_topo = Topology("network_topo", tl)
   network_topo.load_config(path)
   return tl,network_topo

def get_res(network_topo,req_pairs):
	cols = ['Index','Source node', 'Entangled Node' , 'Fidelity', 'Entanglement Time' ,'Expire Time', 'State']
	memoryDict = {}
	source_node_list=[]
	#table=[]
	for pair in req_pairs:
		print('src ',pair[0])

		if pair[0] not in source_node_list:
			source_node_list.append(pair[0])
	
		table=[]
		src=pair[0]
		for info in network_topo.nodes[src].resource_manager.memory_manager:
			if info.state == 'ENTANGLED' or info.state == 'OCCUPIED':
				table.append([info.index+1,src,info.remote_node,round(info.fidelity,4),round(info.entangle_time * 1e-12,4),round(info.memory.coherence_time,4),info.state])
		print(tabulate(table, headers=cols, tablefmt='grid'))
		memoryDict["sender"] = table
		
		table=[]
		print('dst ',pair[1])
		dst=pair[1]
		for info in network_topo.nodes[dst].resource_manager.memory_manager:
			if info.state == 'ENTANGLED' or info.state == 'OCCUPIED':
				table.append([info.index+1,dst,info.remote_node,round(info.fidelity,4),round(info.entangle_time * 1e-12,4),round(info.memory.coherence_time,4),info.state])
		print(tabulate(table, headers=cols, tablefmt='grid'))
		memoryDict["receiver"] = table
		print('memory dict', memoryDict)
		return memoryDict ,source_node_list
		 
def set_parameters(topology:Topology):
   
	MEMO_FREQ = 2e4
	MEMO_EXPIRE = 0
	MEMO_EFFICIENCY = 1
	MEMO_FIDELITY = 0.9349367588934053
	for node in topology.get_nodes_by_type("EndNode"):
		node.memory_array.update_memory_params("frequency", MEMO_FREQ)
		node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
		node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
		node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)

	for node in topology.get_nodes_by_type("ServiceNode"):
		node.memory_array.update_memory_params("frequency", MEMO_FREQ)
		node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
		node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
		node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)


	DETECTOR_EFFICIENCY = 0.9
	DETECTOR_COUNT_RATE = 5e7
	DETECTOR_RESOLUTION = 100
	for node in topology.get_nodes_by_type("BSMNode"):
		node.bsm.update_detectors_params("efficiency", DETECTOR_EFFICIENCY)
		node.bsm.update_detectors_params("count_rate", DETECTOR_COUNT_RATE)
		node.bsm.update_detectors_params("time_resolution", DETECTOR_RESOLUTION)
	  

	SWAP_SUCC_PROB = 0.9
	SWAP_DEGRADATION = 0.99

	ATTENUATION = 1e-5
	QC_FREQ = 1e11
	for qc in topology.qchannels:
		qc.attenuation = ATTENUATION
		qc.frequency = QC_FREQ


###############################################################################################


# path (Type : String) -Path to config Json file
# backend (Type : String) -Qiskit/Qutip
#For each Request --below are input parameters
#          sender and receiver (Type : String)-nodes in topology
#          start_time (Type : Float)--start time of request//pico seconds precision
#          size (Type: Integer)--Demand size of request
#          end_time (Type : Float)--end time of request//pico seconds precision
#          target_fidelity(Type : Float)--minimum fidelity requested(<1)
#          priority (Type : Integer)--priority of request
#          timeout (Type : Float)--end time of request//pico seconds precision


"""
def e2e(backend,path,no.of.requests):

	
	tl,network_topo=load_topo(path,backend,start_time,end_time,priority,target_fidelity,timeout)
	set_parameters(network_topo)
	req_pairs=[]
	network_topo.get_virtual_graph()##to view graph
	while (no.of.requests) : 
		###take inupt parameters for each request
		node1=sender 
		node2=receiver            
		tm=network_topo.nodes[node1].transport_manager
		tm.request(node2, float(start_time),int(size), 20e12 , int(priority) ,float(target_fidelity), float(timeout) )
		req_pairs.append((node1,node2))
		no.of.requests--
	tl.init()
	tl.run()
	get_res(network_topo,req_pairs)

"""   