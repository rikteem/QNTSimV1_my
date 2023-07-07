import importlib
import math
import time
from collections.abc import Iterable
from contextlib import nullcontext
from enum import Enum
from pprint import pprint
from random import shuffle
from statistics import mean
from time import time
from tokenize import String
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from .app.e2e import *
from .app.e91 import *
from .app.ghz import *
from .app.ip1 import *
from .app.ip2 import ip2_run
from .app.mdi_qsdc import *
from .app.ping_pong import *
from .app.qsdc1 import *
from .app.qsdc_teleportation import *
from .app.single_photon_qd import *
from .app.teleportation import *
from .app.utils import *
from .helpers import *
from pyvis.network import Network
from qntsim.communication import Network, Protocol
from qntsim.topology.topology import Topology
from tabulate import tabulate


def display_quantum_state(state_vector):
    """
    Converts a quantum state vector to Dirac notation in qubita and returns it
    as a string.

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
                output_str += (f"({coeff.real:.3f}" if coeff.real > 0 else "(") + (
                    "+" if coeff.real > 0 and coeff.imag > 0 else "") + f"{coeff.imag:.3f}j)|"
            else:
                output_str += f"({coeff.real:.3f})|"
            output_str += basis_states[i] + "> + "
    return output_str[:-3]


def graph_topology(network_config_json):

    network_config_json, tl, network_topo = load_topology(
        network_config_json, "Qiskit")
    print('Making graph')
    graph = network_topo.get_virtual_graph()
    print(network_topo)
    return graph


def network_graph(network_topo, source_node_list, report):
    t = 0
    timel, fidelityl, latencyl, fc_throughl, pc_throughl, nc_throughl = [], [], [], [], [], []

    while t < 20:  # Pass endtime of simulation instead of 20

        fidelityl = calcfidelity(network_topo, source_node_list, t, fidelityl)
        latencyl = calclatency(network_topo, source_node_list, t, latencyl)
        fc_throughl, pc_throughl, nc_throughl = throughput(
            network_topo, source_node_list, t, fc_throughl, pc_throughl, nc_throughl)
        t += 1
        timel.append(t)
    latency, fidelity, through = 0, 0, 100
    for i in latencyl:
        if i > 0:
            latency = i
    for i in fidelityl:
        if i > 0:
            fidelity = i
    for i in fc_throughl:
        if i > 0:
            through = i
    execution_time = 3
    performance = {"latency": latency,
                   "fidelity": fidelity, "throughput": through}
    # graph["throughput"]["fully_complete"]= fc_throughl
    # graph["throughput"]["partially_complete"]= pc_throughl
    # graph["throughput"]["rejected"]= nc_throughl        #{fc_throughl,pc_throughl,nc_throughl}
    # graph["time"] = timel
    report["performance"] = performance
    print(report)
    return report


def create_response(app_name, network_config, sender, receiver, **kwargs):
    start_time = time()
    protocol, results, source_nodes = run(**kwargs, topology=network_config,
                                          sender=sender, receiver=receiver, app_name=app_name)
    end_time = time()
    execution_time = start_time-end_time
    application = [{"header": f'input_message{str(i)}', "value": message}
                   for i, message in enumerate(kwargs.get('messages', []), 1)]
    application.extend([{"header": f'output_message{str(i)}', "value": message}
                        for i, message in enumerate(results.get('messages', []), 1)])
    application.append(
        {'header': 'attack', 'value': kwargs.get('attack', 'none')})
    application.extend({'header': key, 'value': value}
                       for key, value in results.items() if key != 'messages')
    response = {'application': application}
    response = network_graph(
        protocol.networks[0]._net_topo, source_nodes, response)
    response['performance']['execution_time'] = execution_time
    return response


class APPLICATION_TYPE(Enum):
    e91 = E91
    qsdc1 = QSDC1
    ghz = GHZ
    tel = Teleportation
    pp = PingPong
    ip1 = IP1
    # qd_sp = SinglePhotonQD
    # qsdc_tel = QSDCTeleportation
    # ip2 = ip2_run


def run(app_name, **kwargs):
    topology = kwargs.get('topology')
    sender, receiver = kwargs.get('sender'), kwargs.get('receiver')
    message = kwargs.get('message')
    key_length = kwargs.get('key_length', 0)
    seq_len = kwargs.get('sequenceLength', 0)
    attack = kwargs.get('attack')
    protocol, results = Protocol(**kwargs), {"Error_Msg": "App not executed."}
    protocol.networks = [Network(topology=topology, messages=None)]
    _, tl, net_topo = load_topology(topology, "Qutip")
    trials = int(hasattr(APPLICATION_TYPE, app_name))
    match app_name:
        case 'e91':
            n = 8*key_length
            if key_length not in range(1, 30):
                return protocol, {"Error_Msg": "keyLength Should be Greater than 0 and less than 30. Retry Again."}, []
            trials = 4
        case 'qsdc1':
            key = kwargs.get('key')
            if len(key) % 2:
                return protocol, {'Error_Msg': 'Key should have even number of digits'}, []
            n = seq_len*len(key)
        case 'e2e':  # complete
            _, tl, net_topo = load_topology(
                kwargs.get('topology'), 'Qiskit')
            trans_manager = net_topo.nodes[sender].transport_manager
            trans_manager.request(sender,
                                  kwargs.get('start_time'),
                                  kwargs.get('size'),
                                  20e12,
                                  kwargs.get('priority'),
                                  kwargs.get('targetFidelity'),
                                  kwargs.get('timeout'))
            tl.init()
            tl.run()
            results, source_nodes = get_res(net_topo, [(sender, receiver)])
        case 'ghz':  # complete
            node1 = kwargs.get('endnode1')
            node2 = kwargs.get('endnode2')
            node3 = kwargs.get('endnode3')
            central_node = kwargs.get('middlenode')
        case 'tel':
            amplitude1, amplitude2 = kwargs.get(
                'amplitude1'), kwargs.get('amplitude2')
        case 'pp':
            if len(message) > 9:
                return protocol, {"Error_Msg": "Message should be less than or equal to 9."}
            n = seq_len*len(message)
        case 'ip1':
            n = 50
        case 'qd_sp' | 'qsdc_tel':
            messages = {
                (sender, receiver): message} if app_name == 'qsdc_tel' else {
                    (sender, receiver): kwargs.get('message1'),
                    (receiver, sender): kwargs.get('message1')}
            protocol = Protocol(name=app_name, messages_list=[
                                messages], attack=attack)
            messages, avg_err, avg_sd, avg_leak, avg_fid = protocol(
                topology=topology)
            results = {
                "messages": messages,
                "error": avg_err,
                "std_dev": avg_sd,
                "info_leak": avg_leak,
                "msg_fidelity": avg_fid
            }
            source_nodes = [sender]
        case 'ip2':
            alice_attrs = kwargs.get('alice_attrs')
            alice_attrs['message'] = {(sender, receiver): message}
            network, recv_msgs, err_val = ip2_run(topology=topology,
                                                  alice_attrs=alice_attrs,
                                                  bob_id=kwargs.get('bob_id'),
                                                  num_decoy_photons=kwargs.get(
                                                      'num_decoy'),
                                                  threshold=kwargs.get(
                                                      'threshold'),
                                                  attack=attack)
            protocol.networks = [network]
            results = {
                "messages": recv_msgs,
                "error": err_val[0],
                "std_dev": err_val[1],
                "info_leak": err_val[2],
                "msg_fidelity": err_val[3]
            }
            source_nodes = [sender]
        case _:
            return protocol, {"Error_Msg": "Wrong app id."}, []
    app = APPLICATION_TYPE[app_name].value() if trials else None
    match app_name:
        case 'e91' | 'qsdc1' | 'pp' | 'ip1':
            source, destination, source_nodes = app.roles(sender, receiver, n)
        case 'tel':
            source, destination, source_nodes = app.roles(sender, receiver)
        case 'ghz':
            n1, n2, n3, cn, source_nodes = app.roles(
                node1, node2, node3, central_node)
    params = [source, destination]
    while trials:
        tl.init()
        tl.run()
        match app_name:
            case 'e91': params.append(n)
            case 'qsdc1': params.extend([seq_len, key])
            case 'tel': params.extend([amplitude1, amplitude2])
            case 'pp':
                app.create_key_lists(source, destination)
                params = [seq_len, message]
            case 'ip1': params.append(message)
            case 'ghz': params = [n1, n2, n3, cn]
        # results = e91.eve_run(source, destination, n) # eve-e91
        results = app.run(*params)
        if key_length < len(results.get('sender_keys', [])):
            results['sender_keys'] = results['sender_keys'][:key_length]
            results['receiver_keys'] = results['receiver_keys'][:key_length]
            results['shifted_key_length'] = key_length
        trials -= 1
    match app_name:
        case 'e91': return protocol, {"Error_Msg": "Couldn't generate required length.Retry Again"}, []
        case 'ghz' | 'tel': results = {k: display_quantum_state(state) for k, state in results.items()}

    return protocol, results, source_nodes


def execute_protocol(app_name, *args, **kwargs):
    topology = kwargs.get('topology')
    message = kwargs.get('message')
    sender, receiver = kwargs.get('sender'), kwargs.get('receiver')
    messages = Dict[Tuple[str], str]
    if 'qsdc' in app_name:
        messages = {(sender, receiver): message}
    elif 'qd' in app_name:
        messages = {(sender, receiver): kwargs.get('message1'),
                    (receiver, sender): kwargs.get('message2')}
    protocol = Protocol(**kwargs, messages_list=messages, name=app_name)
    messages, avg_err, avg_sd, avg_leak, avg_fid = protocol(topology=topology)
    results = {
        "messages": messages,
        "error": avg_err,
        "std_dev": avg_sd,
        "info_leak": avg_leak,
        "msg_fidelity": avg_fid
    }
    source_nodes = [sender]

    return protocol, results, source_nodes
