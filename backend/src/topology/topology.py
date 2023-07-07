"""Definition of the Topology class.
This module provides a definition of the Topology class, which can be used to manage a network's structure.
Topology instances automatically perform many useful network functions.
"""

from itertools import combinations
from typing import TYPE_CHECKING

import json5

if TYPE_CHECKING:
    from ..kernel.timeline import Timeline

import webbrowser

import matplotlib.pyplot as plt
#----------------------------
import networkx as nx
from pyvis.network import Network

from ..components.optical_channel import ClassicalChannel, QuantumChannel
from ..network_management.reservation import Reservation
from .node import *

#----------------------------


class Topology():
    """Class for managing network topologies.
    The topology class provies a simple interface for managing the nodes and connections in a network.
    A network may also be generated using an external json file.
    Attributes:
        name (str): label for topology.
        timeline (Timeline): timeline to be used for all objects in network.
        nodes (Dict[str, Node]): mapping of node names to node objects.
        qchannels (List[QuantumChannel]): list of quantum channel objects in network.
        cchannels (List[ClassicalChannel]): list of classical channel objects in network.
        graph: (Dict[str, Dict[str, float]]): internal representation of quantum graph.
    """

    def __init__(self, name: str, timeline: "Timeline"):
        """Constructor for topology class.
        Args:
            name (str): label for topology.
            timeline (Timeline): timeline for simulation.
        """

        self.name = name
        self.timeline = timeline
        self.nodes = {}           # internal node dictionary {node_name : node}
        self.qchannels = []       # list of quantum channels
        self.cchannels = []       # list of classical channels
        
        self.graph = {}           # internal quantum graph representation {node_name : {adjacent_name : distance}}
        self.graph_no_middle = {} # internal quantum graph without bsm nodes {node_name : {adjacent_name : distance}}
        self._cc_graph = {}       # internal classical graph representation {node_name : {adjacent_name : delay}}
        self.nx_graph=None
        self.all_pair_shortest_distance={}
        self.djiktras_path=[]
        self.cc_delay_graph={}
        #self.get_virtual_graph=()



    def create_random_topology(self, n, config):  
        labels={}
        G=nx.barabasi_albert_graph(n,1)
        config = json5.load(open(config))
        for node in G.nodes:
            labels[node]="s"+str(node)
            for keys in config["end_node"]:
                labels[node]=keys
    
         # create nodes
        for node_name in G.nodes:
            node = ServiceNode("s"+str(node_name), self.timeline)          
            self.add_node(node)
        for nodes in config["end_node"]:
            # #print('end node params',nodes)
            node = EndNode(nodes,self.timeline)
            # #print(' topology end node', node)
            self.add_node(node)


        #adding cchannels
        for i in G.nodes:
            for j in G.nodes:
                if i==j:                    
                    continue
                # #print('topology', i , j)
                cchannel_params = {"delay": 1e9, "distance": 1e3}
                self.add_classical_channel("s"+str(i) , "s"+str(j), **cchannel_params)
                for end,service in config['end_node'].items():
                    self.add_classical_channel(end,"s"+str(i), **cchannel_params)
                    self.add_classical_channel(end,"s"+str(j), **cchannel_params)
                    self.add_classical_channel("s"+str(j),end, **cchannel_params)
                    self.add_classical_channel("s"+str(i),end, **cchannel_params)
                    # self.add_classical_channel(end,end, **cchannel_params)
        for end, service in config['end_node'].items():
            # #print('key value', end, service)
            cchannel_params = {"delay": 1e9, "distance": 1e3}
            self.add_classical_channel(end,service, **cchannel_params)
            self.add_classical_channel(service,end, **cchannel_params)
            res=list(combinations(*[config['end_node']],2))
            # #print('combinations',res[0])
            for i,(a,b) in enumerate(res):
                self.add_classical_channel(a,b, **cchannel_params)
                self.add_classical_channel(b,a, **cchannel_params)

        # create qconnections (two way quantum channel)
      
        for (src,dst) in G.edges: 
            # #print('src dst',src, dst, G.edges)    
            qconnection_params = {"attenuation": 1e-5, "distance": 70}     
            self.add_quantum_connection("s"+str(src), "s"+str(dst), **qconnection_params)
        for key, value in config['end_node'].items():
            # #print('q connectiom key value', key, value, qconnection_params)
            qconnection_params = {"attenuation": 1e-5, "distance": 70}
            self.add_quantum_connection(key,value, **qconnection_params)


         # generate forwarding tables
        #-------------------------------
        all_pair_dist, G = self.all_pair_shortest_dist()
        print("Returned")
        self.nx_graph=G
        self.all_pair_shortest_distance=all_pair_dist
        # self.djiktras_path=self.djiktras()
        #-------------------------------
        for node in self.nodes.values():
            # #print('nodes',type(node))
            if type(node) != BSMNode:
                node.all_pair_shortest_dist = all_pair_dist
                # print(node.all_pair_shortest_dist)
                node.nx_graph=self.nx_graph
                node.delay_graph=self.cc_delay_graph
                # #print('delay graph',node.name)
                node.neighbors = list(G.neighbors(node.name))
            # if type(node) == EndNode:
            #     # node.all_pair_shortest_dist = all_pair_dist
            #     # node.nx_graph=self.nx_graph
            #     # node.delay_graph=self.cc_delay_graph
            #     #print('Add service node',config['end_node'])
        for key, value in config['end_node'].items():
            # #print('end node key value',node.name, key, value )
            # if node.name == key:
            # #print('check', node.name, key, value)
            self.nodes[key].service_node = value
    
       
    def create_linear_topology(self, n):  
        labels={}
        G=nx.path_graph(n,create_using=None)
        #print("G node",G.nodes)
        for node in G.nodes:
            labels[node]="s"+str(node)
        
        # create nodes
        for node_name in G.nodes:
            #print("bug",node_name,type(node_name))
            if node_name==0 or node_name==n-1:
                #print("node mane",node_name)
                node = EndNode("s"+str(node_name), self.timeline)          
                self.add_node(node)
            else:
                node = ServiceNode("s"+str(node_name), self.timeline)          
                self.add_node(node)

        #TODO:add ccchanels for all possible node pairs
        #adding cchannels
        for i in G.nodes:
            if i!=n-1:
                cchannel_params = {"delay": 1e9, "distance": 1e3}
                self.add_classical_channel("s"+str(i) , "s"+str(i+1), **cchannel_params)
        
        k = range(n)[::-1]
        for i in k:
            if i!=0:
                cchannel_params = {"delay": 1e9, "distance": 1e3}
                self.add_classical_channel("s"+str(i) , "s"+str(i-1), **cchannel_params)
                               
        #create qconnections (two way quantum channel)
        for (src,dst) in G.edges:   
            qconnection_params = {"attenuation": 1e-5, "distance": 70}     
            self.add_quantum_connection("s"+str(src), "s"+str(dst), **qconnection_params)

        all_pair_dist, G = self.all_pair_shortest_dist()
        self.nx_graph=G
        self.all_pair_shortest_distance=all_pair_dist
        for node in self.nodes.values():
            if type(node) != BSMNode:
                node.all_pair_shortest_dist = all_pair_dist
                node.nx_graph=self.nx_graph
                node.delay_graph=self.cc_delay_graph
                node.neighbors = list(G.neighbors(node.name))
        if n>1:
            self.nodes["s"+str(0)].service_node = "s"+str(1)
            self.nodes["s"+str(n-1)].service_node = "s"+str(n-2)
    
    def create_star_topology(self, n):  
        labels={}
        G=nx.star_graph(n,create_using=None)
        #print("Gstar node",G.nodes)
        for node in G.nodes:
            labels[node]="s"+str(node)
        
        # create nodes
        for node_name in G.nodes:
            #print("bug",node_name,type(node_name))
            if node_name==0 :
                #print("node mane",node_name)
                node = ServiceNode("s"+str(node_name), self.timeline)          
                self.add_node(node)
            else:
                node = EndNode("s"+str(node_name), self.timeline)          
                self.add_node(node)

        
        #adding cchannels
        for i in G.nodes:
            if i!=0:
                cchannel_params = {"delay": 1e9, "distance": 1e3}
                self.add_classical_channel("s"+str(0) , "s"+str(i), **cchannel_params)
        
        
        for i in G.nodes:
            if i!=0:
                cchannel_params = {"delay": 1e9, "distance": 1e3}
                self.add_classical_channel("s"+str(i) , "s"+str(0), **cchannel_params)
                               
        #create qconnections (two way quantum channel)
        for (src,dst) in G.edges:   
            qconnection_params = {"attenuation": 1e-5, "distance": 70}     
            self.add_quantum_connection("s"+str(src), "s"+str(dst), **qconnection_params)

        all_pair_dist, G = self.all_pair_shortest_dist()
        self.nx_graph=G
        self.all_pair_shortest_distance=all_pair_dist
        for node in self.nodes.values():
            if type(node) != BSMNode:
                node.all_pair_shortest_dist = all_pair_dist
                node.nx_graph=self.nx_graph
                node.delay_graph=self.cc_delay_graph
                node.neighbors = list(G.neighbors(node.name))
        for i in range(n+1):
            if i!=0:
                self.nodes["s"+str(i)].service_node = "s"+str(0)

    def load_config_json(self, config) -> None:
        #print("lcj_start",config)
        #print()
        """Method to load a network configuration file.
        Network should be specified in json format.
        Will populate nodes, qchannels, cchannels, and graph fields.
        Will also generate and install forwarding tables for quantum router nodes.
        Args:
            config (dictionary): json network configuration
            {
                "nodes": [{
                    "Name": "Name of node",
                    "Type": ["service", "end"],
                    "noOfMemory": 50, # No of Memories
                    "memory":{
                        "frequency": 2e4, # Memory Frequency
                        "expiry": 0, # Memory Expiry Time
                        "efficiency": 2e4, # Memory Efficiency
                        "fidelity": 2e4, # Memory Fidelity
                    },
                }],
                "quantum_connections": [{
                    "Nodes": ["N1", "N2"] # Name of connected nodes
                    "Attenuation": 1e-5,
                    "Distance": 70,
                }],
                "classical_connections": [{
                    "Nodes": ["N1", "N2"] # Name of connected nodes
                    "Delay": 1e-5,
                    "Distance": 1e3,
                }],
            }
        Side Effects:
            Will modify graph, graph_no_middle, qchannels, and cchannels attributes.
        """
        for node in config["nodes"]:
            #print("test check lcj nodes",node,node["Type"],type(node["Type"]))
            nodeObj = None
            if node["Type"] == "service":
                nodeObj = ServiceNode(node["Name"],self.timeline,node["noOfMemory"])
                #self.add_node(nodeObj)
            elif node["Type"] == "end":
                #print("check Type",node["Name"])
                nodeObj = EndNode(node["Name"],self.timeline,node["noOfMemory"])
                #self.add_node(nodeObj)
            
            
            if nodeObj is None:
                return f"Wrong type {node['Type']}"
            else:
                #nodeObj.memory_array.update_memory_params("frequency", node["memory"]["frequency"])
                #nodeObj.memory_array.update_memory_params("coherence_time", node["memory"]["expiry"])
                #nodeObj.memory_array.update_memory_params("efficiency", node["memory"]["efficiency"])
                #nodeObj.memory_array.update_memory_params("raw_fidelity", node["memory"]["fidelity"])
                for arg, val in node.get("memory", {}).items():
                    nodeObj.memory_array.update_memory_params(arg, val)
                for arg, val in node.get("lightSource", {}).items():
                    setattr(nodeObj.lightsource, arg, val)
                nodeObj.network_manager.set_swap_success(es_swap_success=node.get("swap_success_rate", 1))
                nodeObj.network_manager.set_swap_degradation(es_swap_degradation=node.get("swap_degradation", 0.99))
                self.add_node(nodeObj)
            
            
        for cc in config["classical_connections"]:
           
            cchannel_params = {
                "delay": cc["Delay"]/2,  # divide RT time by 2
                "distance": cc["Distance"]
            }
            if cc["Nodes"][0] is cc["Nodes"][1]:
                continue
            else:
                self.add_classical_channel(cc["Nodes"][0], cc["Nodes"][1], **cchannel_params)
                self.add_classical_channel(cc["Nodes"][1], cc["Nodes"][0], **cchannel_params)
        
        for qc in config["quantum_connections"]:
            
            qchannel_params = {
                "attenuation": qc["Attenuation"],
                "distance": qc["Distance"]
            }
            self.add_quantum_connection(qc["Nodes"][0], qc["Nodes"][1], **qchannel_params)
        
          
        # generate forwarding tables
        #-------------------------------
        all_pair_dist, G = self.all_pair_shortest_dist()
        # print('all pair distance', all_pair_dist, G)
        self.nx_graph=G
        #print('self.nx_graph',self.nx_graph,self.name)
        
        #-------------------------------
        for nodeObj in self.nodes.values():
            if type(nodeObj) != BSMNode:
                nodeObj.all_pair_shortest_dist = all_pair_dist
                # print(nodeObj.all_pair_shortest_dist)
                nodeObj.nx_graph=self.nx_graph
                nodeObj.delay_graph=self.cc_delay_graph
                nodeObj.neighbors = list(G.neighbors(nodeObj.name))
            else:
                for arg, val in config.get("detector", {}).items():
                    setattr(nodeObj.bsm, arg, val)
        
        
        
        for qc in config["quantum_connections"]:
            qcnode0 = next(filter(lambda node: node.name == qc["Nodes"][0], self.nodes.values()), None)
            qcnode1 = next(filter(lambda node: node.name == qc["Nodes"][1], self.nodes.values()), None)
            #print(qcnode0,qcnode0.name,qcnode1,qcnode1.name)
            if type(qcnode0) == EndNode:
                if type(qcnode1) == EndNode:
                    qcnode0.end_node = qc["Nodes"][1]
                    qcnode1.end_node = qc["Nodes"][0]
                else:
                    qcnode0.service_node = qc["Nodes"][1]
                    qcnode1.end_node = qc["Nodes"][0]
            else:
                if type(qcnode1) == EndNode:
                    qcnode0.end_node = qc["Nodes"][1]
                    qcnode1.service_node = qc["Nodes"][0]
                else:
                    qcnode0.service_node = qc["Nodes"][1]
                    qcnode1.service_node = qc["Nodes"][0]
                    
            #self.nodes[qc["Nodes"][0]] = qcnode0
            #self.nodes[qc["Nodes"][1]] = qcnode1
        
        
    def load_config(self, config_file: str) -> None:
        """Method to load a network configuration file.
        Network should be specified in json format.
        Will populate nodes, qchannels, cchannels, and graph fields.
        Will also generate and install forwarding tables for quantum router nodes.
        Args:
            config_file (str): path to json file specifying network.
        Side Effects:
            Will modify graph, graph_no_middle, qchannels, and cchannels attributes.
        """

        config = json5.load(open(config_file))
        delay_list=[]
        # create nodes
        for params in config["service_node"]:
            # #print('params',params)
            node = ServiceNode(params,self.timeline)
            self.add_node(node)
        for params in config["end_node"]:
            # #print('end node params',params)
            node = EndNode(params,self.timeline)
            self.add_node(node)
        # for node_params in config["nodes"]:
        #     name = node_params.pop("name")
        #     node_type = node_params.pop("type")
        
        #     if node_type == "EndNode":
        #         node = EndNode(name, self.timeline, **node_params)
        #     elif node_type == "ServiceNode":
        #         node = ServiceNode(name, self.timeline, **node_params)
        #     else:
        #         node = Node(name, self.timeline)
        #     #print('Topology node1',node,node_type)
        #     self.add_node(node)
        # #print('adding connections')
        # create discrete cconnections (two way classical channel)
        if "cconnections" in config:
            for cchannel_params in config["cconnections"]:
                node1 = cchannel_params.pop("node1")
                node2 = cchannel_params.pop("node2")
                # #print('cconnections',node1,node2)
                self.add_classical_connection(node1, node2, **cchannel_params)

        # create discrete cchannels
        # #print('adding cc connections')
        if "cchannels" in config:
            for cchannel_params in config["cchannels"]:
                node1 = cchannel_params.pop("node1")
                node2 = cchannel_params.pop("node2")
                # #print(' cchanels', node1,node2)
                self.add_classical_channel(node1, node2, **cchannel_params)

        # create cchannels from a RT table
        # #print('adding cc channels')
        if "cchannels_table" in config:
            table_type = config["cchannels_table"].get("type", "RT")
            assert table_type == "RT", "non-RT tables not yet supported"
            labels = config["cchannels_table"]["labels"]
            table = config["cchannels_table"]["table"]
            assert len(labels) == len(table)                 # check that number of rows is correct

            for i in range(len(table)):
                assert len(table[i]) == len(labels)          # check that number of columns is correct
                for j in range(len(table[i])):
                    if table[i][j] == 0:                     # skip if have 0 entries
                        continue
                    delay = table[i][j] / 2 
                    delay_list.append(delay)
                    # #print('delay',node.name,delay_list)                 # divide RT time by 2
                    cchannel_params = {"delay": delay, "distance": 1e3}
                    # #print('Labels',labels[i],labels[j])
                    self.add_classical_channel(labels[i], labels[j], **cchannel_params)

        # create qconnections (two way quantum channel)
        # #print('Adding q connection')
        if "qconnections" in config:
            for qchannel_params in config["qconnections"]:
                node1 = qchannel_params.pop("node1")
                node2 = qchannel_params.pop("node2")
                # #print('qconnection',node1,node2)
                self.add_quantum_connection(node1, node2, **qchannel_params)
        
        # create qchannels
        if "qchannels" in config:
            for qchannel_params in config["qchannels"]:
                node1 = qchannel_params.pop("node1")
                node2 = qchannel_params.pop("node2")
                # #print('qchannels',node1,node2)
                self.add_quantum_channel(node1, node2, **qchannel_params)

        # generate forwarding tables
        #-------------------------------
        all_pair_dist, G = self.all_pair_shortest_dist()
        # #print('all pair distance', all_pair_dist, G)
        self.nx_graph=G
        # #print('self.nx_graph',self.nx_graph,self.name)
        
        #-------------------------------
        
        for node in self.nodes.values():
            # #print('nodes',type(node))
            if type(node) != BSMNode:
                node.all_pair_shortest_dist = all_pair_dist
                node.nx_graph=self.nx_graph
                node.delay_graph=self.cc_delay_graph
                # #print('delay graph',node.name)
                node.neighbors = list(G.neighbors(node.name))
            if type(node) == EndNode:
                # #print('Add service node',config['end_node'])
                for key, value in config['end_node'].items():
                    # #print('end node key value',node.name, key, value )
                    if node.name == key:
                        # #print('check', node.name, key, value)
                        node.service_node = value
                        break
            if type(node) ==  ServiceNode:
                for key, value in config['end_node'].items():
                    if node.name == value:
                        node.end_node =key
                        break
                # #print('service noce end node',node.end_node)
                        
                # for key,value in config.items():
                #     #print('end node params',key,value)
                #     if node.name in params:
                #         node.service_node = params
                #         break
        
        # for node in self.get_nodes_by_type("QuantumRouter"):
        #     #-----------------------------------------------
        #     node.all_pair_shortest_dist = all_pair_dist
        #     node.nx_graph=self.nx_graph
        #     node.delay_graph=self.cc_delay_graph
        #     # #print('delay graph',node.delay_graph)
        #     node.neighbors = list(G.neighbors(node.name))
        #     # #print('kkkkkkk',node.name,node.neighbors)
        #     key=node.name
        #     # node.all_neighbor[key]=node.neighbors
        #     for items in node.neighbors:
        #         node.all_neighbor.setdefault(key,{})[node.name]=items
            #-----------------------------------------------
            # table = self.generate_forwarding_table(node.name)
            # for dst, next_node in table.items():
            #     node.network_manager.protocol_stack[0].add_forwarding_rule(dst, next_node)
               
    def add_node(self, node: "Node") -> None:
        """Method to add a node to the network.
        Args:
            node (Node): node to add.
        """

        self.nodes[node.name] = node
        self.graph[node.name] = {}
        if type(node) != BSMNode:
            self.graph_no_middle[node.name] = {}
        self._cc_graph[node.name] = {}
        self.cc_delay_graph[node.name]={}

    def add_quantum_connection(self, node1: str, node2: str, **kwargs) -> None:
        kwargs["distance"] =  float(kwargs["distance"])
        # print('add quantum connection', node1, node2)
        assert node1 in self.nodes, node1 + " not a valid node"
        assert node2 in self.nodes, node2 + " not a valid node"

        if ((type(self.nodes[node1]) == EndNode) and (type(self.nodes[node2]) == EndNode) or 
            (type(self.nodes[node1]) == EndNode) and (type(self.nodes[node2]) == ServiceNode) or
            (type(self.nodes[node1]) == ServiceNode) and (type(self.nodes[node2]) == EndNode) or
            (type(self.nodes[node1]) == ServiceNode) and (type(self.nodes[node2]) == ServiceNode)):
            
            #Add direct channel between node1 and node2
            #Since these are one way channels we add another channel from node2 to node1
            self.add_quantum_channel(node1, node2, **kwargs)
            self.add_quantum_channel(node2, node1, **kwargs)
            
            # update non-middle graph
            self.graph_no_middle[node1][node2] = float(kwargs["distance"])
            self.graph_no_middle[node2][node1] = float(kwargs["distance"])

            # add middle node
            name_middle = "_".join(["middle", node1, node2])
            middle = BSMNode(name_middle, self.timeline, [node1, node2])
            self.add_node(middle)

            # update distance param
            print("type:", type(kwargs["distance"]))
            kwargs["distance"] = float(kwargs["distance"]) / 2

            # add quantum channels
            for node in [node1, node2]:
                # #print('node kwrgs',node,name_middle,kwargs)
                self.add_quantum_channel(node, name_middle, **kwargs)

            # update params
            del kwargs["attenuation"]
            if node1 in self._cc_graph and node2 in self._cc_graph[node1]:
                # print('node1 node2', node1, node2, self._cc_graph[node1][node2])
                temp1=self._cc_graph[node1][node2] 
                temp2= self._cc_graph[node2][node1]
                kwargs["delay"] = (temp1 + temp2) / 4
                # print('kwargs delay', kwargs["delay"])

            # add classical channels (for middle node connectivity)
            for node in [node1, node2]:
                self.add_classical_connection(name_middle, node, **kwargs)

        else:
            # #print('Node1 node2',node1, node2)
            self.add_quantum_channel(node1, node2, **kwargs)
            self.add_quantum_channel(node2, node1, **kwargs)

    def add_quantum_channel(self, node1: str, node2: str, **kwargs) -> None:
        kwargs["distance"] =  float(kwargs["distance"])
        """Method to add a one-way quantum channel connection.
        NOTE: kwargs are passed to constructor for quantum channel, may be used to specify channel parameters.
        Args:
            node1 (str): first node in pair to connect (sender).
            node2 (str): second node in pair to connect (receiver).
        """

        name = "_".join(["qc", node1, node2])
        qchannel = QuantumChannel(name, self.timeline, **kwargs)
        qchannel.set_ends(self.nodes[node1], self.nodes[node2])
        self.qchannels.append(qchannel)

        # edit graph
        self.graph[node1][node2] = float(kwargs["distance"])
        if type(self.nodes[node1]) != BSMNode and type(self.nodes[node2]) != BSMNode:
            self.graph_no_middle[node1][node2] = float(kwargs["distance"])

    def add_classical_connection(self, node1: str, node2: str, **kwargs) -> None:
        """Method to add a two-way classical channel between nodes.
        NOTE: kwargs are passed to constructor for classical channel, may be used to specify channel parameters.
        Args:
            node1 (str): first node in pair to connect.
            node2 (str): second node in pair to connect.
        """

        self.add_classical_channel(node1, node2, **kwargs)
        self.add_classical_channel(node2, node1, **kwargs)

    def add_classical_channel(self, node1: str, node2: str, **kwargs) -> None:
        """Method to add a one-way classical channel between nodes.
        NOTE: kwargs are passed to constructor for classical channel, may be used to specify channel parameters.
        Args:
            node1 (str): first node in pair to connect.
            node2 (str): second node in pair to connect.
        """
        # #print('add classical',node1,node2,self.nodes)
        assert node1 in self.nodes and node2 in self.nodes

        name = "_".join(["cc", node1, node2])
        cchannel = ClassicalChannel(name, self.timeline, **kwargs)
        cchannel.set_ends(self.nodes[node1], self.nodes[node2])
        self.cchannels.append(cchannel)
        #print(" add cc channel",cchannel ,cchannel.delay)
        # edit graph
        # #print('add classical channel',node1,node2)
        self._cc_graph[node1][node2] = cchannel.delay 
        # #print('_cc_graph',self._cc_graph)
        if type(self.nodes[node1]) != BSMNode and type(self.nodes[node2]) != BSMNode:
            self.cc_delay_graph[node1][node2]=cchannel.delay
            # #print('ccdelay',self.cc_delay_graph)

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        return [node for name, node in self.nodes.items() if type(node).__name__ == node_type]

    def generate_forwarding_table(self, starting_node: str) -> dict:
        """Method to create forwarding table for static routing protocol.
        Generates a mapping of destination nodes to next node for routing using Dijkstra's algorithm.
        Args:
            node (str): name of node for which to generate table.
        """

        # set up priority queue and track previous nodes
        nodes = list(self.nodes.keys())
        costs = {node: float("inf") for node in nodes}
        previous = {node: None for node in nodes}
        costs[starting_node] = 0

        # Dijkstra's
        while len(nodes) > 0:
            current = min(nodes, key=lambda node: costs[node])
            if type(self.nodes[current]) == BSMNode:
                nodes.remove(current)
                continue
            if costs[current] == float("inf"):
                break
            for neighbor in self.graph_no_middle[current]:
                distance = self.graph_no_middle[current][neighbor]
                new_cost = costs[current] + distance
                if new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    previous[neighbor] = current
            nodes.remove(current)

        # find forwarding neighbor for each destination
        next_node = {k: v for k, v in previous.items() if v} # remove nodes whose previous is None (starting, not connected)
        for node, prev in next_node.items():
            if prev is starting_node:
                next_node[node] = node
            else:
                while prev not in self.graph_no_middle[starting_node]:
                    prev = next_node[prev]
                    next_node[node] = prev

        return next_node

    def populate_protocols(self):
        # TODO: add higher-level protocols not added by nodes
        raise NotImplementedError("populate_protocols has not been added")

    #-----------------------------------------------
    def generate_nx_graph(self):
        G = nx.Graph()
        #print('gengph',G, G.nodes)
        for node in self.nodes.keys():

            if type(self.nodes[node]) == BSMNode:
                continue

            for neighbor in self.graph_no_middle[node]:    
                distance = self.graph_no_middle[node][neighbor]
                #print('------------node-------------', type(node))
                #print('------------neighbor-------------', self,node,neighbor)
                # self.owner.all_neighbor[node]=neighbor
                ###print('------------distance-------------', type(distance))
                G.add_node(node)                
                G.add_edge(node, neighbor, color='blue', weight=distance)  
        print("G",G, type(G))    
        return G


    # def get_cc_graph(self):
    #     return self.cc_delay_graph
    
    # def djiktras(self):
    #     G=self.generate_nx_graph()
    #     return nx.dijkstra_path(G)

    def all_pair_shortest_dist(self):
        print("Calling...")
        G = self.generate_nx_graph()
        
        print("Returned...")
        short_distance = nx.floyd_warshall(G)
        print(short_distance)
        return short_distance, G

    def get_virtual_graph(self):
        #Plotting virtual graph
        nx_graph = self.generate_nx_graph()
        #print(self.nodes.keys())
        for node in self.nodes.keys(): 
            #Check if this is middle node then skip it
            if type(self.nodes[node]) == BSMNode:
                ###print("In if-------",node)
                continue
            
            #Check the memory of this node for existing entanglements
            for info in self.nodes[node].resource_manager.memory_manager:
                
                if info.state != 'ENTANGLED':
                    ###print("Info.remote node-------------", info.remote_node)
                    continue
                else:
                    # #print('xxxx', (node, info.remote_node))
                    #This is a virtual neighbor
                    #print("Node, remote node-------",(node, info.remote_node))
                    nx_graph.add_edge(node, str(info.remote_node), color='red')
        print('before draw')
        self.draw_graph(nx_graph)
        print('after draw')
        return nx_graph


    def draw_graph(self,networkx_graph):
        pyviz_graph=Network('500px', '500px')
        pyviz_graph.from_nx(networkx_graph)
        """for node in networkx_graph.nodes:
            pyviz_graph.add_node(str(node))
        for source,target,attri in networkx_graph.edges(data=True):
            pyviz_graph.add_edge(str(source),str(target), color=attri['color'])
            """
        pyviz_graph.write_html('drawgraph.html')
        webbrowser.open_new("drawgraph.html")
        
   
        
    def calcfidelity(self):
        fid=[]
        for node in self.nodes:
            if type(self.nodes[node]) == BSMNode:
                continue
            for info in self.nodes[node].resource_manager.memory_manager:
                if info.state == 'ENTANGLED':
                    fid.append(info.fidelity)
        avgfid=sum(fid)/len(fid)
        return avgfid


    def calctime(self,li):
        time=[]
        for pairs in li:
            src=pairs[0]
            dest=pairs[1]
            starttime=pairs[2]
            max_time=0
            latency=0
            for info in self.nodes[dest].resource_manager.memory_manager:
                if info.remote_node == src and info.entangle_time > max_time:
                    if (info.entangle_time*1e-12 - starttime) < 1:    
                        max_time = info.entangle_time*1e-12
                
            latency=max_time - starttime
            # #print('maxxx', src,dest,starttime,max_time,latency)
            time.append(latency)
        # #print('tttttt', time)
        avgtime=sum(time)/len(time)
        # #print('Average latency', avgtime)
        

    def calctime2(self, uniquenode):
        time=[]
        for node in uniquenode:
            memId=[]
            ##print('qqq',node.name)
            for ReqId,ResObj in node.network_manager.requests.items():
                if ResObj.isvirtual:
                    continue
                starttime=ResObj.start_time*1e-12
                
                ##print('Starttime', starttime,ResObj.initiator, ResObj.responder)
                if ReqId in node.resource_manager.reservation_to_memory_map.keys():
                    #memId=self.nodes[node].resource_manager.reservation_to_memory_map.get(ReqId)
                    memId=node.resource_manager.reservation_to_memory_map.get(ReqId)
                    ##print(memId)
                    maxtime=0
                    for info in node.resource_manager.memory_manager:
                        if info.index in memId and info.entangle_time > maxtime and info.entangle_time != 20 and info.state =='ENTANGLED':
                            ##print('ddd',info.entangle_time)
                            maxtime=info.entangle_time*1e-12

                    ##print('maxtime', maxtime)
                latency=maxtime-starttime
                if latency > 0 :
                    time.append(latency)
                ##print('maxxx', ResObj.initiator, ResObj.responder,starttime,latency)
        ##print('time', time)
        avgtime=sum(time)/len(time)
        # #print('Average latency',avgtime)


    def throughput(self, li):
        csuccess, cfail = 0,0
        for pairs in li:
            src=pairs[0]
            dest=pairs[1]
            # #print('ccc', src, dest)
            for ReqId,ResObj in self.nodes[src].network_manager.requests.items():
                #print(ResObj.initiator, ResObj.responder)
                if src == ResObj.initiator:
                    #for ReqId,ResObj in self.nodes[dest].network_manager.requests.items():
                    if dest == ResObj.responder:
                        csuccess +=1
                        break 
                else:
                    cfail +=1
            """for info in self.nodes[src].resource_manager.memory_manager:
                if info.remote_node == dest:
                    #print('ssss')
                else:
                    #print('dddd')"""

        # #print('Success/Fail',csuccess,cfail)


        """
            for ReqId,ResObj in self.nodes[src].network_manager.requests.items():
                if ReqId in self.nodes[src].resource_manager.reservation_to_memory_map.keys():
                    for info in self.nodes[src].resource_manager.memory_manager:
                        if info.remote_node == ResObj.responder:
                            csuccess +=1
                        else:
                            cfail +=1
            #print('ratio',csuccess,cfail)
        """
        """
        for node in uniquenode:
            for ReqId,ResObj in node.network_manager.requests.items():
                if ReqId in node.resource_manager.reservation_to_memory_map.keys():
                    for info in node.resource_manager.memory_manager:
                        if info.remote_node == ResObj.responder:
                            #print('ddddd', info.remote_node, ResObj.responder)"""



        """
        for node in uniquenode:
            for info in node.resource_manager.memory_manager:
                if info.remote_node == node.network_manager.requests.ResObj.responder:
                    #print('Swap succesful')"""



"""def plot_graph(self, nx_graph):
        colors = nx.get_edge_attributes(nx_graph,'color').values()
        ###print("Colors",colors)
        weights = nx.get_edge_attributes(nx_graph,'weight').values()
        nx.draw(nx_graph, edge_color=colors, with_labels = True)
        #nx.draw(nx_graph,with_labels=True)
        plt.show(graph.html)
"""
    #------------------------------------------------
"""
        colors = nx.get_edge_attributes(nx_graph,'color').values()
        weights = nx.get_edge_attributes(nx_graph,'weight').values()
        nx.draw(nx_graph, edge_color=colors, with_labels = True)
"""