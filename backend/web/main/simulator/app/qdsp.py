import time
from typing import Dict

import numpy as np
from qntsim.communication import ErrorAnalyzer, Network, to_binary, to_string
from qntsim.components.photon import Photon
from qntsim.components.waveplates import HalfWaveplate
from qntsim.kernel.timeline import Timeline
from qntsim.topology.node import EndNode
from qntsim.topology.topology import Topology
from qntsim.utils.encoding import polarization


def qdsp(topology:Dict, app_settings:Dict):
    response = {}
    message1 = app_settings.get("sender").get("message")
    message2 = app_settings.get("receiver").get("message")
    start_time = time.time()
    _is_binary, messages = to_binary(messages=[message1, message2])
    simulator = Timeline(stop_time=app_settings.get("stoptime", 10e12), backend=app_settings.get("backend", "Qutip"))
    configuration = Topology(name="qdsp", timeline=simulator)
    configuration.load_config_json(config=topology)
    src_node:EndNode = configuration.nodes.get(app_settings.get("sender").get("node"))
    dst_node:EndNode = configuration.nodes.get(app_settings.get("receiver").get("node"))
    initial_states = np.random.randint(4, size=len(messages[0]))
    basis = polarization.get("bases")
    _quantum_state = {0:basis[0][0],
                      1:basis[0][1],
                      2:basis[1][0],
                      3:basis[1][1]}
    photons = [Photon(name=state, quantum_state=_quantum_state[state]) for state in initial_states]
    hwp = HalfWaveplate(name=np.pi/2, timeline=simulator)
    for photon, msg in zip(photons, messages[0]):
        src_node.send_qubit(dst=dst_node.name, qubit=hwp.apply(qubit=photon) if int(msg) else photon)
    photons = dst_node.receive_qubit(src=src_node.name)
    results = [Photon.measure(basis=basis[photon.name//2], photon=hwp.apply(qubit=photon) if int(msg) else photon) for photon, msg in zip(photons, messages[1])]
    strings = ["".join([str(result^int(char)) for result, char in zip(results, message)]) for message in messages]
    recv_msgs = to_string(strings=strings, _was_binary=_is_binary)
    network = Network(topology=topology, messages={(app_settings.get("sender").get("node"), app_settings.get("receiver").get("node")):messages[0], (app_settings.get("receiver").get("node"), app_settings.get("sender").get("node")):messages[1]}, require_entanglement=False)
    network._strings = strings
    _, _, err_prct, err_sd, info_lk, msg_fidelity = ErrorAnalyzer._analyse(network=network)
    end_time = time.time()
    app_settings.update(output_msg=recv_msgs[0], avg_err=err_prct, std_dev=err_sd, info_leak=info_lk, msg_fidelity=msg_fidelity)
    response["application"] = app_settings
    from main.simulator.topology_funcs import network_graph
    response = network_graph(network_topo=configuration, source_node_list=[src_node.name], report=response)
    response["performance"]["execution_time"] = end_time - start_time

    return response