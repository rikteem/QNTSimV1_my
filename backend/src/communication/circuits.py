from ..components.circuit import QutipCircuit


def bell_type_state_analyzer(num_qubits:int) -> QutipCircuit:
    """
    Returns a QutipCircuit for analyzing a Bell-type state of a given number of qubits.

    Args:
        num_qubits (int): Number of qubits in the Bell-type state.

    Returns:
        QutipCircuit: QutipCircuit for analyzing the Bell-type state.
    """
    qtc = QutipCircuit(num_qubits)
    for i in range(num_qubits-1, 0, -1):
        qtc.cx(0, i)
    qtc.h(0)
    for i in range(num_qubits):
        qtc.measure(i)
    
    return qtc

def xor_type_state_analyzer(num_qubits:int) -> QutipCircuit:
    qtc = QutipCircuit(num_qubits)
    for i in range(num_qubits-1):
        qtc.cx(i, num_qubits-1)
        qtc.h(i)
    for i in range(num_qubits):
        qtc.measure(i)
    return qtc