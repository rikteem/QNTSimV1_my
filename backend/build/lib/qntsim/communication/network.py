import inspect
import itertools
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial, reduce
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from IPython.display import clear_output
from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.random import randint
from pandas import DataFrame

from ..components.circuit import QutipCircuit
from ..kernel.timeline import Timeline
from ..topology.topology import Topology
from .circuits import bell_type_state_analyzer
from .noise import ERROR_TYPE
from .NoiseModel import noise_model
from .utils import to_binary, to_string

Timeline.bk = True
Timeline.DLCZ = False


class Network:
    """
    Initializes a quantum network object, which consists of nodes that can communicate with each other using qubits.

    During object creation:
        Args:
        - topology (str): A string representing the type of network topology, e.g. 'complete', 'line', 'ring', 'grid'.
        - messages (Dict[Tuple, str]): A dictionary containing the messages to be sent, in the form {(sender, receiver): message}.
        - name (str): An optional string representing the name of the network.
        - backend (str): An optional string representing the name of the backend to be used, e.g. 'Qutip'.
        - parameters (str): An optional string representing the name of the file containing the network parameters.
        - stop_time (int): An optional integer representing the time to stop the simulation, in nanoseconds.
        - start_time (int): An optional integer representing the time to start the simulation, in nanoseconds.
        - end_time (int): An optional integer representing the time to end the simulation, in nanoseconds.
        - priority (int): An optional integer representing the priority of the network.
        - target_fidelity (float): An optional float representing the target fidelity of the network.
        - timeout (int): An optional integer representing the timeout of the network, in nanoseconds.
        - **kwds (Any): Additional keyword arguments to be passed to the network.

        (Optional) Kwds:
            size (int, callable): The number of n2n entangled pairs required in the network.
            keys_of (int): Index of the node, for which the keys are requested.
            label (str): Initial states of the qubits. Doesn't work with superposition statess.

    During function call:
        Args:
            id_ (int, optional): The id of the <Network> object. Defaults to 0.

    Attributes:
        Network.__Network_name: Name of the object for identification.
        Network._backend: The backend on which the circuits are executed.
        Network._bell_pairs: Dictionary of the bell pairs with the index denoting the entanglement between the memory keys
        Network._bin_msgs: Binary equivalent of <Network>.messages.
        Network._flow: List of functions which will be executed in the defined sequence.
        Network._initials: Initials states of single photons.
        Network._kwds: Keyword arguements provided to the object, required during specific function calls.
        Network._net_topo: <Topology> object, managing network topologies.
        Network._outputs: Measurement outcomes from measuring out the photons.
        Network._parameters: the device parameters of the optical components.
        Network._strings: List of binary strings generated from the measurement outcomes.
        Network._timeline: <Timeline> object, which provides an interface for the simulation kernel and drives event execution.
        Network._topology: Topology of the network.
        Network.cchannels: Classical channels between the nodes in the network.
        Network.manager: <QuantumManager> object to track and manage quantum states.
        Network.messages: Messages to be transfered over the network.
        Network.nodes: End nodes present in the network.
        Network.qchannels: Quantum channels between the nodes in the network.
        Network.recv_msgs: Dictionary of the received messages, recreated from the strings.
        Network.size: Number of entangled pairs required for successful transmission of the messages.

    Methods:
        Network.__call__(id_): Calls and executes the network of 'id_'
        Network.__getitem__(item): Return indexed end node.
        Network.__iter__(): Iterates over the nodes in the network
        Network.__repr__(): Returns the string representation of the <Network> object
        Network._decode(): Reconstructs the message from the received messages in the network
        Network._execute(id_): Executes the network of 'id_'
        Network._identify_states(): Notes the entanglement of each keys
        Network._initialize_photons(): Initializes photons into random states among {|H⟩, |V⟩, |u⟩, |d⟩}
        Network._initiate(): Initiates the simulator, while requesting and rectifying entanglements or, initializing photons
        Network._rectify_entanglements(label): Rectifies the entanglements generated by the simulator
        Network._request_entanglements(): Requests entanglements from the simulator
        Network._set_parameters(): Tunes in the optical components
        Network.get_keys(node_index, info_state): Extracts the info on keys for the states matching the 'info_state'
        Network.generate_state(state, label): Generates multi-party entangled states from Bell pairs
        Network.encode(msg_index, node_index): Transmits message over the network through encoding the info on single photons
        Network.superdense_code(msg_index, node_index): Tranmits message over the network through superdense coding
        Network.teleport(msg_index, node_index): Teleports the message over the network
        Network.measure(): Measures the qubits in the network
        Network.dump(node_name, info_state): Dumps all the quantum states maching with the 'info_state' for the nodes provided
        Network.draw(): Generates a visual representation of the topology of network
        Network.execute(networks): Executes all the networks in the list
        Network.decode(networks, *args): Reconstructs the message from the received messages for all the networks

    Further info:

    Examples:
        QSDC with mutual authentication (IP2):
            from functools import partial
            from typing import Any, Dict, List, Tuple
            from qntsim.library import insert_check_bits, insert_decoy_photons, bell_type_state_analyzer, Protocol
            from qntsim.library.attack import Attack, ATTACK_TYPE

            class Party:
                input_messages:Dict[Tuple, str] = None
                id:str = None
                received_msgs:Dict[int, str] = None

            class Alice(Party):
                chk_bts_insrt_lctns:List[int] = None
                num_check_bits:int = None

                @classmethod
                def input_check_bits(cls, network:Network, returns:Any):
                    .
                    .
                    .

                @classmethod
                def encode(cls, network:Network, returns:Any):
                    .
                    .
                    .

                @classmethod
                def insert_new_decoy_photons(cls, network:Network, returns:Any, num_decoy_photons:int):
                    .
                    .
                    .

            class Bob(Party):
                @classmethod
                def setup(cls, network:Network, returns:Any, num_decoy_photons:int):
                    .
                    .
                    .

                def decode(network:Network, returns:Any):
                    .
                    .
                    .

                @classmethod
                def check_integrity(cls, network:Network, returns:Any, cls1, threshold:float):
                    .
                    .
                    .

            class UTP:
                @classmethod
                def check_channel_security(cls, network:Network, returns:Any, cls1, cls2, threshold:float):
                    .
                    .
                    .

                def authenticate(network:Network, returns:Any, cls1, cls2, circuit:QutipCircuit):
                    .
                    .
                    .

                def measure(network:Network, returns:Any, circuit:QutipCircuit, cls):
                    .
                    .
                    .

            def pass_(network:Network, returns:Any):
                return returns

            topology = '2n_linear.json'
            Alice.input_messages = {(1, 2):'011010'
            Alice.id = '1011'
            Alice.num_check_bits = 4
            Bob.id = '0111'
            threshold = 0.2
            attack, chnnl = (None, None) #(attack_type, channel_no.) channel_no. doesn't implement attack. one can say that the channel 1 is secured.
            chnnl = [1 if i==chnnl else 0 for i in range(3)]
            Network._funcs = [partial(Alice.input_check_bits),
                            partial(Bob.setup, num_decoy_photons=num_decoy_photons),
                            partial(Alice.encode),
                            partial(Attack.implement, attack=ATTACK_TYPE[attack].value) if attack and chnnl[0] else partial(pass_),
                            partial(UTP.check_channel_security, cls1=Alice, cls2=Bob, threshold=threshold),
                            partial(Alice.insert_new_decoy_photons, num_decoy_photons=num_decoy_photons),
                            #   partial(Attack.implement, attack=ATTACK_TYPE[attack].value) if attack and chnnl[1] else partial(pass_),
                            partial(UTP.check_channel_security, cls1=UTP, cls2=Alice, threshold=threshold),
                            partial(Attack.implement, attack=ATTACK_TYPE[attack].value) if attack and chnnl[2] else partial(pass_),
                            partial(UTP.check_channel_security, cls1=UTP, cls2=Bob, threshold=threshold),
                            partial(UTP.authenticate, cls1=Alice, cls2=Bob, circuit=bell_type_state_analyzer(2)),
                            partial(UTP.measure, circuit=bell_type_state_analyzer(2), cls=Alice),
                            partial(Bob.decode),
                            partial(Bob.check_integrity, cls1=Alice, threshold=threshold)]

            network = Network(topology='2n_linear.json',
                            messages=Alice.input_messages,
                            name='ip2',
                            size=lambda x:(x+Alice.num_check_bits+len(Alice.id)+len(Bob.id))//2,
                            label='00')
            network()
            print(f'Received messages:{Bob.received_messages}')
            print(f'Error in execution:{mean(protocol.mean_list)}')
    """

    _flow: List[partial] = []

    def __init__(
        self,
        topology,
        messages: Dict[Tuple, str],
        name: str = "network",
        backend: str = "Qutip",
        # parameters: str = "parameters.json",
        stop_time: int = 10e12,
        start_time: int = 5e12,
        end_time: int = 10e12,
        priority: int = 0,
        target_fidelity: float = 0.5,
        timeout: int = 10e12,
        require_entanglement:bool = True,
        **kwds,
    ) -> None:
        self.__name = name
        self._topology = topology
        self._backend = backend
        # self._parameters = parameters
        self._stop_time = stop_time
        self._start_time = start_time
        self._end_time = end_time
        self._priority = priority
        self._target_fidelity = target_fidelity
        self._timeout = timeout
        self.messages = messages
        self._is_binary, self._bin_msgs = to_binary(messages=list(messages.values()))
        self.__dict__.update(**kwds)
        if not hasattr(self, "size"):
            self.size = len(self._bin_msgs[0])
        elif callable(self.size):
            self.size = self.size(len(self._bin_msgs[0]))
        if hasattr(self, "noise"):
            self.__dict__.update(
                {
                    noise: ERROR_TYPE[noise].value(*probs)
                    for noise, probs in self.noise.items()
                }
            )
        # stack = inspect.stack()
        # caller = stack[1][0].f_locals.get("self").__class__.__name__
        # from .protocol import ProtocolPipeline

        # if caller != ProtocolPipeline.__name__:
        #     print("Configuring logger!")
        #     logging.basicConfig(
        #         filename=self.__name + ".log",
        #         filemode="w",
        #         level=logging.INFO,
        #         format="%(pathname)s %(threadName)s %(module)s %(funcName)s %(message)s",
        #     )
        self._initiate(require_entanglement=require_entanglement)
        self.get_keys(
            _=None,
            node_index=self.keys_of if hasattr(self, "keys_of") else 0,
            info_state="ENTANGLED",
        )

    def __iter__(self):
        """
        Returns an iterator over the nodes in the network.

        Args:
        - None

        Returns:
        - An iterator over the nodes in the network.
        """
        return iter(self.nodes)

    def __getitem__(self, item):
        """
        Retrieve the node at the specified index.

        Parameters:
            item (int): The index of the node to retrieve.

        Returns:
            Node: The node at the specified index.
        """
        return self.nodes[item]

    def _initiate(self, require_entanglement:bool=True):
        """
        Initializes the quantum network by creating a timeline and topology,
        setting parameters, and identifying end nodes. If there are multiple end nodes,
        it requests entanglements, identifies states, rectifies entanglements,
        and logs information. Otherwise, it initializes photons.
        """
        # Create a timeline and topology for the quantum network
        self._timeline = Timeline(stop_time=self._stop_time, backend=self._backend)
        self._net_topo = Topology(name=self.__name, timeline=self._timeline)

        # Load the configuration for the network topology
        load_topo = self._net_topo.load_config_json if "nodes" in self._topology else self._net_topo.load_config
        load_topo(self._topology)

        # Set parameters for the quantum network
        # self._set_parameters()

        # Identify the end nodes in the network
        self.nodes = self._net_topo.get_nodes_by_type("EndNode")
        self.qchannels = self._net_topo.qchannels
        self.cchannels = self._net_topo.cchannels

        # Initialize the quantum manager for the network
        self.manager = self._timeline.quantum_manager

        # Set initial values for Bell pairs and state identification
        self._bell_pairs = {}

        # If there are multiple end nodes, request entanglements and rectify entanglements
        if require_entanglement:
            self._request_entanglements()
            # print(__name__, "Entities", self._timeline.entities)
            # print(__name__, "Events", self._timeline.events)
            self._timeline.init()
            self._timeline.run()
            self._identify_quantum_states()
            self._rectify_entanglements(
                label=self.label if hasattr(self, "label") else "00"
            )

            # Clear the output and log information
            clear_output()
            logging.info("EPR pair generator")

        # Otherwise, initialize photons
        else:
            self._initialize_photons()

    # def _set_parameters(self):
    #     nodes = self._net_topo.nodes
    #     print('node', nodes,self._topology)
    #     for node in self._topology.get("nodes", []):
    #         node_obj = nodes.get(node.get("Name"))
    #         if node.get("Type") in ["service", "end"]:
    #             for arg, val in node.get("memory", {}).items():
    #                 node_obj.memory_array.update_memory_params(arg, val)
    #             for arg, val in node.get("lightSource", {}).items():
    #                 setattr(node_obj.lightsource, arg, val)
    #         elif node.get("Type")=="bsm":
    #             for arg, val in node.get("detector", {}).items():
    #                 setattr(node_obj.bsm, arg, val)
        # # Read the parameter data from the file
        # with open(self._parameters, "r") as file:
        #     data = json.load(file)

        # # Loop through each parameter type and update the corresponding components
        # for key, value in data.items():
        #     # Get the nodes of the current type
        #     nodes = (
        #         self._net_topo.get_nodes_by_type(key)
        #         if key != "qchannel"
        #         else self._net_topo.qchannels
        #     )

        #     # Loop through each node of the current type and update its parameters
        #     for component in nodes:
        #         if key == "qchannel":
        #             # Update qchannel parameters
        #             component.attenuation, component.frequency = value
        #         elif key == "EndNode" or key == "ServiceNode":
        #             # Update memory array parameters for EndNodes and ServiceNodes
        #             for k, v in value.items():
        #                 component.memory_array.update_memory_params(k, v)
        #         elif key == "BSMNode":
        #             # Update detector parameters for BSMNodes
        #             for k, v in value.items():
        #                 component.bsm.update_detectors_params(k, v)
        #         elif key == "QuantumRouter":
        #             # Update swapping parameters for QuantumRouters
        #             if k == "SWAP_SUCCESS_PROBABILITY":
        #                 component.network_manager.protocol_stack[
        #                     1
        #                 ].set_swapping_success_rate(v)
        #             else:
        #                 component.network_manager.protocol_stack[
        #                     1
        #                 ].set_swapping_degradation(v)

    def _request_entanglements(self):
        # Loop through each sequence of keys in messages
        for node_sequence in self.messages:
            # Loop through each consecutive pair of keys in the sequence
            for source_name, dest_name in itertools.pairwise(node_sequence):
                # Get the source and destination nodes for the entanglement request
                source_node = self._net_topo.nodes[source_name]
                # dest_node = self._net_topo.nodes[dest_name]
                print(f"Requesting {self.size} entanglements between {source_name} and {dest_name}")

                # Get the transport manager for the source node and send the entanglement request
                transport_manager = source_node.transport_manager
                transport_manager.request(
                    dest_name,
                    size=self.size,
                    start_time=self._start_time,
                    end_time=self._end_time,
                    priority=self._priority,
                    target_fidelity=self._target_fidelity,
                    timeout=self._timeout,
                )

    def _identify_quantum_states(self):
        """
        Identifies the quantum states of a circuit.
        """
        for node in self[:-1]:  # iterate over all nodes except the last node
            for info in node.resource_manager.memory_manager:
                if info.state != "ENTANGLED":
                    break  # exit early if the state is not 'ENTANGLED'
                key = info.memory.qstate_key
                state = self.manager.get(key).state
                # Determine the Bell pair indices
                bell_pair_index_j = 0 if state[1] == state[2] == 0 else 1
                bell_pair_index_i = (
                    1 - int(state[bell_pair_index_j] / state[3 - bell_pair_index_j])
                ) // 2
                self._bell_pairs[tuple(self.manager.get(key).keys)] = (
                    bell_pair_index_i,
                    bell_pair_index_j,
                )

    def _rectify_entanglements(self, label: str):
        """
        Rectifies the entanglements of a circuit based on the Bell pairs identified.
        """
        for (key1, key2), (
            bell_pair_index_i,
            bell_pair_index_j,
        ) in self._bell_pairs.items():
            qtc = QutipCircuit(1)
            if bell_pair_index_j ^ int(label[1]):
                qtc.x(0)
            if bell_pair_index_i ^ int(label[0]):
                qtc.z(0)
            self.manager.run_circuit(qtc, [key1])
            self._bell_pairs[(key1, key2)] = (int(label[0]), int(label[1]))

    def _add_noise(self, err_type: str, qtc: QutipCircuit, keys: List[int] = None):
        """
        Add noise to a QutipCircuit object using the specified error model.

        Args:
        - err_type (str): The type of error to apply ('reset' or 'readout').
        - qtc (QutipCircuit): The QutipCircuit object to apply the error to.
        - keys (Optional[List[int]]): A list of qubit indices to apply the readout error to.

        Returns:
        - QutipCircuit: The QutipCircuit object with the specified error applied.
        """
        model = noise_model()  # Create a new noise model

        # Apply the specified error to the noise model
        match err_type:
            case "reset":
                if hasattr(self, "reset"):
                    model.add_reset_error(err=self.reset)
                    # Apply the reset error to the circuit
                    return model._apply_reset_error(crc=qtc, size=qtc.size)
                return (
                    qtc  # If no reset error is specified, return the original circuit
                )
            case "readout":
                if hasattr(self, "readout"):
                    model.add_readout_error(err=self.readout)
                # Apply the readout error to the circuit
                return model._apply_readout_error_qntsim(
                    crc=qtc, manager=self.manager, keys=keys
                )

    def _initialize_photons(self):
        """
        Initializes the photons for a quantum circuit.
        """
        self._initials = randint(4, size=self.size)
        for info, initial in zip(
            self[0].resource_manager.memory_manager, self._initials
        ):
            key = info.memory.qstate_key
            q, r = divmod(initial, 2)
            qtc = QutipCircuit(1)
            qtc = self._add_noise(err_type="reset", qtc=qtc)
            if r:
                qtc.x(0)
            if q:
                qtc.h(0)
            self.manager.run_circuit(qtc, [key])
        self._initials = self._initials.tolist()
        logging.info(
            f"Initialized {self.size} photons with initial states {self._initials}"
        )

    def get_keys(self, _:Optional[None], node_index: int, info_state: str = "ENTANGLED"):
        """Retrives the keys of a node, of a specific state. Updates the 'keys' attribute with the required keys.

        Args:
            node_index (int): Index of the node in the network.
            info_state (str, optional): The state of the keys, on demand. Defaults to 'ENTANGLED'.
        """
        keys = []
        for info in self[node_index].resource_manager.memory_manager:
            if info.state == info_state:
                key = info.memory.qstate_key
                state = self.manager.get(key=key)
                keys.append(state.keys)
        self.keys = keys

    def generate_state(self, _, state: int = 0, label: str = None):
        """Generates multi-party entangled states from Bell pairs.
        'state=0' generates GHZ states.
        'state=1' generates XOR states.

        Args:
            state (int, optional): Refernce to a specific entangled state. Defaults to 0.
            label (str, optional): Initial state of the qubits. Defaults to None.
        """
        self.state = state

        qtc = QutipCircuit(2)
        qtc = self._add_noise(err_type="reset", qtc=qtc)
        qtc.cx(0, 1)
        if state:
            qtc.h(0)
        qtc.measure(1 - state)

        qc = QutipCircuit(1)
        qc = self._add_noise(err_type="reset", qtc=qc)
        if state:
            qc.z(0)
        else:
            qc.x(0)

        for keys in self.messages:
            for key in keys[1:-1]:
                for info1, info2 in zip(
                    self._net_topo.nodes.get(key).resource_manager.memory_manager[
                        : self.size
                    ],
                    self._net_topo.nodes.get(key).resource_manager.memory_manager[
                        self.size :
                    ],
                ):
                    keys = [info1.memory.qstate_key, info2.memory.qstate_key]
                    qstate = self.manager.get(keys[1 - state])
                    if self._add_noise(err_type="readout", qtc=qtc, keys=keys).get(
                        keys[1 - state]
                    ):
                        self.manager.run_circuit(
                            qc, list(set(qstate.keys) - set([keys[1 - state]]))
                        )
        if label:
            for info in self[0].resource_manager.memory_manager:
                if info.state != "ENTANGLED":
                    break
                keys = self.manager.get(info.memory.qstate_key).keys
                for key, (i, lbl) in zip(keys, enumerate(label)):
                    qtc = QutipCircuit(1)
                    qtc = self._add_noise(err_type="reset", qtc=qtc)
                    if int(lbl):
                        _ = qtc.x(0) if i else qtc.z(0)
                    self.manager.run_circuit(qtc, [key])

    def encode(self, _: Any, msg_index: int, node_index: int = 0):
        """Encodes the classical bits as unitary gates on single photons. 0 & 1 are mapped to I and iY gates, respectively.

        Args:
            returns (Any): Returns from previous function.
            msg_index (int): Index of the message to be encoded.
            node_index (int, optional): Index of the node encoding the message. Defaults to 0.
        """
        qtc = QutipCircuit(1)
        qtc = self._add_noise(err_type="reset", qtc=qtc)
        qtc.x(0)
        qtc.z(0)

        for bin, info in zip(
            self._bin_msgs[msg_index],
            self.nodes[node_index].resource_manager.memory_manager,
        ):
            if int(bin):
                key = info.memory.qstate_key
                self.manager.run_circuit(qtc, [key])
        logging.info("message bits into qubits")

    def superdense_code(self, _: Any, msg_index: int, node_index: int = 0):
        """Encodes 2-bit classical information through superdense coding.

        Args:
            returns (Any): Returns from previous function.
            msg_index (int): Index of the message to be encoded.
            node_index (int, optional): Index of the node encoding the message. Defaults to 0.
        """
        for bin1, bin2, info in zip(
            self._bin_msgs[msg_index][::2],
            self._bin_msgs[msg_index][1::2],
            self.nodes[node_index].resource_manager.memory_manager,
        ):
            qtc = QutipCircuit(1)
            qtc = self._add_noise(err_type="reset", qtc=qtc)
            if int(bin2):
                qtc.x(0)
            if int(bin1):
                qtc.z(0)
            key = info.memory.qstate_key
            self.manager.run_circuit(qtc, [key])
        logging.info("message bits into the channel")

    def teleport(self, _: Any, node_index: int = 0, msg_index: int = 0):
        """Encodes message bit as superposed states and then teleports the state over the entangled channel. 0's and 1's are encoded as '+' and '-' quantum states, respectively.

        Args:
            returns (Any): Returns from previous function.
            msg_index (int): Index of the message to be encoded.
            node_index (int, optional): Index of the node encoding the message. Defaults to 0.
        """
        alpha = complex(1 / np.sqrt(2))
        bsa = bell_type_state_analyzer(2)
        self._corrections = {}
        msg = iter(self._bin_msgs[msg_index])
        for info in self[node_index].resource_manager.memory_manager:
            if info.state == "ENTANGLED":
                bin = next(msg)
                key = info.memory.qstate_key
                new_key = self.manager.new([alpha, ((-1) ** int(bin)) * alpha])
                state = self.manager.get(key)
                keys = tuple(set(state.keys) - set([key]))
                outputs = self._add_noise(err_type="readout", qtc=bsa, keys=[new_key, key])
                self._corrections[keys] = [outputs.get(new_key), outputs.get(key)]
                print(key, state.keys, new_key, info.state)
        logging.info("message states")

    def measure(self, _: Any):
        """Measures the qubits and stores the output for decoding the message

        Args:
            returns (Any): Returns from the previous function call.
        """
        self._outputs = []
        if hasattr(self, "_initials"):
            node = self[0]
            for info, initial in zip(
                node.resource_manager.memory_manager, self._initials
            ):
                key = info.memory.qstate_key
                qtc = QutipCircuit(1)
                qtc = self._add_noise(err_type="reset", qtc=qtc)
                if initial // 2:
                    qtc.h(0)
                qtc.measure(0)
                self._outputs.append(
                    self._add_noise(err_type="readout", qtc=qtc, keys=[key])
                )
        elif hasattr(self, "_corrections"):
            output = 0
            print(self._corrections)
            for keys, value in self._corrections.items():
                print(keys)
                if len(keys) > 1:
                    key = max(keys)
                    qtc = QutipCircuit(1)
                    qtc = self._add_noise(err_type="reset", qtc=qtc)
                    if ~self.state:
                        qtc.h(0)
                    qtc.measure(0)
                    output = self._add_noise(
                        err_type="readout", qtc=qtc, keys=[key]
                    ).get(key)
                qtc = QutipCircuit(1)
                qtc = self._add_noise(err_type="reset", qtc=qtc)
                if output:
                    if self.state:
                        qtc.x(0)
                    else:
                        qtc.z(0)
                if value[1]:
                    qtc.x(0)
                if value[0]:
                    qtc.z(0)
                qtc.h(0)
                qtc.measure(0)
                key = min(keys)
                self._outputs.append(
                    self._add_noise(err_type="readout", qtc=qtc, keys=[key])
                )

    # @delayed
    # @wrap_non_picklable_objects
    def _decode(self, *_):
        self._strings = []
        if hasattr(self, "_initials"):
            node = self.nodes[0]
            for bin_msg in self._bin_msgs:
                string = ""
                for info, initial, output in zip(
                    node.resource_manager.memory_manager, self._initials, self._outputs
                ):
                    bin = bin_msg[info.index] if len(self._bin_msgs) > 1 else "0"
                    key = info.memory.qstate_key
                    string += str(initial % 2 ^ output.get(key) ^ int(bin))
                self._strings.append(string)
        else:
            self._strings = ["".join(str(*output.values()) for output in self._outputs)]
        self.recv_msgs = {rec[1:]:message for rec, message in zip(list(self.messages)[::-1], to_string(strings=self._strings, _was_binary=self._is_binary))}
        for k, v in self.recv_msgs.items():
            logging.info(f"Received message {k}: {v}")

        return self.recv_msgs

    @staticmethod
    def decode(networks: List["Network"], *args):
        """Decodes the received message from the meaured outputs

        Args:
            networks (List[Network]): List of <Network> objects

        Returns:
            List[Dict[int, str]]: The decoded messages for all the 'networks'
        """
        logging.info("messages")
        return [network._decode(*arg) for network, arg in zip(networks, args)]
        # executor = ThreadPoolExecutor(max_workers=len(networks))
        # jobs = [executor.submit(network._decode, network, *args) for network in networks]
        # return [job.result() for job in  jobs]
        # return Parallel(n_jobs=-1, prefer='threads')(network._decode(network=network, *args) for network in networks)

    def dump(self, _: Any, node_name: str = "", info_state: str = ""):
        """Logs the current memory state of the nodes in the network

        Args:
            returns (Any): Returns from the previous functions
            node_name (str, optional): Index of the node to be dumped. Defaults to ''.
            info_state (str, optional): State of the memory to be dumped. Choices = ['ENTANGLED', 'OCCUPIED', 'RAW']. Defaults to '', upon which all memories are dumped.
        """
        logging.basicConfig(
            filename=self.__name + ".log",
            filemode="w",
            level=logging.INFO,
            format="%{funcName}s %(message)s",
        )
        for node in [self._net_topo.nodes.get(node_name)] if node_name else self.nodes:
            logging.info(f"{node.owner.name}'s memory arrays")
            keys, states = [], []
            for info in node.resource_manager.memory_manager:
                if not info_state or info.state == info_state:
                    key = info.memory.qstate_key
                    state = self.manager.get(key)
                    keys.append(state.keys)
                    states.append(state.state)
                dataframe = DataFrame({"keys": keys, "states": states})
        logging.info(dataframe.to_string())

    def draw(self, _: Any):
        """_summary_

        Args:
            returns (Any): Returns from the previous function call.

        Returns:
            networkx.Graph: <networkx.Graph> object
        """
        return self._net_topo.get_virtual_graph()

    @staticmethod
    def execute(networks: List["Network"]):
        """Executes the flow of the networks

        Args:
            networks (List[Network]): List of <network> objects

        Returns:
            List[Any]: The executed result of each network
        """
        return [network._execute(i) for i, network in enumerate(networks, 1)]
        # executor = ThreadPoolExecutor(max_workers=len(networks))
        # jobs = [executor.submit(network._execute, network, i) for i, network in enumerate(networks, 1)]
        # print([job for job in jobs])
        # return [job.result() for job in  jobs]
        # return Parallel(n_jobs=-1, prefer='threads')(network._execute(id_=i) for i, network in enumerate(networks, 1))

    def __call__(self, id_: int = 0):
        return self._execute(id_)
        # executor = ThreadPoolExecutor(max_workers=1)
        # jobs = executor.submit(self._execute, self, id_)
        # return [job.result() for job in  jobs]
        # return Parallel(n_jobs=-1, prefer='threads')([self._execute(id_=id_)])

    # @delayed
    # @wrap_non_picklable_objects
    def _execute(self, id_: int = 0):
        self._id = id_
        self.__name += str(self._id)
        return reduce(lambda returns, func: func(self, returns), self._flow, ())

    def __repr__(self) -> str:
        """
        Returns a string representation of the network state showing the memory keys and states of each node.

        Returns:
        str: A string representation of the network state.
        """
        # For each node in the network, get the memory keys and states of its resource manager.
        # Then join the key-state pairs for each state into a single string and join the node memory
        # state strings together with a newline character.
        return "\n".join(
            [
                f"Memory keys of: {node.owner.name}\n"
                + "\n".join(
                    [
                        f"{state.keys}\t{state.state}"
                        for state in [
                            self.manager.get(info.memory.qstate_key)
                            for info in node.resource_manager.memory_manager
                        ]
                    ]
                )
                for node in self
            ]
        )
