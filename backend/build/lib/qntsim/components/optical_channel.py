"""Models for simulation of optical fiber channels.

This module introduces the abstract OpticalChannel class for general optical fibers.
It also defines the QuantumChannel class for transmission of qubits/photons and the ClassicalChannel class for transmission of classical control messages.
OpticalChannels must be attached to nodes on both ends.
"""

import heapq as hq
from typing import TYPE_CHECKING

#from numpy import random
from random import random

if TYPE_CHECKING:
    from ..kernel.timeline import Timeline
    from ..topology.node import Node
    from ..components.photon import Photon
    from ..message import Message
    from ..network_management.request import RRPMsgType
from ..kernel.entity import Entity
from ..kernel._event import Event
from ..network_management.request import RRPMsgType


class OpticalChannel(Entity):
    """Parent class for optical fibers.

    Attributes:
        name (str): label for channel instance.
        timeline (Timeline): timeline for simulation.
        sender (Node): node at sending end of optical channel.
        receiver (Node): node at receiving end of optical channel.
        atteunuation (float): attenuation of the fiber (in dB/km).
        distance (int): length of the fiber (in m).
        polarization_fidelity (float): probability of no polarization error for a transmitted qubit.
        light_speed (float): speed of light within the fiber (in m/ps).
    """

    def __init__(self, name: str, timeline: "Timeline", attenuation: float, distance: int, polarization_fidelity: float, light_speed: float):
        """Constructor for abstract Optical Channel class.

        Args:
            name (str): name of the beamsplitter instance.
            timeline (Timeline): simulation timeline.
            attenuation (float): loss rate of optical fiber (in dB/km).
            distance (int): length of fiber (in m).
            polarization_fidelity (float): probability of no polarization error for a transmitted qubit.
            light_speed (float): speed of light within the fiber (in m/ps).
        """

        Entity.__init__(self, name, timeline)
        self.sender = None
        self.receiver = None
        self.attenuation = attenuation
        self.distance = distance  # (measured in m)
        self.polarization_fidelity = polarization_fidelity
        self.light_speed = light_speed # used for photon timing calculations (measured in m/ps)
        # self.chromatic_dispersion = kwargs.get("cd", 17)  # measured in ps / (nm * km)

    def init(self) -> None:
        pass

    def set_distance(self, distance: int) -> None:
        self.distance = distance


class QuantumChannel(OpticalChannel):
    """Optical channel for transmission of photons/qubits.

    Attributes:
        name (str): label for channel instance.
        timeline (Timeline): timeline for simulation.
        sender (Node): node at sending end of optical channel.
        receiver (Node): node at receiving end of optical channel.
        atteunuation (float): attenuation of the fiber (in dB/km).
        distance (int): length of the fiber (in m).
        polarization_fidelity (float): probability of no polarization error for a transmitted qubit.
        light_speed (float): speed of light within the fiber (in m/ps).
        loss (float): loss rate for transmitted photons (determined by attenuation).
        delay (int): delay (in ps) of photon transmission (determined by light speed, distance).
        frequency (float): maximum frequency of qubit transmission (in Hz).
    """

    def __init__(self, name: str, timeline: "Timeline", attenuation: float, distance: int, polarization_fidelity=1, light_speed=2e-4, frequency=8e7):
        """Constructor for Quatnum Channel class.

        Args:
            name (str): name of the quantum channel instance.
            timeline (Timeline): simulation timeline.
            attenuation (float): loss rate of optical fiber (in dB/km).
            distance (int): length of fiber (in m).
            polarization_fidelity (float): probability of no polarization error for a transmitted qubit (default 1).
            light_speed (float): speed of light within the fiber (in m/ps) (default 2e-4).
            frequency (float): maximum frequency of qubit transmission (in Hz) (default 8e7).
        """

        super().__init__(name, timeline, attenuation, distance, polarization_fidelity, light_speed)
        self.delay = 0
        self.loss = 1
        self.frequency = frequency  # maximum frequency for sending qubits (measured in Hz)
        self.send_bins = []

    def init(self) -> None:
        """Implementation of Entity interface (see base class)."""
        # print("type next:", type(self.distance), type(self.attenuation))
        self.delay = round(self.distance / float(self.light_speed))
        self.loss = 1 - 10 ** (self.distance * float(self.attenuation) / -10)

    def set_ends(self, sender: "Node", receiver: "Node") -> None:
        self.sender = sender
        self.receiver = receiver
        sender.assign_qchannel(self, receiver.name)

    def transmit(self, _from:str, qubit: "Photon", dst:str, app:str, source: "Node") -> None:
        """Method to transmit photon-encoded qubits.

        Args:
            qubit (Photon): photon to be transmitted.
            source (Node): source node sending the qubit.

        Side Effects:
            Receiver node may receive the qubit (via the `receive_qubit` method).
        """

        assert self.delay != 0 and self.loss != 1, "QuantumChannel init() function has not been run for {}".format(self.name)
        assert source == self.sender

        # remove lowest time bin
        if len(self.send_bins) > 0:
            time = -1

            while time < self.timeline.now():
                # #print(len(hq))
                # #print("time", time, len(self.send_bins), self.timeline.now())
                time_bin = hq.heappop(self.send_bins)
                time = int(time_bin * (1e12 / self.frequency))
            assert time == self.timeline.now(), "qc {} transmit method called at invalid time".format(self.name)

        # check if photon kept
        if (random() > self.loss) or qubit.is_null:
            # check if polarization encoding and apply necessary noise
            if (qubit.encoding_type["name"] == "polarization") and (
                    random() > self.polarization_fidelity):
                qubit.random_noise()

            # schedule receiving node to receive photon at future time determined by light speed
            future_time = self.timeline.now() + self.delay
            #process = Process(self.receiver, "receive_qubit", [source.name, qubit])
            #event = Event(future_time, process)
            event = Event(future_time, self.receiver, "receive_qubit", [_from, dst, app, qubit])
            #self.timeline.schedule(event)
            self.timeline.schedule_counter += 1
            self.timeline.events.push(event)

        # if photon lost, exit
        else:
            pass

    def schedule_transmit(self, min_time: int) -> int:
        """Method to schedule a time for photon transmission.

        Quantum Channels are limited by a frequency of transmission.
        This method returns the next available time for transmitting a photon.
        
        Args:
            min_time (int): minimum simulation time for transmission.

        Returns:
            int: simulation time for next available transmission window.
        """

        min_time = max(min_time, self.timeline.now())
        time_bin = min_time * (self.frequency / 1e12)
        if time_bin - int(time_bin) > 0.00001:
            time_bin = int(time_bin) + 1
        else:
            time_bin = int(time_bin)
        # #print("TIME BIN:", time_bin)
        # find earliest available time bin
        while time_bin in self.send_bins:
            time_bin += 1
        hq.heappush(self.send_bins, time_bin)

        # calculate time
        time = int(time_bin * (1e12 / self.frequency))
        return time


