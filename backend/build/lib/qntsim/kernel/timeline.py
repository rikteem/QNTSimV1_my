"""Definition of main Timeline class.

This module defines the Timeline class, which provides an interface for the simulation kernel and drives event execution.
All entities are required to have an attached timeline for simulation.
"""

from _thread import start_new_thread
from math import inf
from sys import stdout
from time import time_ns, sleep
from typing import TYPE_CHECKING

from numpy import random
from sympy import false

if TYPE_CHECKING:
    from ._event import Event

from .kernel_utils import EventList
from ..utils import log
from .quantum_kernel import QuantumKernel
from .quantum_manager import QuantumManagerDensity
import logging
logger = logging.getLogger("main_logger." + "timeline")

"""
ch=input("Enter 0 for DLCZ ,1 for barettkok")
if ch=='0':
    DLCZ=True
    bk=False
    print("DLCZ input value",DLCZ)
else:
    DLCZ=False
    bk=True
    print("DLCZ input value",DLCZ)
"""
#DLCZ=False
#bk=False 
#if not DLCZ:
    #bk=True
#else:
    #bk=False


class Timeline:
    DLCZ=False
    bk=True


    def __init__(self, stop_time=inf,backend=str, formalism='ket_vector'):
        
        self.events = EventList()
        self.entities = []
        self.time = 0
        self.stop_time = stop_time
        self.schedule_counter = 0
        self.run_counter = 0
        self.is_running = False
        
        self.type=backend

        if formalism == 'ket_vector':
            #self.quantum_manager =QuantumKernel.create("Qutip")()
            #print('timeline manager',QuantumKernel.create(self.type))
            #self.quantum_manager =QuantumKernel.create(self.type)()
            self.quantum_manager =QuantumKernel.create(self.type)()
            #self.quantum_manager = QuantumManagerKet()
        elif formalism == 'density_matrix':
            self.quantum_manager = QuantumManagerDensity()
        else:
            raise ValueError(f"Invalid formalism {formalism}")

    def now(self) -> int:
        """Returns current simulation time."""

        return self.time

    def init(self) -> None:
        """Method to initialize all simulated entities."""
        log.logger.info("Timeline initial network")
        for entity in self.entities:
            entity.init()

    def run(self) -> None:
        """Main simulation method.

        The `run` method begins simulation of events.
        Events are continuously popped and executed, until the simulation time limit is reached or events are exhausted.
        A progress bar may also be displayed, if the `show_progress` flag is set.
        """
        log.logger.info("Timeline start simulation")
        
        logger.info("Timeline started simulation ")
        tick = time_ns()
        self.is_running = True

        while len(self.events) > 0:
        #while True:
            event = self.events.pop()

            if event.time >= self.stop_time:
                #self.schedule(event)
                self.schedule_counter += 1
                self.events.push(event)
                break

            assert self.time <= event.time, f"invalid event time for process scheduled on {event.owner}"
            
            #if event.is_invalid():
            if event._is_removed:
                continue

            self.time = event.time
            
            event.run()

            self.run_counter += 1
            # print(f'The event-queue is: {self.events.filter_events()}')

       
        self.is_running = False
        time_elapsed = time_ns() - tick
        log.logger.info("Timeline end simulation. Execution Time: %d ns; Scheduled Event: %d; Executed Event: %d" %
                        (time_elapsed, self.schedule_counter, self.run_counter))

    def stop(self) -> None:
        """Method to stop simulation."""
        log.logger.info("Timeline is stopped")
        self.stop_time = self.now()


    
    