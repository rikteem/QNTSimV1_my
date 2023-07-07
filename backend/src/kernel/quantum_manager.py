"""This module defines the quantum manager class, to track quantum states.
The states may currently be defined in two possible ways:
    - KetState (with the QuantumManagerKet class)
    - DensityMatrix (with the QuantumManagerDensity class)
The manager defines an API for interacting with quantum states.
"""

from abc import abstractmethod
from copy import copy
from typing import List, Dict, Tuple, TYPE_CHECKING
from math import sqrt

from qutip.qip.circuit import QubitCircuit, Gate
# from qutip.qip.operations import gate_qntsim_product
from numpy import log2, array, kron, identity, zeros, arange, outer
from numpy.random import random_sample, choice
from qiskit import *
from .quantum_utils import *
from qiskit import quantum_info


class QuantumManager():
    """Class to track and manage quantum states (abstract).
    All states stored are of a single formalism (by default as a ket vector).
    Attributes:
        states (Dict[int, KetState]): mapping of state keys to quantum state objects.
    """

    def __init__(self, formalism):
        self.states = {}
        self._least_available = 0
        self.formalism = formalism

    @abstractmethod
    def new(self, amplitudes: any) -> int:
        """Method to create a new quantum state.
        Args:
            amplitudes: complex amplitudes of new state. Type depends on type of subclass.
        Returns:
            int: key for new state generated.
        """
        pass

    def get(self, key: int) -> "State":
        """Method to get quantum state stored at an index.
        Args:
            key (int): key for quantum state.
        Returns:
            State: quantum state at supplied key.
        """
        return self.states[key]

    @abstractmethod
    def run_circuit(self, circuit: "Circuit", keys: List[int]) -> int:
        """Method to run a circuit on a given set of quantum states.
        Args:
            circuit (Circuit): quantum circuit to apply.
            keys (List[int]): list of keys for quantum states to apply circuit to.
        Returns:
            Dict[int, int]: dictionary mapping qstate keys to measurement results.
        """

        assert len(keys) == circuit.size, "mismatch between circuit size and supplied qubits"


    
    def _prepare_circuit(self, circuit: "Circuit", keys: List[int]):
        
        # Create a quantum circuit with or without classical measurement registers based on number of measured qubits
        if len(circuit.measured_qubits)>0:
            new_circuit = QuantumCircuit(ClassicalRegister(len(circuit.measured_qubits)))
        else:
            new_circuit = QuantumCircuit()

        # all the keys in the circuit. len(all_keys) > len(keys) because all_keys includes the qubits which some 
        # of the qubits in keys is entangled with. 
        all_keys = []

        # go through keys and get all unique qstate objects from the required keys
        for key in keys:
            qstate = self.states[key]

            # Check if you have added the state corresponding to the key in the circuit
            if int(qstate.qubits[0].register.name[2:]) not in all_keys:
                
                # Some qubits could be entangled with other states. For those states, you have to add all the 
                # entangled states to the present circuit. Hence, we check the keys and their corresponding states. 
                for i in qstate.qubits:
                    new_circuit.add_register(i.register)
                    all_keys.append(int(i.register.name[2:]))

                # To use old the qubits in the new circuit, you need to initialize them using their old state. 
                # We convert their old (collective) state into a (multi qubit) quantum instruction and append it to the circuit. 
                new_circuit.append(qstate.to_instruction(), list(range(new_circuit.num_qubits-qstate.num_qubits, new_circuit.num_qubits)) )

        # The keys list if smaller than the all_keys list. So, what you are doing here is 
        # bring all the all_keys elements (and corresponding qubits) as per the order in keys.
        # This makes applying the gates easier since you can apply the gates directly based on the 
        # index recieved from circuit definition
        for i, key in enumerate(keys):
            j = all_keys.index(key)
            if j != i:
                new_circuit.swap(i,j)
                all_keys[i], all_keys[j] = all_keys[j], all_keys[i]

        # Apply all the gates and measurements on the circuit
        circ = circuit.compile_circuit(new_circuit)

        return all_keys, circ

    @abstractmethod
    def set(self, keys: List[int], amplitudes: any) -> None:
        """Method to set quantum state at a given key(s).
        Args:
            keys (List[int]): key(s) of state(s) to change.
            amplitudes: Amplitudes to set state to, type determined by type of subclass.
        """

        num_qubits = log2(len(amplitudes))
        assert num_qubits.is_integer(), "Length of amplitudes should be 2 ** n, where n is the number of keys"
        num_qubits = int(num_qubits)
        assert num_qubits == len(keys), "Length of amplitudes should be 2 ** n, where n is the number of keys"

    def remove(self, key: int) -> None:
        """Method to remove state stored at key."""
        del self.states[key]


