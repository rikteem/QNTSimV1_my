from .Error import NoiseError
from warnings import warn
from random import choices
    
_ATOL = 1e-6
_1qubit_gates = ['id', 'x', 'h', 'y', 'z', 's', 't', 'tdg', 'ry', 'rx', 'rz']
_2qubit_gates = ['cx', 'swap']
_3qubit_gates = ['ccx']

class noise_model:

    def __init__(self) -> None:
        
        '''
        This is the noise model to simulate different quantum noises like SPAM error, gate error, channel error etc.
        '''
        
        self._noise_instruction = {}
        self._noise_qubits = {}
        self._noise_gates = set()
        self._noise = set()
        pass

    def add_readout_error(self, err, qubit = None) -> None:
        
        '''
        Method to add readout error in noise model
        
        Inputs:
            err [ReadoutError]: <ReadoutError> instance
            qubit [list]: List containing qubits with readout error
        '''
        
        if err.ideal:
            warn("Readout error found as ideal... Discarding the error.")
        else:
            self._noise_instruction["ReadoutError"] = err
            if qubit:
                self._noise_qubits["ReadoutError"] = set(qubit)
            else:
                self._noise_qubits["ReadoutError"] = None
            self._noise = self._noise|set(["ReadoutError"])
        pass
    
    def add_reset_error(self, err, qubit = None) -> None:
        
        '''
        Method to add reset error in noise model
        
        Inputs:
            err [ResetError]: <ResetError> instance
            qubit [list]: List containing qubits with reset error
        '''
        
        if err.ideal:
            warn("Reset error found as ideal... Discarding the error.")
        else:
            self._noise_instruction["ResetError"] = err
            if qubit:
                self._noise_qubits["ResetError"] = set(qubit)
            else:
                self._noise_qubits["ResetError"] = None
            self._noise = self._noise|set(["ResetError"])
        pass

    def apply(self, qc, QNTSim = True):
        
        '''
        Method to apply noise model in a quantum circuit
        
        Inputs:
            qc [QuantumCircuit]: <QuantumCircuit> instance
            QNTSim [bool]: True/ False depending on the platform QNTSim/ Qiskit
            manager [quantum_manager]: <quantum_manager> for QNTSim
            keys [list]: List of keys to run the QuantumCircuit
        
        Returns:
            crc [QuantumCircuit]: <QuantumCircuit> instance
        '''
        
        if not QNTSim:
            from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
            q_reg = {}
            size = 0
            c_reg = []
            for qr in qc.qregs:
                q_reg[QuantumRegister(qr.size, qr.name)] = [size, size + qr.size]
                size += qr.size
            for cr in qc.cregs:
                c_reg.append(ClassicalRegister(cr.size, cr.name))
            q_r = list(q_reg.keys())
            crc = QuantumCircuit(q_r[0])
            for reg in q_r[1:] + c_reg:
                crc.add_register(reg)
#            if "ResetError" in self._noise:  # THIS IS ONLY FOR TESTING PURPOSE AND SHOULD BE REMOVED BEFORE APPLYING THE NOISE IN THE PROTOCOLS
#                crc = self._apply_reset_error(crc, crc.num_qubits)
            for d in qc._data:
                crc._data.append(d)
                # GATE NOISE WILL BE ADDED HERE
                if d.operation.name == 'measure' and "ReadoutError" in self._noise and self._is_noisy(q_reg, d.qubits[0], "ReadoutError"):
                    crc = self._apply_readout_error_qiskit(crc, d)
            return crc
        from qntsim.components.circuit import QutipCircuit
        crc = QutipCircuit(qc.size)
#        if "ResetError" in self._noise:  # THIS IS ONLY FOR TESTING PURPOSE AND SHOULD BE REMOVED BEFORE APPLYING THE NOISE IN THE PROTOCOLS
#            crc = self._apply_reset_error(crc, crc.size)
        for gate in qc.gates:
            crc.gates.append(gate)
        crc.measured_qubits = qc.measured_qubits
        return crc
    
    def _is_noisy(self, reg, qubit_data, err):
        
        '''
        Method to check whether the qubit for the provided data is noisy or not
        '''
        
        qubit = reg[qubit_data._register][0] + qubit_data._index
        if self._noise_qubits and qubit not in self._noise_qubits[err]:
            return False
        return True
    
    def _apply_reset_error(self, crc, size):
        
        '''
        Method to apply reset error
        '''
        
        for qubit in range(size):
            if choices(range(3), self._noise_instruction["ResetError"].probabilities)[0] == 2:
                crc.x(qubit)
        return crc

    def _apply_readout_error_qiskit(self, crc, data):
        
        '''
        Method to apply readout error on qiskit
        '''
        
        flag = False
        for i in range(2):
            if choices(range(2), self._noise_instruction["ReadoutError"].probabilities[i])[0] - i:
                flag = True
                crc.x(data.qubits).c_if(data.clbits[0], i)
        if flag:
            crc._data.append(data)
        return crc
    
    def _apply_readout_error_qntsim(self, crc, manager, keys):
        
        '''
        Method to apply readout error on QNTSim
        '''
        
        from qntsim.components.circuit import QutipCircuit
#        for key in keys:  # THIS FOR LOOP IS ONLY FOR TESTING PURPOSE AND SHOULD BE REMOVED BEFORE APPLYING THE NOISE IN THE PROTOCOLS
#            states = manager.get(key).state
#            if states[1]:
#                qc = QutipCircuit(1)
#                qc.x(0)
#                qc.measure(0)
#                manager.run_circuit(qc, [key])
        result = manager.run_circuit(crc, keys)
        if not crc.measured_qubits:
            return
        if "ReadoutError" not in self._noise:
            return result
        for key in list(result.keys()):
            if self._noise_qubits["ReadoutError"] and key not in self._noise_qubits["ReadoutError"]:
                continue
            flag = False
            for i in range(2):
                if choices(range(2), self._noise_instruction["ReadoutError"].probabilities[i])[0] - i and result[key] == i:
                    flag = True
            if flag:
                result[key] = 1 - result[key]
                qc = QutipCircuit(1)
                qc.x(0)
                qc.measure(0)
                manager.run_circuit(qc, [key])
        return result
