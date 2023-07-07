import logging
from functools import partial
from time import time, time_ns
from typing import Any, Dict, List, Tuple

from IPython.display import clear_output
from numpy import mean

from .attack import ATTACK_TYPE, Attack
from .network import Network
from .security_checks import insert_check_bits


class ProtocolPipeline:
    """Creates the flow of functions for the execution of the communication protocols, which are a set of rules that enable data to be exchanged between nodes.

    During instantiation:
        Args:
            messages_list (List[Dict[Tuple, str]]): List of dictionary of messages for each <Network> the class would generate. Basically, the class would create a <Network> object for each message dictionary provied in the list.
            name (str, optional): A unique name to the protocol. Defaults to 'protocol'.

        (Optional) Kwds:
            state (int):
            label (str): Initial states of qubits for entanglement in the computational basis. Does not work with superposition states.
            encode (partial): User-defined encode function for the encoding scheme of a specific protocol.
            attack (str): Acronym of the attack to be implemented.
            measure (partial): User-defined measure function for measuring the qubits in the specific protocol.

    During function call:
        Args:
            topology (_type_): The topology of the network. Can be a json or, a file containing the json-format.
            functions (List[partial], optional): User-defined flow of functions. Defaults to None.

        (Optional) Kwds:
            decode (partial): User-defined decode function for the decoding scheme of a specific protocol.

            *Any other keyword arguments required to pass on to the <Network> class.*

    Attributes:
        Protocol.__Protocol_name:
        Protocol.__Protocol_funcs:
        Protocol.messages_list:
        Protocol.networks:
        Protocol.recv_msgs_list:
        Protocol.full_err_list:
        Protocol.mean_list:
        Protocol.sd_list:

    Methods:
        Protocol.__iter__(): Returns an iterator over the networks in the protocol.
        Protocol.__call__(): Executes the protocol by generating and executing the networks. Returns the output of the last function in the flow of the protocol.
        Protocol.__repr__(): Returns a string representation of the protocol.

    Further Info:
        The class creates the flow of execution for protocols, containing no authentication, or no security checks using random bits, or anything of that sort. In other words, the class generates the flow for unauthenticated/insecure protocols based on the parameters provided during the instantiation, or function call, or both. In other words, the parameters provided to the class are mapped to specfic function calls, which then implements the specific protocol in the specific sequential flow. These parameters to the instantiation, or to the function calls need to be provided with specific keywords, so that the map can be created to the function calls, as these parameters serve as the arguments to the function calls.
        User-defined functions can also be provided as keyword arguments during constructor/function call, though with the condition that the functions need to defined in the following fashion:-

            def <function_name>(arg1:'Network', arg2:Any, ...):
                .
                .
                .

        where the argument 'arg1' is an object of class <Network> and 'arg2' is treated as the returned value from a previous function call. Although, the 'decode' functions takes a list of <Network> objects as its first argument. In other words, the 'decode' functions must be defined as:

            def decode(arg1:List['Network'], arg2:Any, ...):
                .
                .
                .
        Refer to the examples for further clarification on function definitions.

        For further information on the optional keyword arguments, refer to the <Network> documentation.

    Examples:
        QSDC protocols using:
            Quantum One-Time-Pad:

                from statistics import mean
                from qntsim.library import Protocol

                topology = 'single_node.json'
                messages = {(1, 2):'hello'}
                attack = None

                protocol = Protocol(name='qsdc_otp', messages_list=[messages], attack=attack)
                protocol(topology=topology)
                print('Received messages:', protocol.recv_msgs_list)
                print('Error:', mean(protocol.mean_list))

            EPR pairs and teleportation:

                from statistics import mean
                from qntsim.library.protocol import Protocol

                topology = '2n_linear.json'
                messages = {(1, 2):'hello'}
                attack = None

                protocol = Protocol(name='qsdc_tel', messages_list=[messages], label='00', attack=attack)
                protocol(topology=topology)
                print('Received messages:', protocol.recv_msgs_list)
                print('Error:', mean(protocol.mean_list))

            3-party entangled state and controlled teleportation:

                from statistics import mean
                from qntsim.library import Protocol

                topology = '3n_linear.json'
                messages = {(1, 2):'hello'}

                protocol = Protocol(messages_list=[messages], name='qsdc_ctel', state=1, label='000')
                protocol(topology=topology)
                print('Recived messages::', protocol.recv_msgs_list)
                print('Error in execution:', mean(protocol.mean_list))

            EPR pairs and GHZ measurement:

                from statistics import mean
                from typing import Any, List
                from functools import partial
                from qntsim.library import Protocol, Network, bell_type_state_analyzer

                def encode(network:Network, returns:Any, ...):
                    .
                    .
                    .

                def measure(network:Network, returns:Any, ...):
                    .
                    .
                    .

                def decode(networks:List[Network], returns:Any, ...):
                    .
                    .
                    .

                topology='2n_linear.json'
                messages = {(1, 2):'hi'}
                attack = None

                protocol = Protocol(messages_list=[messages], name='qsdc_swap_entg', encode=partial(encode), measure=partial(measure, circuit=bell_type_state_analyzer(3)), attack=attack)
                protocol(topology=topology, decode=partial(decode), size=lambda x:x+(3-x%3 if x%3 else 0))
                print('Recieved messages:', protocol.recv_msgs_list)
                print('Error in execution:', mean(protocol.mean_list))

        QD protocols using:
            Single Photons:

                from statistics import mean
                from qntsim.library.protocol import Protocol

                topology = 'single_node.json'
                messages = {(1, 2):'hello', (2, 1):'world'}
                attack = None

                protocol = Protocol(name='qd_sp', messages_list=[messages], attack=attack)
                protocol(topology=topology)
                print('Recieved messages:', protocol.recv_msgs_list)
                print('Error in execution:', mean(protocol.mean_list))

            EPR pairs and superdense coding:

                from functools import partial
                from statistics import mean
                from typing import List
                from qntsim.library import Protocol, Network, bell_type_state_analyzer

                def measure(network:Network, returns):
                    .
                    .
                    .

                def decode(networks:List[Network], returns:Any, *args):
                    .
                    .
                    .

                topology='2n_linear.json'
                messages = {1:'h', 2:'m'}
                attack = None

                protocol = Protocol(name='qd_epr', messages_list=[messages], encode=partial(Network.superdense_code), measure=partial(measure), attack=attack)
                protocol(topology=topology, decode=partial(decode), size=lambda x:x//2)
                print('Received messages:', protocol.recv_msgs_list)
                print('Error:', mean(protocol.mean_list))

        QSS protocols using:
            GHZ states:

                from statistics import mean
                from qntsim.library import Protocol

                topology = '3n_linear.json'
                messages = {(1, 2):'hello'}

                protocol = Protocol(messages_list=[messages], name='qsdc_ctel', state=0, label='000')
                protocol(topology=topology)
                print('Recived messages::', protocol.recv_msgs_list)
                print('Error in execution:', mean(protocol.mean_list))
    """

    # networks = []
    # def __new__(cls, *args, **kwargs):
    #     """
    #     Returns the existing instance of the class if it exists, otherwise creates a new instance.

    #     """
    #     if not hasattr(cls, '_instance'):
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(
        self, messages_list: List[Dict[Tuple, str]], name: str = "protocol", **kwds
    ) -> None:
        """
        Initializes the Protocol class.

        Args:
            messages_list (List[Dict[Tuple, str]]): A list of dictionaries where each dictionary contains the messages to be
                                                    transmitted over a network.
            name (str): A name for the Protocol object.
            **kwds: Optional keyword arguments to modify the behaviour of the Protocol object.
        """
        self.__name = name
        self.__kwds = kwds
        self._index = -1

        # Set up logging
        logging.basicConfig(
            filename=self.__name + ".log",
            filemode="w",
            level=logging.INFO,
            format="%(pathname)s > %(threadName)s : %(module)s . %(funcName)s %(message)s",
        )

        self.messages_list = messages_list
        self.__funcs = []

        # Add functions to the flow based on the keyword arguments passed in
        if "state" in self.__kwds:
            self.__funcs.append(
                partial(
                    Network.generate_state,
                    state=self.__kwds.get("state"),
                    label=self.__kwds.get("label"),
                )
            )

        # If 'encode' is not in the keyword arguments, use Network.teleport as the default encoding function
        # Otherwise, use the function specified in 'encode'
        self.__funcs.append(
            partial(Network.teleport)
            if "encode" not in self.__kwds and "label" in self.__kwds
            else partial(self.__kwds.get("encode", Network.encode), msg_index=0)
        )

        # Add an attack to the flow if one was specified
        if (attack := self.__kwds.get("attack", "")) in ATTACK_TYPE.__members__:
            self.__funcs.append(
                partial(Attack.implement, attack=ATTACK_TYPE[attack].value)
            )

        # If there is more than one message, add encoding functions for each subsequent message
        if len(messages_list[0]) > 1:
            self.__funcs.extend(
                partial(self.__kwds.get("encode", Network.encode), msg_index=i)
                for i in range(1, len(messages_list[0]))
            )

        # Add a measurement function to the end of the flow
        self.__funcs.append(self.__kwds.get("measure", partial(Network.measure)))

    def __iter__(self):
        """
        Returns an iterator over the networks list.
        """
        return iter(self.networks)

    def __next__(self):
        if self._index < len(self.networks) - 1:
            self._index += 1
            return self.networks[self._index]
        else:
            print("No more networks left.")

    def __len__(self):
        return len(self.networks)

    def __call__(
        self, topology, functions: List[partial] = None, *args: Any, **kwds: Any
    ) -> Any:
        """
        Calls the Protocol object.

        Args:
            topology: The topology of the network.
            functions (List[partial]): A list of functions that make up the network flow. Defaults to None.
            *args: Variable length argument list.
            **kwds: Arbitrary keyword arguments.

        Returns:
            Any: The result of executing the network flow on the networks.
        """
        # Set the network flow to the provided list of functions, or to the default flow defined in the constructor
        Network._flow = functions or self.__funcs

        # Record the start time
        start_time = time_ns()

        # Create a list of networks, one for each set of messages in messages_list, using the provided topology
        self.networks = [
            Network(
                **kwds,
                **self.__kwds,
                name=self.__name,
                topology=topology,
                messages=messages,
            )
            for messages in self.messages_list
        ]

        # Record the midpoint time
        mid_time = time_ns()

        # Log that all networks have been generated
        logging.info("generated all networks")

        # Execute the network flow for all networks in parallel
        returns_list = Network.execute(networks=self.networks)

        # If the network flow was not provided as an argument, use the default flow and attempt to decode received messages
        if Network._flow == self.__funcs:
            self.recv_msgs_list = kwds.get("decode", Network.decode)(
                networks=self.networks,
                all_returns=returns_list
            )

        # Log the completion time
        logging.info(
            f"completed execution within {(time_ns()-start_time-mid_time):e} ns"
        )

        # Import and use the ErrorAnalyzer class to analyze errors in the network and store the results in the protocol instance
        from .error_analyzer import ErrorAnalyzer

        (
            self.full_err_list,
            self.full_lk_list,
            self.mean_list,
            self.sd_list,
            self.lk_list,
            self.fid_list,
        ) = ErrorAnalyzer.analyse(protocol=self)

        return (
            self.recv_msgs_list,
            mean(self.mean_list),
            mean(self.sd_list),
            mean(self.lk_list),
            mean(self.fid_list),
        )

    def __repr__(self) -> str:
        """
        Return a string representation of the current state of the protocol.
        """
        # Use a list comprehension to build the string
        string = "\n".join(
            [
                # Use f-strings for string interpolation
                f"Network:{network._Network__name}\n"
                + f"Memory keys of node:{node.owner.name}\n"
                +
                # Use a generator expression to iterate over the memory manager items
                "\n".join(
                    [
                        f"{state.keys}\t{state.state}"
                        for info in node.resource_manager.memory_manager
                        # Get the state from the network's manager using the qstate_key
                        # Use a try-except block to handle cases where the state has been deleted
                        # before this method is called
                        if (state := network.manager.get(info.memory.qstate_key))
                        is not None
                    ]
                )
                for network in self
                for node in network
            ]
        )

        return string

    @staticmethod
    def execute(topology:Dict, app_settings:Dict):
        response = {}
        
        protocol = ProtocolPipeline()