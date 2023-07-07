from abc import ABC, abstractclassmethod
from typing import Any, Dict, Tuple

from qntsim.communication import Network


class Party(ABC):
    """Abstract base class for a party in a communication network."""

    node: str = None
    input_messages: Dict[Tuple, str] = None
    userID: str = None
    received_msgs: Dict[int, str] = None
    
    @abstractclassmethod
    def encode(cls, network: Network, returns: Any):
        """
        Abstract class method for encoding a message to be sent over the network.
        
        Args:
            network (Network): The communication network.
            returns (Any): Returns from the previous function call.
            
        Returns:
            The encoded message.
        """
        pass
    
    @abstractclassmethod
    def decode(cls, network: Network, returns: Any):
        """
        Abstract class method for decoding a received message from the network.
        
        Args:```
            network (Network): The communication network.
            returns (Any): Returns from the previous function call.
            
        Returns:
            The decoded message.
        """
        pass
    
    @abstractclassmethod
    def measure(cls, network:Network, returns:Any):
        """
        Abstract class method for performing measurements on qubits.
        
        Args:
            network (Network): The communication network.
            returns (Any): Returns from the previous function call.
            
        Returns:
            The measurement outcomes.
        """
        pass

    @classmethod
    def update_params(cls, **kwargs):
        for var, val in kwargs.items():
            setattr(cls, var, val)