"""Definition of Routing protocol.

This module defines the StaticRouting protocol, which uses a pre-generated static routing table to direct reservation hops.
Routing tables may be created manually, or generated and installed automatically by the `Topology` class.
Also included is the message type used by the routing protocol.
"""

from enum import Enum,auto
from platform import node
from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from ..topology.node import Node 
    from ..topology.topology import Topology
    from ..kernel._event import Event
    


import matplotlib.pyplot as plt
import networkx as nx
from ..message import Message
from ..protocol import StackProtocol
from .reservation import RSVPMsgType,ResourceReservationMessage
import json
import math
from ..kernel._event import Event

from ..topology.message_queue_handler import ManagerType, ProtocolType,MsgRecieverType

class UpdateRoutingMessageType(Enum):
    UPDATE_ROUTING_TABLE=auto()
# add msg type
class UpdateRoutingMessage(Message):
    def __init__(self, msg_type: UpdateRoutingMessageType, receiver,node,vneighbors):
        super().__init__(msg_type, receiver)
        self.protocol_type=RoutingTableUpdateProtocol
        # #print('Update routing message',self.receiver,node,vneighbors)
        self.vneighbors=vneighbors

class Message():
    def __init__(self, receiver_type : Enum, receiver : Enum, msg_type , **kwargs):
        self.receiver_type =receiver_type
        self.receiver = receiver
        self.msg_type = msg_type
        self.kwargs = kwargs
    
class StaticRoutingMessage(Message):
    """Message used for communications between routing protocol instances.

    Attributes:
        msg_type (Enum): type of message, required by base `Message` class.
        receiver (str): name of destination protocol instance.
        payload (Message): message to be delivered to destination.
    """
    
    def __init__(self, msg_type: Enum, receiver: str, payload: "Message"):
        super().__init__(msg_type, receiver)
        self.payload = payload
        self.skip=[]
        # if self.msg_type==RoutingMessageType.UPDATE_ROUTING_TABLE:
        #     # virtual neighbor self.own.virtualneighbors
        #     #print('self.own.virtualneighbors',self.own.virtualneighbors)
# class RoutingUpdateMessage(Message):

#     def __init__(self, msg_type: Enum, sender: str):
#         super().__init__(msg_type, receiver)

