"""Models simulation of wavepleates (half and quarter)"""

import heapq as hq
from typing import TYPE_CHECKING

#from numpy import random
from random import random
import numpy as np

if TYPE_CHECKING:
    from ..kernel.timeline import Timeline
    from ..topology.node import Node
    from ..components.photon import Photon
    from ..message import Message

from ..kernel.entity import Entity
from ..kernel._event import Event


class Waveplate(Entity):
    """Parent class for waveplates

    Attributes:
        name (str): label for channel instance.
        timeline (Timeline): timeline for simulation.
        angle (float): angle of waveplate in degrees
        power_loss (float): fraction of lost photons
        extinction_ratio (float): fraction of photons which pass through unaltered
    """

    def __init__(self, name: str, timeline: "Timeline", angle: float, power_loss: float = 0, extinction_ratio: float = 0):
        """Constructor for abstract Optical Channel class.

        Args:
            name (str): label for channel instance.
            timeline (Timeline): timeline for simulation
            angle (float): angle of waveplate in degrees
            power_loss (float): fraction of lost photons
            extinction_ratio (float): fraction of photons which pass through unaltered
        """

        Entity.__init__(self, name, timeline)
        self.angle = angle
        self.power_loss = power_loss
        self.extinction_ratio = extinction_ratio 


    def apply(self, qubit: "Photon") -> None:
        """Method to apply waveplate transformations to a photon
        """

        # check if photon kept
        if (random() > self.power_loss) or qubit.is_null:

            #check encoding
            if (qubit.encoding_type["name"] == "polarization"):

                #apply extinction ratio
                if(random() > self.extinction_ratio ):

                    #apply waveplate transformations
                    self.rotate(qubit)
                

            return qubit

        #if photon lost
        else:
            return None

    def rotate(self,qubit: Photon) -> None:
        
        cost = np.cos(self.angle*np.pi/180)
        sint = np.sin(self.angle*np.pi/180)
        U = np.array([[cost,-sint],[sint,cost]])  #waveplate transformation

        if(len(qubit.quantum_state.entangled_states) == 1):
            #if no entanglement, apply operator directly
            qubit.quantum_state.state = U@qubit.quantum_state.state

        else:
            #if entanglement is present, pad operator to the basis and then apply
            index = qubit.quantum_state.entangled_states.index(qubit.quantum_state)
            U_large = [1]
            for i in range(len(qubit.quantum_state.entangled_states)):
                if(index != i):
                    U_large = np.kron(U_large,np.eye(2))
                else:
                    U_large = np.kron(U_large,U)

            new_state = U_large@qubit.quantum_state.state

            for i in range(len(qubit.quantum_state.entangled_states)):
                qubit.quantum_state.entangled_states[i].state = new_state

class QuarterWaveplate(Waveplate):
    """
    Models a Quarter wave plate (Hadamard gate for polarization encoded photons). Rotates polarization of a photon by 45 degrees.
    
    Attributes:
        name (str)
        angle (float) = 45: Angle of the waveplate in degrees
        extinction_ratio (float): fraction of photons that pass unaltered
        power_loss (float): fraction of photons lost
    """
    def __init__(self, name: float, timeline, extinction_ratio: float = 0, power_loss: float = 0):
        super().__init__(name, timeline, 45, power_loss, extinction_ratio)


class HalfWaveplate(Waveplate):
    """
    Models a Half wave plate. Rotates polarization of a photon by 90 degrees.
    
    Attributes:
        name (str)
        angle (float) = 90: Angle of the waveplate in degrees
        extinction_ratio (float): fraction of photons that pass unaltered
        power_loss (float): fraction of photons lost
    """
    def __init__(self, name: float, timeline, extinction_ratio: float = 0, power_loss: float = 0):
        super().__init__(name, timeline, 90, power_loss, extinction_ratio)