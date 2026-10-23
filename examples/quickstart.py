"""Minimal end-to-end example: obfuscate -> (untrusted compile) -> de-obfuscate."""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from cloaq import deobfuscate, functionally_equivalent, obfuscate, simulate, tvd

# a small circuit with X, CX, H and phase gates
qc = QuantumCircuit(3, 3)
qc.x(0)
qc.h(1)
qc.cx(1, 2)
qc.t(0)
qc.s(1)
qc.tdg(2)
qc.cx(0, 1)
qc.h(2)
qc.measure([0, 1, 2], [0, 1, 2])

circuit, logic_key, phase_key = obfuscate(qc, seed=7)
print(f"logic key bits: {len(logic_key)}, phase key bits: {len(phase_key)}")

# an untrusted compiler only ever sees `circuit` (never the keys)
compiled = transpile(circuit, AerSimulator(), optimization_level=0)

restored = deobfuscate(compiled, logic_key, phase_key)
print("exactly equivalent to original:", functionally_equivalent(restored, qc))
print("TVD original vs obfuscated    :", round(tvd(simulate(qc), simulate(circuit)), 3))
print("TVD original vs restored      :", round(tvd(simulate(qc), simulate(restored)), 3))
