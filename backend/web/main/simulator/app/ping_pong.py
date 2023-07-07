import logging
import random
import time
from functools import partial
from statistics import mean
from typing import Any, Dict, List

from qntsim.communication import (Network, ProtocolPipeline,
                                  bell_type_state_analyzer, pass_, to_string)
from qntsim.components.circuit import QutipCircuit
from qntsim.topology.node import EndNode

logger = logging.getLogger("main_logger.application_layer.ping_pong")

def ping_pong(topology:Dict, app_settings:Dict):
    s = time.time()
    try:
        response = {}
        start_time = time.time()
        protocol = ProtocolPipeline(
            messages_list=[
                {
                    (
                        app_settings.get("sender").get("node"),
                        app_settings.get("receiver").get("node")
                    ):app_settings.get("sender").get("message")
                }],
            encode=partial(encode, mode_switch_prob=app_settings.get("sender").get("switchProb", 0.25)),
            measure=partial(pass_), attack=app_settings.get("attack"))
        received_msgs, avg_err, std_dev, info_leak, msg_fidelity = protocol(topology=topology, size=lambda x:int(x*5*app_settings.get("sender").get("switchProb", 0.25)), require_entanglement=True, decode=partial(decode, err_threshold=app_settings.get("error_threshold", 0.54)))
        end_time = time.time()
        if "Err_msg" in received_msgs[0]:
            app_settings.update(received_msgs[0])
        else:
            app_settings.update(output_msg=received_msgs[0], avg_err=avg_err, std_dev=std_dev, info_leak=info_leak, msg_fidelity=msg_fidelity)
        response["application"] = app_settings
        print(response)
        from main.simulator.topology_funcs import network_graph
        response = network_graph(network_topo=protocol.networks[0]._net_topo, source_node_list=[app_settings.get("sender").get("node")], report=response)
        response["performance"]["execution_time"] = end_time - start_time
    except Exception:
        raise
    finally:
        e = time.time()
        print(divmod(e-s, 60))

    return response

def encode(network: Network, _, msg_index: int, mode_switch_prob: float):
    logging.info("Encoding message into the entangled pairs.")
    src_node: EndNode = network.nodes[msg_index]
    message = network._bin_msgs[msg_index]
    msg_iter = iter(message)
    ctrl_meas_basis = {}
    outputs = {}
    for info in src_node.resource_manager.memory_manager:
        if info.state == "ENTANGLED":

            qtc = QutipCircuit(1)
            qtc = network._add_noise(err_type="reset", qtc=qtc)

            mode = random.choices(["service", "control"], weights=[1 - mode_switch_prob, mode_switch_prob])[0]
            key = info.memory.qstate_key

            logger.info(f"mode: {mode} on key: {key}")

            if mode == "service":
                if int(next(msg_iter, 0)):
                    qtc.x(0)
                if int(next(msg_iter, 0)):
                    qtc.z(0)
            elif mode == "control":
                ctrl_meas_basis[key] = random.randint(0, 1)
                if ctrl_meas_basis[key]:
                    qtc.h(0)
                qtc.measure(0)
                info.to_occupied()

            state = network.manager.get(key)
            # print(state.keys, network.manager.run_circuit(circuit=qtc, keys=[key]))
            outputs[tuple(sorted(state.keys))] = network.manager.run_circuit(circuit=qtc, keys=[key])

    return outputs, ctrl_meas_basis


def decode(networks:List[Network], all_returns:List[Any], err_threshold:float):
    network = networks[0]
    returns = all_returns[0]
    outputs, ctrl_meas_basis = returns[0], iter(returns[1])
    string = ""
    int_lst = [0]
    bsa = bell_type_state_analyzer(2)
    for keys, result in outputs.items():
        if result:
            qtc = QutipCircuit(1)
            qtc = network._add_noise(err_type="reset", qtc=qtc)
            c = next(ctrl_meas_basis)
            if returns[1][c]: qtc.x(0)
            qtc.measure(0)
            output = network._add_noise(err_type="readout", qtc=qtc, keys=keys[-1:])
            int_lst.append(returns[1][c]^result[list(result)[0]]^output[list(output)[0]])
        else:
            output = list(network._add_noise(err_type="readout", qtc=bsa, keys=keys).values())[::-1]
            string += "".join(str(out) for out in output)
    network._strings = [string[:len(network._bin_msgs[0])]]
    if mean(int_lst) > err_threshold:
        logger.error("Eavesdropper detected in channel.")
        return {"Err_msg":"Eavesdropper detected in channel."}
    else:
        return to_string(strings=network._strings, _was_binary=network._is_binary)

if __name__=="__main__":
    topology = {
        'nodes': [
            {
                'Name': 'node1',
                'Type': 'end',
                'noOfMemory': 500,
                'memory': {
                    'frequency': 80000000,
                    'expiry': -1,
                    'efficiency': 1,
                    'fidelity': 0.93
                    },
                'lightSource': {
                    'frequency': 80000000,
                    'wavelength': 1550,
                    'bandwidth': 0,
                    'mean_photon_num': 0.1,
                    'phase_error': 0
                    }
                },
            {
                'Name': 'node2',
                'Type': 'end',
                'noOfMemory': 500,
                'memory': {
                    'frequency': 80000000,
                    'expiry': -1,
                    'efficiency': 1,
                    'fidelity': 0.93
                    },
                'lightSource': {
                    'frequency': 80000000,
                    'wavelength': 1550,
                    'bandwidth': 0,
                    'mean_photon_num': 0.1,
                    'phase_error': 0
                    }
                }
            ],
        'quantum_connections': [
            {
                'Nodes': ['node1', 'node2'],
                'Attenuation': 0.1,
                'Distance': 70
                }
            ],
        'classical_connections': [
            {
                'Nodes': ['node1', 'node1'],
                'Delay': 0,
                'Distance': 0
                },
            {
                'Nodes': ['node1', 'node2'],
                'Delay': 10000000000,
                'Distance': 1000
                },
            {
                'Nodes': ['node2', 'node1'],
                'Delay': 10000000000,
                'Distance': 1000
                },
            {
                'Nodes': ['node2', 'node2'],
                'Delay': 0,
                'Distance': 0
                }
            ],
        'detector': {
            'efficiency': 1,
            'count_rate': 25000000,
            'time_resolution': 150
            }
        }
    app_settings = \
        {
            "sender":
                {
                    "node": "node1",
                    "message": "hi",
                    "switchProb": 0.3
                },
            "receiver":
                {
                    "node": "node2"
                }
        }
    print(ping_pong(topology=topology, app_settings=app_settings))