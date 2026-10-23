"""Shared constants and circuit-plumbing helpers."""

from __future__ import annotations

from math import pi

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

#: Phase angles are quantised to 8 increments of pi/4 in [0, 2*pi).
STEP = pi / 4
#: Name of the ancilla key register added by logic obfuscation.
QK_NAME = "qk"


def qk_index(circuit: QuantumCircuit) -> int:
    """Index of the key qubit: the ``qk`` register if present, else the last qubit.

    Compilers may flatten register names, but ``qk`` is always appended last.
    """
    for reg in circuit.qregs:
        if reg.name == QK_NAME:
            return circuit.find_bit(reg[0]).index
    return circuit.num_qubits - 1


def without_qk(circuit: QuantumCircuit, qk_i: int, keep_qk: bool = False):
    """Empty circuit with the same data qubits/clbits, and a map old-index -> new qubit."""
    n_data = circuit.num_qubits - 1
    qregs = [QuantumRegister(n_data, "q")]
    if keep_qk:
        qregs.append(QuantumRegister(1, QK_NAME))
    cregs = [ClassicalRegister(r.size, r.name) for r in circuit.cregs]
    out = QuantumCircuit(*qregs, *cregs)
    qmap, j = {}, 0
    for i in range(circuit.num_qubits):
        if i == qk_i:
            if keep_qk:
                qmap[i] = out.qubits[n_data]
        else:
            qmap[i] = out.qubits[j]
            j += 1
    out.global_phase = circuit.global_phase
    return out, qmap
