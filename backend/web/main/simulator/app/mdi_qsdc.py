import math
from typing import Dict, List
from random import shuffle
from numpy.random import randint

from qntsim.components.circuit import QutipCircuit
from qntsim.communication.network import Network

messages = {1:'hi'}

def bsm_circuit():
    qtc = QutipCircuit(2)
    qtc.cx(0, 1)
    qtc.h(0)
    qtc.measure(0)
    qtc.measure(1)
    
    return qtc

def random_encode_photons(network:Network):
    node = network.net_topo.nodes['n1']
    manager = network.manager
    basis = {}
    for info in node.resource_manager.memory_manager:
        if info.state=='RAW':
            key = info.memory.qstate_key
            base = randint(4)
            basis.update({key:base})
            q, r = divmod(base, 2)
            qtc = QutipCircuit(1)
            if r: qtc.x(0)
            if q: qtc.h(0)
            manager.run_circuit(qtc, [key])
        if info.index==2*(network.size+75): break
    
    return network, basis

def authenticate_party(network:Network, basis:Dict[int, int]):
    manager = network.manager
    node = network.net_topo.nodes['n1']
    keys = [info.memory.qstate_key for info in node.resource_manager.memory_manager[:2*network.size+150]]
    keys1 = keys[network.size-25:network.size]
    keys1.extend(keys[2*network.size:2*network.size+75])
    shuffle(keys1)
    keys2 = keys[2*network.size-25:2*network.size]
    keys2.extend(keys[2*network.size+75:])
    shuffle(keys2)
    # print(keys1)
    # print(keys2)
    all_keys = []
    outputs = []
    for keys in zip(keys1, keys2):
        all_keys.append(keys)
        outputs.append(manager.run_circuit(bsm_circuit(), list(keys)))
    err, counter = 0, 0
    for output in outputs:
        (key1, key2) = tuple(output.keys())
        base1 = basis.get(key1)
        base2 = basis.get(key2)
        out1 = output.get(key1)
        out2 = output.get(key2)
        if base1!=None!=base2 and base1//2==base2//2:
            counter+=1
            if (out1 if base1//2 else out2)!=(base1%2)^(base2%2): err+=1
    # print(err/counter*100)
    
    return network, err/counter*100

def swap_entanglement(network:Network):
    node = network.net_topo.nodes['n1']
    manager = network.manager
    keys = [info.memory.qstate_key for info in node.resource_manager.memory_manager[:2*network.size]]
    ent_keys = []
    for keys in zip(keys[:network.size-25], keys[network.size:2*network.size-25]):
        states = manager.get(keys[0]), manager.get(keys[1])
        e_keys = [k for key, state in zip(keys, states) for k in state.keys if k!=key]
        ent_keys.append(e_keys)
        output = manager.run_circuit(bsm_circuit(), keys=list(keys))
        cond = True
        # for e_key, key in zip(e_keys, )
        print(keys, e_keys, output)
        for key, e_key in zip(keys, e_keys):
            value = output.get(key)
            qtc = QutipCircuit(1)
            if cond and value:
                qtc.z(0)
            elif value:
                qtc.x(0)
            cond = False
        manager.run_circuit(qtc, [e_key])
    return network, ent_keys

def get_ent_keys(network:Network, node_name:str):
    node = network.net_topo.nodes[node_name]
    ent_keys = []
    for info in node.resource_manager.memory_manager:
        key = info.memory.qstate_key
        state = network.manager.get(key=key)
        if len(state.keys)>1: ent_keys.append(state.keys)
    
    return ent_keys

# def encode(network:Network):
#     nodes = network.network.nodes
    

# e_keys = swap_entanglement(network=network)
# network.dump(info_state='ENTANGLED')
# print(e_keys)

# Network.superdense_code(network_obj=network, message=0, node=0)
# network.dump('')

# topology = '/code/web/configs/3node.json'
# network = Network(topology=topology,
#                   messages=messages,
#                   label='00',
#                   size=lambda x: x//2+25)
# network.dump('n1', 'ENTANGLED')
# network, basis = random_encode_photons(network=network)
# network, error = authenticate_party(network=network, basis=basis)
# print(error)
# network, ent_keys = swap_entanglement(network=network)
# # network.dump(node_name='n0')
# # network.dump(node_name='n1')
# # ent_keys = get_ent_keys(network=network, node_name='n0')
# print(len(ent_keys))

# def superdense_code(network:Network, ent_keys:List):
#     manager = network.manager
#     message = network.bin_msgs[0]
#     for keys, char0, char1 in zip(ent_keys, message[::2], message[1::2]):
#         key = min(keys)
#         qtc = QutipCircuit(1)
#         if int(char1): qtc.x(0)
#         if int(char0): qtc.z(0)
#         manager.run_circuit(qtc, [key])
#         key = max(keys)
#         qtc = QutipCircuit(1)
#         if randint(2): qtc.z(0)
#         manager.run_circuit(qtc, [key])
    
#     return network

# network = superdense_code(network=network, ent_keys=ent_keys)
# network.dump(node_name='n0', info_state='ENTANGLED')
# # network.dump(node_name='n2')

# def decode(network:Network, ent_keys:List):
#     manager = network.manager
#     outputs = [manager.run_circuit(bsm_circuit(), keys=keys) for keys in ent_keys]
#     print(network.bin_msgs, outputs)

# decode(network=network, ent_keys=ent_keys)