class StaticRoutingProtocol(StackProtocol):
    """Class to route reservation requests.

    The `StaticRoutingProtocol` class uses a static routing table to direct the flow of reservation requests.
    This is usually defined based on the shortest quantum channel length.

    Attributes:
        own (Node): node that protocol instance is attached to.
        name (str): label for protocol instance.
        forwarding_table (Dict[str, str]): mapping of destination node names to name of node for next hop.
    """
    
    def __init__(self, own: "Node", name: str, forwarding_table: Dict):
        """Constructor for routing protocol.

        Args:
            own (Node): node protocol is attached to.
            name (str): name of protocol instance.
            forwarding_table (Dict[str, str]): forwarding routing table in format {name of destination node: name of next node}.
        """

        super().__init__(own, name)
        self.forwarding_table = forwarding_table

    def add_forwarding_rule(self, dst: str, next_node: str):
        """Adds mapping {dst: next_node} to forwarding table."""

        assert dst not in self.forwarding_table
        self.forwarding_table[dst] = next_node
        ###print('----------Next Hop-------------', next_node)

    def update_forwarding_rule(self, dst: str, next_node: str):
        """updates dst to map to next_node in forwarding table."""

        self.forwarding_table[dst] = next_node
        ###print('----------Next Hop-------------', next_node)

    def push(self, dst: str, msg: "Message"):
        """Method to receive message from upper protocols.

        Routing packages the message and forwards it to the next node in the optimal path (determined by the forwarding table).

        Args:
            dst (str): name of destination node.
            msg (Message): message to relay.

        Side Effects:
            Will invoke `push` method of lower protocol or network manager.
        """

        #Compute the next hop here using our logic
        #Pick the best possible nieghbor according to physical distance



        assert dst != self.own.name


        ###print('(dst, self.own.name) -----', (dst, self.own.name))
        #-----------##print(self.own.all_pair_shortest_dist)
        #dst = self.forwarding_table[dst]

        visited = []

        #If section will run during forward propagation
        if msg.msg_type == RSVPMsgType.REQUEST: 
            ###print('Message Info : ----------', msg.msg_type) 
            ###print('Inside Routing --------------------qcaps---------------- ', msg.qcaps[-1].node)
            ###print('type(Message) : ----------', type(msg))
                  #msg.reservation.memory_size is the demand size
            visited = [qcap.node for qcap in msg.qcaps]

            dst =  self.custom_next_best_hop(self.own.name, dst, msg.reservation.memory_size, visited)

        #Else section will run during backward propagation
        elif msg.msg_type == RSVPMsgType.APPROVE:
            ##print('path: ', msg.path)
            #Return the prevous node of current node 
            curr_ele_index = msg.path.index(self.own.name)
            #print('Back routing phase: Next node  is ----', curr_ele_index,msg.path[curr_ele_index-1])
            dst = msg.path[curr_ele_index-1]        

        
        new_msg = StaticRoutingMessage(Enum, self.name, msg)
        
        ###print('--------------self.own.name------------', self.own.name)
        ###print('--------------dst------------', dst)
        self._push(dst=dst, msg=new_msg)

    #--------------------------------------------------
    def custom_next_best_hop(self, curr_node, dest, demand, visited):
        
        #if curr_node == dest:
        #    return dest

        if (curr_node == 'm' and dest == 'l') or (curr_node == 'm' and dest == 'g'):
            return 'h'

        is_next_virtual = True
        all_pair_path = self.own.all_pair_shortest_dist
        # #print('all pair path',all_pair_path)
        neighbors = self.own.neighbors
        # #print('neighbours',self.own.name,neighbors)
        
        virtual_neighbors = self.own.find_virtual_neighbors()
        #if curr_node == 'h':
        #    ##print('virtual_neighbors: ', virtual_neighbors)

        nodewise_dest_distance = all_pair_path[dest]
        nodewise_dest_distance = json.loads(json.dumps(nodewise_dest_distance))

        ###print('Demand: --------------- ', demand)
    
        
        #Greedy Step:
        #Pick the virtual neighbor that is closest to the destination
    
        least_dist = math.inf
        best_hop = None
        ###print('Current Node: ', curr_node)
        for node in nodewise_dest_distance:
            ###print((node,neighbor_dict[node]))
            if (node in virtual_neighbors.keys()) or (node in neighbors):
                ###print('Virtual neighbor found: ', node)
                dist = nodewise_dest_distance[node]
                if dist < least_dist:
                    best_hop = node
                    least_dist = dist

        """if best_hop != None:
            ##print('virtual_neighbors[best_hop] --------------- ', virtual_neighbors[best_hop])"""
        #If such a virtual neighbor does not exist or cannot satisfy our demands then pick 
        #the best physical neighbor and generate entanglements through it
        #Or if we pick an already traversed neighbor
        
        ###print('Visited ----------------------', visited)
        best_hop_virtual_link_size = 0
        if best_hop in virtual_neighbors:
            best_hop_virtual_link_size = virtual_neighbors[best_hop]

        if best_hop == None or  best_hop_virtual_link_size < demand or ( best_hop in visited):
            is_next_virtual = False
            """##print('Dist Matrix for destination node(',dest,') :  ')
            ##print(nodewise_dest_distance)
            ##print('Neighbors of current node(',curr_node,'):  ', neighbors)"""
            for node in nodewise_dest_distance:
                ###print((node,neighbor_dict[node]))
                if node in neighbors:
                    dist = nodewise_dest_distance[node]
                    if dist < least_dist:
                        best_hop = node
                        least_dist = dist


        
        # #print()
        # #print('---------Next Hop Calculation using Modified Greedy------------')
        # #print('Curr Node: ', curr_node,', picked neighbor: ', best_hop, ', distance b/w picked neighbor and destination ', least_dist)
        
        """##print('Virtual Neighbors of current node: ', self.own.find_virtual_neighbors())
        ##print('---------------------------------------------------------------')
        ##print()"""


        return best_hop
    #--------------------------------------------------

    def pop(self, src: str, msg: "StaticRoutingMessage"):
        """Message to receive reservation messages.

        Messages are forwarded to the upper protocol.

        Args:
            src (str): node sending the message.
            msg (StaticRoutingMessage): message received.

        Side Effects:
            Will call `pop` method of higher protocol.
        """

        self._pop(src=src, msg=msg.payload)

    def received_message(self, src: str, msg: "Message"):
        """Method to directly receive messages from node (should not be used)."""

        raise Exception("RSVP protocol should not call this function")

    def init(self):
        pass

