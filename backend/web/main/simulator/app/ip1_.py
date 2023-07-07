import time
from random import randint, random
from typing import Dict

import numpy as np
from qntsim.communication import (insert_check_bits, insert_decoy_photons,
                                  to_binary, to_string)
from qntsim.communication.security_checks import __insert_seq__
from qntsim.components.photon import Photon
from qntsim.components.waveplates import Waveplate
from qntsim.kernel.timeline import Timeline
from qntsim.topology.node import EndNode
from qntsim.topology.topology import Topology
from qntsim.utils.encoding import polarization


def ip1(topology:Dict, app_settings:Dict):
    response = {}
    basis = polarization.get("bases")
    theta = np.random.randint(0, 360)
    message = app_settings.get("sender").get("message")
    start_time = time.time()
    _is_binary, messages = to_binary(messages=[message])
    simulator = Timeline(stop_time=app_settings.get("stop_time", 10e12), backend=app_settings.get("backend", "Qutip"))
    configuration = Topology(name="ip", timeline=simulator)
    configuration.load_config_json(config=topology)
    src_node:EndNode = configuration.nodes.get(app_settings.get("sender").get("node"))
    dst_node:EndNode = configuration.nodes.get(app_settings.get("receiver").get("node"))
    mod_msg = insert_check_bits(messages=messages, num_check_bits=app_settings.get("sender").get("num_check_bits"))
    photons = [Photon(name=char, quantum_state=basis[0][int(char)]) for _, message in mod_msg.items() for char in message]
    wp = Waveplate(name=theta, timeline=simulator, angle=theta)
    photons = [wp.apply(qubit=photon) for photon in photons]
    sender_id = app_settings.get("sender").get("userID")
    ida_photons = [Photon(name=basis[int(i0)][int(i1)], quantum_state=basis[int(i0)][int(i1)]) for i0, i1 in zip(sender_id[::2], sender_id[1::2])]
    receiver_id = app_settings.get("receiver").get("userID")
    r = np.random.randint(low=0, high=2, size=len(receiver_id))
    idb_photons = [Photon(name=basis[int(i0)][int(i0)^int(i1)], quantum_state=basis[int(i0)][int(i0)^int(i1)]) for i0, i1 in zip(receiver_id, r)]
    theta_photons = [Photon(name=basis[int(i0)][int(i0)^int(i1)], quantum_state=basis[int(i0)][int(i0)^int(i1)]) for i0, i1 in zip(receiver_id, bin(theta)[2:])]
    decoy_states = np.random.randint(4, size=app_settings.get("sender").get("num_decoy_photons"))
    decoy_photons = [Photon(name=basis[state//2][state%2], quantum_state=basis[state//2][state%2]) for state in decoy_states]
    ida_locs, q2 = __insert_seq__(photons, ida_photons)
    idb_locs, q3 = __insert_seq__(q2, idb_photons)
    theta_locs, q4 = __insert_seq__(q3, theta_photons)
    decoy_locs, q5 = __insert_seq__(q4, decoy_photons)
    for photon in q5:
        src_node.send_qubit(dst=dst_node.name, qubit=photon)
    photons = dst_node.receive_qubit(src=src_node.name)
    