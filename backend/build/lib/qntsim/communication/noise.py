'''
This file contains different noises, their description and python code to realize them.
Here following noises are included:
i. SPAM (State Preparation And Measurement)
'''

from enum import Enum
from .Error import NoiseError
    
_ATOL = 1e-6

# def __init__(self) -> None:
#     pass

# @staticmethod
def _check_probability(probabilities, tolerance):
    
    '''
    Check whether probabilities are valid or not (upto given tolerance).
    '''
    
    if not isinstance(probabilities, list):
        raise NoiseError("Probabilities should be a list")
    if not probabilities:
        raise NoiseError("Input probabilities: Empty")
    for p in probabilities:
        if isinstance(p, int) or isinstance(p, float):
            if p < -tolerance or p > 1 + tolerance:
                raise NoiseError(f"Probability {p} does not lie in the interval [0, 1]")
        else:
            raise NoiseError(f"Probability {p} is not a real number")
    if abs(sum(probabilities) - 1) > tolerance:
        raise NoiseError(f"Sum of the probabilities {probabilities} is not 1")
    pass

# @staticmethod
def _scale_probability(probabilities):
    
    '''
    Scales the probability values in proper range
    '''
    
    for i in range(len(probabilities)):
        if probabilities[i] < 0:
            probabilities[i] = 0
        if probabilities[i] > 1:
            probabilities[i] = 1
    s = sum(probabilities)
    if s - 1:
        for i in range(len(probabilities)):
            probabilities[i] /= s
    return probabilities

class ReadoutError:
    
    '''
    Readout error can be caracterised by following components:
    
    i. Probability of getting 0 when ideal measurement gives 0
    
    ii. Probability of getting 1 when ideal measurement gives 0
    
    iii. Probability of getting 0 when ideal measurement gives 1
    
    iv. Probability of getting 1 when ideal measurement gives 1
    
    Note that if 2nd and 3rd probability is given then other two probabilities can be found by
    subtracting them from 1.
    '''
    
    def __init__(self, p01, p10) -> None:
        '''
        Create a readout error for noise model
        
        Inputs:
            p01 [double]: Probability of getting 1 when ideal measurement gives 0
            p10 [double]: Probability of getting 0 when ideal measurement gives 1
        '''
        
        _check_probability(probabilities = [p01, 1 - p01], tolerance = _ATOL)
        _check_probability(probabilities = [p10, 1 - p10], tolerance = _ATOL)
        self.ideal = False
        if p01 + p10 < _ATOL:
            self.ideal = True
        self.probabilities = [_scale_probability([1 - p01, p01]), _scale_probability([p10, 1 - p10])]
        pass

class ResetError:
    
    '''
    Reset error can be characterised by following components:
    
    i. With probability :math:`p_0` qubit is reset to :math:`\\vert 0 \\rangle`
    
    ii. With probability :math:`p_1` qubit is reset to :math:`\\vert 1 \\rangle`
    
    iii. With probability :math:`1 - p_0 - p_1` no reset happens
    
    Therefore the error map will be :math:`E(\\rho) = (1 - p_0 - p_1) \\rho + \\left(p_0 \\vert 0 \\rangle\\langle 0 \\vert + p_1 \\vert 1 \\rangle\\langle 1 \\vert\\right)`
    '''
    
    def __init__(self, p0, p1) -> None:
        
        '''
        Create a reset error for noise model 
        
        Inputs:
            p0 [double]: Probability of resetting to :math:`\\vert 0 \\rangle`
            p1 [double]: Probability of resetting to :math:`\\vert 1 \\rangle`
        '''
        
        _check_probability(probabilities = [p0, p1, 1 - p0 - p1], tolerance = _ATOL)
        self.ideal = False
        if abs(p0 - 1) < _ATOL:
            self.ideal = True
        self.probabilities = _scale_probability([1 - p0 - p1, p0, p1])
        pass

class ERROR_TYPE(Enum):
    reset = ResetError
    readout = ReadoutError