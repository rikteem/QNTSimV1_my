class Network:
    """
    A class representing a classical network.
    """

    def __init__(self, name: str, nodes: list, ip: str, url: str, *args, **kwargs):
        """
        Initialize the Network object.

        Args:
            name (str): The name of the network.
            nodes (list): A list of nodes in the network.
            ip (str): The IP address of the network.
            url (str): The URL of the network.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Attributes:
            name (str): The name of the network.
            nodes (list): A list of nodes in the network.
            ip (str): The IP address of the network.
            url (str): The URL of the network.
        """
        self.name = name
        self.nodes = nodes
        self.ip = ip
        self.url = url

        # Update the object's dictionary with any additional keyword arguments.
        self.__dict__.update(kwargs=kwargs)

    def __str__(self):
        """
        Return a string representation of the Network object.

        Returns:
            str: A string representation of the Network object.
        """
        return f"Network: {self.name} ({', '.join(self.nodes)})"


class QuantumNetwork(Network):
    """
    A class representing a quantum network, which is a type of classical network with additional qubits.
    """

    def __init__(self, name: str, nodes: list, qubits: int, ip: str, url: str, *args, **kwargs):
        """
        Initialize the QuantumNetwork object.

        Args:
            name (str): The name of the quantum network.
            nodes (list): A list of nodes in the network.
            qubits (int): The number of qubits in the quantum network.
            ip (str): The IP address of the quantum network.
            url (str): The URL of the quantum network.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Attributes:
            name (str): The name of the quantum network.
            nodes (list): A list of nodes in the quantum network.
            qubits (int): The number of qubits in the quantum network.
            ip (str): The IP address of the quantum network.
            url (str): The URL of the quantum network.
        """
        super().__init__(name, nodes, ip, url, *args, **kwargs)
        self.qubits = qubits

    def __str__(self):
        """
        Return a string representation of the QuantumNetwork object.

        Returns:
            str: A string representation of the QuantumNetwork object.
        """
        return f"Quantum Network: {self.name} ({', '.join(self.nodes)}), qubits: {self.qubits}"


class Protocol:
    """
    A singleton class representing a protocol that can be used on various networks.
    Attributes:
        networks (list): a list of networks that the protocol can run on.

    Methods:
        __call__: adds one or more networks to the protocol.
        __str__: returns a string representation of the protocol and its networks.
        __iter__: returns an iterator over the networks.
        __repr__: returns a string representation of the class.

    """
    networks = []

    def __new__(cls):
        """
        Returns the existing instance of the class if it exists, otherwise creates a new instance.

        """
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __call__(self, **kwargs):
        """
        Adds one or more networks to the protocol.

        Args:
            **kwargs: a dictionary containing information about one or more networks to be added.

        """
        classical_networks = kwargs.get('classical_networks', [])
        classical_networks = [Network(name=network['name'], nodes=network['nodes'], ip=network['ip'], url=network['url'], **kwargs) for network in classical_networks]
        self.networks.extend(classical_networks)

        quantum_networks = kwargs.get('quantum_networks', [])
        quantum_networks = [QuantumNetwork(name=network['name'], nodes=network['nodes'], ip=network['ip'], url=network['url'], qubits=network['qubits'], **kwargs) for network in quantum_networks]
        self.networks.extend(quantum_networks)

    def __str__(self):
        """
        Returns a string representation of the protocol and its networks.

        """
        network_strings = [str(network) for network in self.networks]
        return f"Protocol ({len(self.networks)} networks):\n" + "\n".join(network_strings)

    def __iter__(self):
        """
        Returns an iterator over the networks.

        """
        return iter(self.networks)

    def __repr__(self):
        """
        Returns a string representation of the class.

        """
        return f"{type(self).__name__}()"



# # Test Network class
# network = Network(name="Test Network", nodes=["Node 1", "Node 2"], ip="192.168.1.1", url="http://testnetwork.com")
# assert str(network) == "Network: Test Network (Node 1, Node 2)"

# # Test QuantumNetwork class
# quantum_network = QuantumNetwork(name="Test Quantum Network", nodes=["Node 1", "Node 2"], qubits=10, ip="192.168.1.1", url="http://testquantumnetwork.com")
# assert str(quantum_network) == "Quantum Network: Test Quantum Network (Node 1, Node 2), qubits: 10"

# # Test Protocol class
# protocol = Protocol()
# protocol(classical_networks=[{"name": "Test Network", "nodes": ["Node 1", "Node 2"], "ip": "192.168.1.1", "url": "http://testnetwork.com"}], quantum_networks=[{"name": "Test Quantum Network", "nodes": ["Node 1", "Node 2"], "qubits": 10, "ip": "192.168.1.1", "url": "http://testquantumnetwork.com"}])
# assert len(protocol.networks) == 2
# assert str(protocol) == "Protocol (2 networks):\nNetwork: Test Network (Node 1, Node 2)\nQuantum Network: Test Quantum Network (Node 1, Node 2), qubits: 10"

# # Test Protocol singleton behavior
# protocol1 = Protocol()
# protocol2 = Protocol()
# assert protocol1 is protocol2



# protocol = Protocol()
# protocol(classical_networks=[{'name': 'Net1', 'nodes': ['node1', 'node2'], 'ip': '192.168.0.1', 'url': 'http://example.com'},
#                              {'name': 'Net2', 'nodes': ['node3', 'node4'], 'ip': '192.168.0.2', 'url': 'http://example.com'}],
#          quantum_networks=[{'name': 'QNet1', 'nodes': ['node1', 'node2'], 'qubits': 3, 'ip': '192.168.0.1', 'url': 'http://example.com'},
#                            {'name': 'QNet2', 'nodes': ['node3', 'node4'], 'qubits': 2, 'ip': '192.168.0.2', 'url': 'http://example.com'}])

# print(protocol)  # Output: Protocol (4 networks):
#                  #         Network: Net1 (node1, node2)
#                  #         Network: Net2 (node3, node4)
#                  #         Quantum Network: QNet1 (node1, node2), qubits: 3
#                  #         Quantum Network: QNet2 (node3, node4), qubits: 2
