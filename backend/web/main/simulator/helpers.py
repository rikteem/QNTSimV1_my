

import logging
import string

from qntsim.kernel.timeline import Timeline
from qntsim.topology.topology import Topology

# from .constants import *
# Do Not Remove the following commented imports - this is for local testing purpose
from constants import *

logger = logging.getLogger("main." + "helpers")

def load_topology(network_config_json, backend):
    
    """
        Creates the network with nodes, quantum connections and 
        updates their respective components with the parameters specified in json
    """
    Timeline.DLCZ=False
    Timeline.bk=True
    print(f'Loading Topology: {network_config_json}')
    
    tl = Timeline(20e12,backend)
    logger.info("Timeline initiated with bk protocol")

    #Create the topology
    network_topo = Topology("network_topo", tl)
    network_topo.load_config_json(network_config_json)

    #Configure the parameters

    #Memory Parameters
    for node_properties in network_config_json["nodes"]:
        node = network_topo.nodes[node_properties["Name"]]
        node.memory_array.update_memory_params("frequency", node_properties["memory"]["frequency"])
        node.memory_array.update_memory_params("coherence_time", node_properties["memory"]["expiry"])
        node.memory_array.update_memory_params("efficiency", node_properties["memory"]["efficiency"])
        node.memory_array.update_memory_params("raw_fidelity", node_properties["memory"]["fidelity"])
        node.network_manager.set_swap_success(node_properties["swap_success_rate"])
        node.network_manager.set_swap_degradation(node_properties["swap_degradation"])
    
    #Detector Parameters
    if "detector_properties" in network_config_json:
        for node in network_topo.get_nodes_by_type("BSMNode"):
            node.bsm.update_detectors_params("efficiency", network_config_json["detector_properties"]["efficiency"])
            node.bsm.update_detectors_params("count_rate", network_config_json["detector_properties"]["count_rate"])
            node.bsm.update_detectors_params("time_resolution", network_config_json["detector_properties"]["time_resolution"])
        
    #Light Source Parameters
    if "light_source_properties" in network_config_json:
        Qnodes = network_topo.get_nodes_by_type("EndNode")+network_topo.get_nodes_by_type("ServiceNode")
        for node in Qnodes:
            node.lightsource.frequency = network_config_json["light_source_properties"]["frequency"]
            node.lightsource.wavelength = network_config_json["light_source_properties"]["wavelength"]
            node.lightsource.bandwidth = network_config_json["light_source_properties"]["bandwidth"]
            node.lightsource.mean_photon_num = network_config_json["light_source_properties"]["mean_photon_num"]
            node.lightsource.phase_error = network_config_json["light_source_properties"]["phase_error"]
    
    return network_config_json,tl,network_topo

def get_entanglement_data(network_topo, src, dst):
    success_entx_src, success_entx_dst = 0, 0
    for mem_info in network_topo.nodes[src].resource_manager.memory_manager:
        if mem_info.state == 'ENTANGLED' and mem_info.remote_node == dst:
            success_entx_src += 1

    for mem_info in network_topo.nodes[dst].resource_manager.memory_manager:
        if mem_info.state == 'ENTANGLED' and mem_info.remote_node == src:
            success_entx_dst += 1

    return min(success_entx_src, success_entx_dst)


def get_service_node(nodes):
    
    service_node = []
    for node in nodes:
        if node.get("Type") == "service":
            service_node.append(node.get("Name"))
    
    return service_node
            
    
def get_end_node(nodes,qconnections):
    
    
    service_node = get_service_node(nodes)
    end_node = {}
    for conns in qconnections:
        nodes = conns.get("Nodes")
        if bool(set(service_node) & set(nodes)):
            end_node[nodes[0]] = nodes[1]
    
    
    return end_node


def get_qconnections(quantum_connections):
    
    qconnections = []
    print('quantun conn',quantum_connections)
    for connections in quantum_connections:
        # for nodes in connections.get("Nodes"):
        conn = {}
        print('connections', connections,connections.get("Nodes")[0])
        conn["node1"] = connections.get("Nodes")[0]
        conn["node2"] = connections.get("Nodes")[1]
        conn["attenuation"] = connections.get("Attenuation")
        conn["distance"] = connections.get("Distance")
        qconnections.append(conn)
    
    print('qconnectios', qconnections)
    return qconnections
            
def to_matrix(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]
                     
def get_cconnections(classical_connections):
    
    cchannels_table ={}
    cchannels_table["type"] ="RT"
    nodes = []
    for conn in classical_connections:
        for node in conn.get("Nodes"):
            # print('inside node', node)
            nodes.append(node)
            # for nod in node:
            #     nodes.append(nod)
            
    # print('nodes',nodes)
    nodes = list(set(nodes))
    # print('nodes',nodes)
    cchannels_table["labels"] = nodes
    table = []
    for node1 in nodes:
        for node2 in nodes:
            if node1 == node2:
                table.append(0)
            else:
                table.append(1000000000)
    
    cchannels_table["table"] = to_matrix(table, len(nodes))
    
    return cchannels_table
 
            
def json_topo(topology):
    
    nodes = topology.get("nodes")
    quantum_connections = topology.get("quantum_connections")
    classical_connections = topology.get("classical_connections")
    
    network_json = {}
    service_node = get_service_node(nodes)
    end_node = get_end_node(nodes,quantum_connections)
    
    network_json["service_node"] = service_node
    network_json["end_node"] = end_node
    network_json["qconnections"] = get_qconnections(quantum_connections)
    network_json["cchannels_table"] = get_cconnections(classical_connections)
    
    return network_json
    
    