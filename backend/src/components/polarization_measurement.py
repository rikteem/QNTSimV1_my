"""
Models a measurement device for polarization states of photons independent of the 
single photon detectors defined in detector.py.
"""

from ..components.photon import Photon
from backend.src.kernel.timeline import Timeline
from ..kernel.entity import Entity
from ..utils.encoding import polarization

import numpy

class PolarizationMeasurement(Entity):

    """
    Device for detection of polarization states of polarization encoded photons.
    Models a polarization beamsplitter followed by two single photon detectors. 

    Attributes:
        mode (int): 0/1 for measurement in computational / hadamard basis respectively
        power_loss (float): fraction of photons lost by the polarization beamsplitter
        detector_efficiency (float): quantumefficiency of the single photon detectors
        detector_dead_time (float): dead time of the attached single photon detectors
    """

    def __init__(self, name: str, timeline: Timeline, mode: int = 0, power_loss: float = 0, detector_efficiency: float = 1, detector_dead_time: float = 0):
        super().__init__(name, timeline)
        
        self.mode = mode
        self.power_loss = power_loss
        self.detector_efficiency = detector_efficiency
        self.detector_dead_time = detector_dead_time 

        self.last_detection_time = [-1,-1] # separate; for both detectors

    def receive_photon(self, photon: Photon) -> int:
        """
        Method to receive a photon for detection.

        Args:
            photon (Photon): polarization encoded photon for measurement 

        Returns:
            measurement_result (int): 0/1 if successful; -1 if no photon is detected (failure)
        """

        assert photon.encoding_type["name"] == "polarization"

        res = Photon.measure(polarization["bases"][self.mode], photon)

        if numpy.random.rand() > self.power_loss:
            if(self.single_photon_detection(photon,res) == True):
                return res
            else:
                return -1
        
    def single_photon_detection(self,photon: Photon, index:int) -> bool:
        """
        simulates single photon detection by the two (abstract) single photon detectors.

        Args:
            photon (Photon): photon for detection
            index (int): identifies which of the two detectors (0 or 1) will receive the photon

        Returns: bool (True or False depending on whether the detection was successful)

        """

        if(numpy.abs(self.last_detection_time[index] - self.timeline.now()) > self.detector_dead_time):
            if(numpy.random.rand() < self.detector_efficiency):

                self.last_detection_time[index] = self.timeline.now()
                del photon
                return True
        else:

            del photon
            return False