class NewRoutingProtocol(StackProtocol):
    """Class to route reservation requests.

    
    Attributes:
        own (Node): node that protocol instance is attached to.
        name (str): label for protocol instance.
        
    """
    
    def __init__(self, own: "Node", name: str):
        """Constructor for routing protocol.

        Args:
            own (Node): node protocol is attached to.
            name (str): name of protocol instance.
            
        """

        super().__init__(own, name)
        
        self.local_neighbor_table={}  # Dictionary with key:node, value:{neighbor:distance}
    


    def setattributes(self,curr_node):
        '''Method to set the local neighborhood, distances, physical graphs and virtual link information'''
        
        """
        nodewise_dest_distance: dictionary of distance of a node with other nodes of the topology
        neighbors,vneighbors and nx_graph are attributes of node class.
        """

        all_pair_path = self.own.all_pair_shortest_dist
        all_pair_path=json.loads(json.dumps(all_pair_path))
        nodewise_dest_distance = all_pair_path[curr_node]
        nodewise_dest_distance = json.loads(json.dumps(nodewise_dest_distance))
        neighbors = self.own.neighbors
        vneighbors=self.own.virtualneighbors
        # #print('virtual neighbors',vneighbors,self.own.timeline.now()*1e-12)
        G=self.own.nx_graph
        # #print('nx graph',self.own.nx_graph)
        """
        The code below is used to populate local_neighbor_table.
        We iterate through the neighbors of node. If that node exist in the nodewise_dest_distance, if it a virtual link we assign distance as 0, else we assign the distance from the nodewise_dest_distance between those nodes.
        """
        for n_nodes in neighbors:
            key=self.own.name
            for node,dist in nodewise_dest_distance.items():  
                if n_nodes==node:  
                    if node in vneighbors:
                        self.local_neighbor_table.setdefault(key,{})[node]=0
                        G.add_edge(key,node,color='red',weight=dist)
                    else:    
                        self.local_neighbor_table.setdefault(key,{})[node]=dist
                    break  
        # #print('Local Neighbor Table',self.local_neighbor_table)
    
    '''
    Old function to generate graph. Now we obtain the physical graph from the topology.

    def generate_graph(self):
        G=self.own.nx_graph
        # #print('local table',self.local_neighbor_table)
        # for node, neighbor in self
        # .local_neighbor_table.items():
        #     # #print('aa',node, neighbor,G.nodes,G.edges)
        #     if node not in G.nodes:
        #         # #print('nodes',node)
        #         G.add_node(node)
        #         # #print('gnode',G.nodes)
        #         for neighnode,dist in neighbor.items():
        #             # #print('bb',neighnode,dist)
        #             G.add_edge(node,neighnode,color='red',weight=dist)
        #         # #print('gedge',G.edges)
        # #print('Gnodes',G.nodes,G.edges)
        # for node1, value in self.own.all_pair_shortest_dist.items():
        #     # #print('apsd',node1,value)
        #     for node2,dist in value.items():
        #         # #print('aspd',node1,node2,dist,G.nodes,G.edges)
        #         if node1 not in G.nodes:
        #             # #print('new nodes',self.own.name,node1,node2,dist,G.nodes,G.edges,self.own.neighbors)
        #             G.add_node(node1)
        #         if (node1,node2) not in G.edges and node1 != node2 and node1 in self.own.neighbors:
        #             # #print('edge2', node1, node2,self.own.neighbors)
        #             G.add_edge(node1,node2,color='red',weight=dist)
        # # nx.draw(G, labels=labels, with_labels=True)
        # plt.savefig('ggg.png')
        #print('gnodes,gedges', G.nodes , G.edges)
        #print(G)
        return G

    '''
    def received_message(self, src: str, msg: "Message"):
        return super().received_message(src, msg)

    def push(self, dst: str, msg: "Message"):
        """Method to receive message from upper protocols.

        Routing packages the message and forwards it to the next node in the optimal path (determined by Dijkstas' algorithm).

        Args:
            dst (str): name of destination node.
            msg (Message): message to relay.

        Side Effects:
            Will invoke `push` method of lower protocol or network manager.
        """

        #Compute the next hop here using our logic
        #Pick the best possible nieghbor according to physical distance
        # #print('--------------self.own.name------------', self.own.name,self.own.neighborhood_list)
        


        assert dst != self.own.name

        #If section will run during forward propagation
        
        if msg.msg_type == RSVPMsgType.REQUEST: 
            self.setattributes(self.own.name)  # Set attributes for the current node
           
            G=self.own.nx_graph
            skip=[]
            if self.own.name == msg.reservation.initiator:
                path=nx.dijkstra_path(G,self.own.name,dst) 
                '''We initially calculate the temporary path using Dijkstra's algorithm.'''

                # #print('lll',path,msg.reservation)
                # for node in path:
                #     if node!= self.own.name and node!=dst:
                #         skip.append(node)
                # #print('kklk',skip,path[1])
                # msg= ResourceReservationMessage(RSVPMsgType.REQUEST, self.name, msg.reservation,temp_path=path)
                ''' We append this temporary path to message class temporary path'''
                msg.temp_path=path
               
                '''
                Marker node: The end node of the the local neighborhood which lies in the temp path.
                We iterate through the temp path, then through the neighborhood_list, and check if the node in the temp path lies in the neighborhood_list.
                we add this marker node to the msg.
                '''
                for items in msg.temp_path:
                    # #print('items',items,self.own.neighborhood_list)
                    # self.own.marker=items
                    msg.marker=items
                    if self.own.neighborhood_list:
                        for nodes in self.own.neighborhood_list:
                            if nodes==items:
                                msg.marker=nodes
                self.own.message_handler.send_message(path[1],msg)
            # #print('Message Info msg.path: ----------', self.own.name,msg.temp_path,self.own.neighborhood_list) 
            # #print('marker node',msg.marker,self.own.name)


            indexx=msg.temp_path.index(self.own.name)
            # #print('indx',self.own.name,indexx,len(msg.temp_path))

            # If the node is the first node in the temp path, we run the next_hop method, which gives us the next node using Djisktr's algorithm
            
            if self.own.name == msg.temp_path[0]:
                dst=self.next_hop(self.own.name,msg.temp_path[-1])
                
            # If the node is the marker node we do the routing again by calling next_hop method
            elif self.own.name == msg.marker:
                # #print('At marker node',self.own.name,self.own.marker)
                dst=self.next_hop(self.own.name,msg.temp_path[-1])

            #If the node is not the source, marker or end node, we skip the routing.
            elif indexx > 0 and indexx < len(msg.temp_path)-1:
                dst=msg.temp_path[indexx+1]
                # #print('mddle',self.own.name,dst,indexx)
                
            #For end node
            elif indexx==len(msg.temp_path)-1:
                # #print('last node')
                dst=msg.temp_path[-1]
                
        #Else section will run during backward propagation
        elif msg.msg_type == RSVPMsgType.APPROVE:
            # #print('path11: ', msg.path)
            #Return the prevous node of current node 
            curr_ele_index = msg.path.index(self.own.name)
            # #print('Back routing phase: Next node  is ----', curr_ele_index,msg.path[curr_ele_index-1])
            dst = msg.path[curr_ele_index-1]        
            # #print('dst',dst)
        


        
        new_msg = StaticRoutingMessage(Enum, self.name, msg)
        # #print('routing msg enum',Enum,self.own.name,dst,new_msg)
       
        self._push(dst=dst, msg=new_msg)

    def next_hop(self,src,dest):
        # This function will give the next hop of the Dijkstra's path.

        G=self.own.nx_graph
        path=nx.dijkstra_path(G,src,dest)
        # #print('dijkstas path',path,path[1],path[-1])
      
        return path[1]
        
    def pop(self, src: str, msg: "StaticRoutingMessage"):
        """Message to receive reservation messages.

        Messages are forwarded to the upper protocol.

        Args:
            src (str): node sending the message.
            msg (StaticRoutingMessage): message received.

        Side Effects:
            Will call `pop` method of higher protocol.
        """

        self._pop(src=src, msg=msg.payload)


