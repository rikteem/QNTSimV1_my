import random
from typing import Dict, List

from qntsim.kernel.timeline import Timeline
from qntsim.topology.node import EndNode, ServiceNode
from qntsim.topology.topology import Topology


def generate_topology(topo_type:str, num_end_nodes:int, num_srvc_node:int):
    topology:Dict = {}
    match topo_type:
        case "linear":
            assert num_end_nodes == 2, "Linear topology supports only two end nodes."
            pass
        case "star":
            pass
        case "ring":
            pass

def generate_random_topology():
    topology:Dict = {}
    num_end_node = -1
    num_svcs_node = -1
    nodes = [
        {
            "Type": (type_:=random.choice(["service", "end"])),
            "Name": f"{i}.{type_}{(num_end_node:=num_end_node+1)}" if (type_ == "end")\
                else f"{i}.{type_}{(num_svcs_node:=num_svcs_node+1)}",
            "noOfMemory": random.randint(1, 500)
        } for i in range(random.randint(5, 20))]
    print(f"end nodes: {num_end_node+1}, service nodes: {num_svcs_node+1}")
    if num_end_node == -1 or num_svcs_node == -1: return generate_random_topology()
    end_nodes = [node for node in nodes if node.get("Type")=="end"]
    svcs_nodes = [node for node in nodes if node.get("Type")=="service"]
    quantum_connections = []
    for end_node in end_nodes:
        svcs_node = random.choice(svcs_nodes)
        quantum_connections.append(
            {
                "Nodes": [end_node.get("Name"), svcs_node.get("Name")],
                "Attenuation": 1/10**random.randint(0, 10),
                "Distance": random.randint(1, 10000)
            })
    while len(svcs_nodes)>1:
        svcs_node1 = random.choice(svcs_nodes)
        svcs_nodes.remove(svcs_node1)
        svcs_node2 = random.choice(svcs_nodes)
        quantum_connections.append(
            {
                "Nodes": [svcs_node1.get("Name"), svcs_node2.get("Name")],
                "Attenuation": 1/10**random.randint(0, 10),
                "Distance": random.randint(1, 10000)
            })
    _connections = {}
    for node in nodes:
        node1 = node.get("Name")
        for connection in quantum_connections:
            if node1 in connection.get("Nodes"):
                node2 = [node for node in connection.get("Nodes") if node!=node1][0]
                if _connections.get(node1):
                    _connections.get(node1).append(node2)
                else:
                    _connections[node1] = [node2]
    for src, dst in _connections.items():
        if "service" in src and len(dst) == 1:
            d = dst[0]
            if "service" in d:
                new_node = {
                    "Name": f"{len(nodes)}.end{(num_end_node:=num_end_node+1)}",
                    "Type": "end",
                    "noOfMemory": random.randint(1, 500)}
                nodes.append(new_node)
                quantum_connections.append(
                    {
                        "Nodes":[src, new_node.get("Name")],
                        "Attenuation": 1/10**random.randint(0, 10),
                        "Distance": random.randint(1, 10000)
                    })
    classical_connections = [
        {
            "Nodes": [node1.get("Name"), node2.get("Name")],
            "Delay": 10**random.randint(0, 10),
            "Distance": random.randint(1, 10000)
        } for node1 in nodes for node2 in nodes if node1.get("Name") != node2.get("Name")]
    print("\nNodes")
    for node in nodes:
        print(node)
    print("\nQuantum Connections")
    for qc in quantum_connections:
        print(qc)
    print("\nClassical Connections")
    for cc in classical_connections:
        print(cc)
    topology.update(
        {
            "nodes":nodes,
            "quantum_connections":quantum_connections,
            "classical_connections":classical_connections
        })
    print("\nTopology")
    print(topology)
    return topology

if __name__=="__main__":
    simulator = Timeline(stop_time=10e12, backend="Qutip")
    configuration = Topology(name="foo", timeline=simulator)
    configuration.load_config_json(config=generate_random_topology())
    configuration.get_virtual_graph()
    for node_name, node in configuration.nodes.items():
        try:
            print(node_name, node.neighbors, node.__class__ in [EndNode, ServiceNode])
        except: print(node_name, node.__class__.__name__)