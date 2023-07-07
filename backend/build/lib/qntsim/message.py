"""Definition of abstract message type."""

from enum import Enum
from abc import ABC
#from .network_management.request import Request

class Message(ABC):
    """Abstract message type inherited by protocol messages."""

    def __init__(self, msg_type: Enum, receiver: str ):
        self.id = None
        self.msg_type = msg_type
        self.receiver = receiver
        self.payload = None