class RoutingTableUpdateProtocol(NewRoutingProtocol):

    def __init__(self,owner,name):
        self.own=owner
        self.name='RoutingTableUpdateProtocol'
        self.update_time=1e9  # Time interval at which this protocol will be called
        self.vlink_data={}
        self.prev_vdata = None

    def find_neighbors(self):
        '''
        This method is used to calculate the local neighborhood of a node.
        We get the delay from the topology and we check if that delay is less than the update time. If it is less we append it to the neighborhood_list. If more it lies outside of the neighborhood circle.
        '''
        # #print('dgraph',self.own.name,self.update_time,self.own.delay_graph)
        neighborhood_list=[]
        for node,dest_delay in self.own.delay_graph.items():
            if self.own.name == node:
                for dst,delay in dest_delay.items():
                    # #print('dddf',delay*1e-12,self.update_time*1e-12)
                    if delay<self.update_time:
                        # #print('findneighbors',node,dst)
                        neighborhood_list.append(dst)
        self.own.neighborhood_list=neighborhood_list
        return neighborhood_list

    def sendmessage(self):
        '''
        Method to send message to all the nodes in the graph with the virtual link information.
        '''
        neighbors=self.own.neighbors
        G=self.own.nx_graph
        neighbor_list=self.find_neighbors()
        
        #Issue: Routing message being sent to all nodes instead of just neighbors
        for node in G.nodes:
            if node != self.own.name:
                if self.prev_vdata != self.own.virtualneighbors:
                    msg=Message(MsgRecieverType.PROTOCOL,ProtocolType.RoutingTableUpdateProtocol,UpdateRoutingMessageType.UPDATE_ROUTING_TABLE,node=node,v_neighbor=self.own.virtualneighbors)
                    self.own.message_handler.send_message(node,msg)
                    self.prev_vdata = self.own.virtualneighbors

        for node in self.own.nx_graph:
            # #print('edges',self.own.nx_graph.edges)
            # if self.own.virtualneighbors:
            #     #print('nodedge',node,self.own.name,self.own.virtualneighbors)
            #     if (self.own.name,self.own.virtualneighbors[0]) in self.own.nx_graph.edges:
            #         #print('add vlink',self.own.name,self.own.virtualneighbors[0])
            #         G.add_edge(self.own.name,self.own.virtualneighbors[0],color='red',weight=0)
            #         break


            '''Add new virtual links to the network graph'''
            for nodes,link in self.vlink_data.items():
                # weight=nx.get_edge_attributes(self.own.nx_graph,'weight')
                weight=self.own.nx_graph.get_edge_data(nodes,link[0])
                G=self.own.nx_graph
                weight=self.own.nx_graph[nodes][link[0]]['weight']
                # #print('node,link',nodes,link[0],weight)
                if (nodes,link[0]) in self.own.nx_graph.edges and weight == 0:
                    break
                else:
                    # #print('add vlink',nodes,link[0])
                    self.own.nx_graph.add_edge(nodes,link[0],color='red',weight=0)
                    break


        # neighborhood_time=1e12 1/10 of second
        # neighborhood_time=1e12
        #process = Process(self, "sendmessage",[])
        #event = Event(self.update_time+self.own.timeline.now(), process)
        event = Event(self.update_time+self.own.timeline.now(), self, "sendmessage",[])
        #self.own.timeline.schedule(event)
        self.own.timeline.schedule_counter += 1
        self.own.timeline.events.push(event)
        self.vlink_data={}
        # #print("--end of send message func in rtup----")


    def received_message(self,src,msg: Message):
        # #print('received message2',src,msg.vneighbors,self.own.timeline.now()*1e-12)
        # vlink_data={}
        if msg.msg_type is UpdateRoutingMessageType.UPDATE_ROUTING_TABLE:
            # #print('received message1',msg.vneighbors)
            key=src
            vneighbors=msg.kwargs.get('v_neighbor')
            if vneighbors:
                # #print('not empty',src,msg.vneighbors,self.own.timeline.now()*1e-12)
                # vlink_data[src].append(msg.vneighbors)
                self.vlink_data[src]=msg.vneighbors
        
        # if self.vlink_data:
        #     #print('hjhj',self.vlink_data,self.own.timeline.now()*1e-12)