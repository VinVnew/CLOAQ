import pytest
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister


@pytest.fixture
def sample():
    """4-qubit circuit exercising X, CX, H and every supported phase gate."""
    q, c = QuantumRegister(4, "q"), ClassicalRegister(4, "c")
    qc = QuantumCircuit(q, c)
    qc.x(0)
    qc.x(1)
    qc.h(3)
    qc.cx(2, 3)
    qc.t(0)
    qc.t(1)
    qc.t(2)
    qc.tdg(3)
    qc.cx(0, 1)
    qc.cx(2, 3)
    qc.s(3)
    qc.z(0)
    qc.sdg(1)
    qc.cx(3, 0)
    qc.cx(1, 2)
    qc.h(3)
    qc.measure(q, c)
    return qc


@pytest.fixture
def tiny():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.t(1)
    qc.h(1)
    qc.measure([0, 1], [0, 1])
    return qc