class QuantumManagerKet(QuantumManager):
    """Class to track and manage quantum states with the ket vector formalism."""

    def __init__(self):
        super().__init__("KET")

    def new(self, amplitudes=[complex(1), complex(0)]) -> int:        
        # key is unique to a qubit. Hence, a new unique key is generated everytime this funct. is called.
        key = self._least_available
        self._least_available += 1
        self.states[key] = QuantumCircuit(QuantumRegister(1, f"k_{key}"))
        return key

    def run_circuit(self, circuit: "Circuit", keys: List[int]) -> int:    
        super().run_circuit(circuit, keys)

        # Compile the circuit into Qiskit quanutm circuit
        all_keys, circ = self._prepare_circuit(circuit, keys)

        # If none of the qubits are measured
        if len(circuit.measured_qubits) == 0:

            # set state, return no measurement result
            for key in all_keys:
                self.states[key] = circ
            return None
        else:

            # measure state (state reassignment done in _measure method)
            keys = [all_keys[i] for i in circuit.measured_qubits]
            return self._measure(circ, keys, all_keys)

    def set(self, keys: List[int], amplitudes: List[complex]) -> None:
        qc = QuantumCircuit(*[QuantumRegister(1, f"k_{key}") for key in keys])
        qc.initialize(amplitudes, list(range(len(keys))))
        for key in keys:
            self.states[key] = qc

    def _measure(self, circ, keys: List[int], all_keys: List[int]) -> Dict[int, int]:
        """Method to measure qubits at given keys.
        SHOULD NOT be called individually; only from circuit method (unless for unit testing purposes).
        Modifies quantum state of all qubits given by all_keys.
        Args:
            circ (QuantumCircuit): Quantum Circuit to measure.
            keys (List[int]): list of keys to measure.
            all_keys (List[int]): list of all keys corresponding to circ.
        Returns:
            Dict[int, int]: mapping of measured keys to measurement results.
        """

        # Measure the circuit (qasm_simulator used to get counts of measurement)
        result = execute(circ, Aer.get_backend('qasm_simulator'), shots = 1).result().get_counts(circ)

        # Get the results as a list of digits 
        result_digits = list(map(int, list(result.keys())[0]))

        # Because of Qiskit's qubit numbering convention. 
        result_digits.reverse()

        # Set all the measured states to one of the comuptational basis depending on the measurmeent outcome
        for res, key in zip(result_digits, keys):
            self.states[key] = QuantumCircuit(QuantumRegister(1, f"k_{key}"))
            if res == 1:
                self.states[key].x(0)
        
        # if there are more qubits in the circuit than the number of measured qubits
        if len(all_keys) > len(keys):

            # Create a list of qubits that have been measured to partial trace them out. 
            measured_indices = [all_keys.index(key) for key in keys]

            # Run the statevector simulator to get the statevector of the circuit. 
            statevector = execute(circ, Aer.get_backend('statevector_simulator'), shots = 1).result().get_statevector(circ)
            
            # Partially trace out measured qubits. This works because the statevector produced in previous step 
            # already considers the wave function (and ultimately entanglement) collapse due to measurements 
            new_state = quantum_info.partial_trace(statevector, measured_indices).to_statevector().data

            for key in keys:
                all_keys.remove(key)

            # creating quantum circuits to reinitialize the unmeasured qubits
            qc = QuantumCircuit(*[QuantumRegister(1, f"k_{key}") for key in all_keys])
            
            # Initialize the qubits with their respective state vectors
            qc.initialize(new_state, list(range(len(all_keys))))

            # Assign quantum circuits to keys.
            for key in all_keys:
                self.states[key] = qc

        return dict(zip(keys, result_digits))


############ All the code below is not required and hence not editted ################