class ClassicalChannel(OpticalChannel):
    """Optical channel for transmission of classical messages.

    Classical message transmission is assumed to be lossless.

    Attributes:
        name (str): label for channel instance.
        timeline (Timeline): timeline for simulation.
        sender (Node): node at sending end of optical channel.
        receiver (Node): node at receiving end of optical channel.
        distance (float): length of the fiber (in m).
        light_speed (float): speed of light within the fiber (in m/ps).
        delay (float): delay in message transmission (default distance / light_speed).
    """

    def __init__(self, name: str, timeline: "Timeline", distance: int, delay=-1):
        """Constructor for Classical Channel class.

        Args:
            name (str): name of the classical channel instance.
            timeline (Timeline): simulation timeline.
            distance (int): length of the fiber (in m).
            delay (float): delay (in ps) of message transmission (default distance / light_speed).
        """

        super().__init__(name, timeline, 0, distance, 0, 2e-4)
        if delay == -1:
            self.delay = distance / self.light_speed
        else:
            self.delay = delay

    def set_ends(self, sender: "Node", receiver: "Node") -> None:
        self.sender = sender
        self.receiver = receiver
        sender.assign_cchannel(self, receiver.name)

    def transmit(self, message: "Message", source: "Node", priority: int) -> None:
        """Method to transmit classical messages.

        Args:
            message (Message): message to be transmitted.
            source (Node): node sending the message.
            priority (int): priority of transmitted message (to resolve message reception conflicts).

        Side Effects:
            Receiver node may receive the qubit (via the `receive_qubit` method).
        """
        # if message.msg_type== RRPMsgType.RESERVE:

            # #print("message type",message.msg_type ,source,self.sender)
        assert source == self.sender
        # if message.msg_type== RRPMsgType.RESERVE:

        #     #print("message type",message.msg_type,source,self.sender,self.receiver.name)
        future_time = round(self.timeline.now() + int(self.delay))
        #process = Process(self.receiver, "receive_message", [source.name, message])
        #event = Event(future_time, process, priority)
        #if hasattr(message, 'id'):
            #if message.id == 1:
                #print('ENT_GEN_SUCCESS_RESPONSE curr_node:', self.sender.name, ' dest: ', self.receiver.name, ' delay: ', self.delay, 'and expected message recv time: ', future_time)

            #if message.id == 2:
                #print('TASK_MANAGER_REQ_MESG curr_node:', self.sender.name, ' dest: ', self.receiver.name, ' delay: ', self.delay, 'and expected message recv time: ', future_time)

        event = Event(future_time,self.receiver, "receive_message", [source.name, message],priority)
        #self.timeline.schedule(event)
        self.timeline.schedule_counter += 1
        self.timeline.events.push(event)