class QuantumManagerDensity(QuantumManager):
    """Class to track and manage states with the density matrix formalism."""

    def __init__(self):
        super().__init__("DENSITY")

    def new(self, state=[[complex(1), complex(0)], [complex(0), complex(0)]]) -> int:        
        key = self._least_available
        self._least_available += 1
        self.states[key] = DensityState(state, [key])
        return key

    def run_circuit(self, circuit: "Circuit", keys: List[int]) -> int:
        super().run_circuit(circuit, keys)
        new_state, all_keys, circ_mat = super()._prepare_circuit(circuit, keys)

        new_state = circ_mat @ new_state @ circ_mat.T

        if len(circuit.measured_qubits) == 0:
            # set state, return no measurement result
            new_state_obj = DensityState(new_state, all_keys)
            for key in all_keys:
                self.states[key] = new_state_obj
            return None
        else:
            # measure state (state reassignment done in _measure method)
            keys = [all_keys[i] for i in circuit.measured_qubits]
            return self._measure(new_state, keys, all_keys)

    def set(self, keys: List[int], state: List[List[complex]]) -> None:
        super().set(keys, state)
        new_state = DensityState(state, keys)
        for key in keys:
            self.states[key] = new_state


    def _measure(self, state: List[List[complex]], keys: List[int], all_keys: List[int]) -> Dict[int, int]:
        """Method to measure qubits at given keys.
        SHOULD NOT be called individually; only from circuit method (unless for unit testing purposes).
        Modifies quantum state of all qubits given by all_keys.
        Args:
            state (List[complex]): state to measure.
            keys (List[int]): list of keys to measure.
            all_keys (List[int]): list of all keys corresponding to state.
        Returns:
            Dict[int, int]: mapping of measured keys to measurement results.
        """

        if len(keys) == 1:
            if len(all_keys) == 1:
                prob_0 = measure_state_with_cache_density(tuple(map(tuple, state)))
                if random_sample() < prob_0:
                    result = 0
                    new_state = [[1, 0], [0, 0]]
                else:
                    result = 1
                    new_state = [[0, 0], [0, 1]]

            else:
                key = keys[0]
                num_states = len(all_keys)
                state_index = all_keys.index(key)
                state_0, state_1, prob_0 = measure_entangled_state_with_cache_density(tuple(map(tuple, state)),
                        state_index, num_states)
                if random_sample() < prob_0:
                    new_state = array(state_0, dtype=complex)
                    result = 0
                else:
                    new_state = array(state_1, dtype=complex)
                    result = 1

        else:
            # swap states into correct position
            if not all([all_keys.index(key) == i for i, key in enumerate(keys)]):
                all_keys, swap_mat = self._swap_qubits(all_keys, keys)
                state = swap_mat @ state @ swap_mat.T

            # calculate meas probabilities and projected states
            len_diff = len(all_keys) - len(keys)
            state_to_measure = tuple(map(tuple, state))
            new_states, probabilities = measure_multiple_with_cache_density(state_to_measure, len(keys), len_diff)

            # choose result, set as new state
            possible_results = arange(0, 2 ** len(keys), 1)
            result = choice(possible_results, p=probabilities)
            new_state = new_states[result]

        result_digits = [int(x) for x in bin(result)[2:]]
        while len(result_digits) < len(keys):
            result_digits.insert(0, 0)
       
        new_state_obj = DensityState(new_state, all_keys)
        for key in all_keys:
            self.states[key] = new_state_obj
    
        return dict(zip(keys, result_digits))


class KetState():
    """Class to represent an individual quantum state as a ket vector.
    Attributes:
        state (np.array): state vector. Should be of length 2 ** len(keys).
        keys (List[int]): list of keys (qubits) associated with this state.
    """

    def __init__(self, amplitudes: List[complex], keys: List[int]):
        # check formatting
        assert all([abs(a) <= 1.01 for a in amplitudes]), "Illegal value with abs > 1 in ket vector"
        assert abs(sum([a ** 2 for a in amplitudes]) - 1) < 1e-5, "Squared amplitudes do not sum to 1" 
        num_qubits = log2(len(amplitudes))
        assert num_qubits.is_integer(), "Length of amplitudes should be 2 ** n, where n is the number of qubits"
        assert num_qubits == len(keys), "Length of amplitudes should be 2 ** n, where n is the number of qubits"

        self.state = array(amplitudes, dtype=complex)
        self.keys = keys

    def __str__(self):
        return "\n".join(["Keys:", str(self.keys), "State:", str(self.state)])


class DensityState():
    """Class to represent an individual quantum state as a density matrix.
    Attributes:
        state (np.array): density matrix values. NxN matrix with N = 2 ** len(keys).
        keys (List[int]): list of keys (qubits) associated with this state.
    """

    def __init__(self, state: List[List[complex]], keys: List[int]):
        """Constructor for density state class.
        Args:
            state (List[List[complex]]): density matrix elements given as a list. If the list is one-dimensional, will be converted to matrix with outer product operation.
            keys (List[int]): list of keys to this state in quantum manager.
        """

        state = array(state, dtype=complex)
        if state.ndim == 1:
            state = outer(state.conj(), state)

        # check formatting
        assert abs(trace(array(state)) - 1) < 0.1, "density matrix trace must be 1"
        for row in state:
            assert len(state) == len(row), "density matrix must be square"
        num_qubits = log2(len(state))
        assert num_qubits.is_integer(), "Dimensions of density matrix should be 2 ** n, where n is the number of qubits"
        assert num_qubits == len(keys), "Dimensions of density matrix should be 2 ** n, where n is the number of qubits"

        self.state = state
        self.keys = keys

    def __str__(self):
        return "\n".join(["Keys:", str(self.keys), "State:", str(self.state)])