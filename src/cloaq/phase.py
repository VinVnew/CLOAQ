"""Step 2 - phase (angle) obfuscation.

Every uncontrolled phase gate (Z, S, Sdg, T, Tdg, P, Rz) becomes ``P(decoy)``. Its true angle
``kappa * pi/4`` (``kappa`` in 0..7) is stored as 3 key bits. Dummy ``P`` gates with random
angles are added on idle qubits and carry key ``000`` (``P(0)`` is removed on de-obfuscation).

Rz(a) is replaced by P(a); the two differ only by a global phase.

The key is ordered by (qubit index, position along that qubit's wire), which a compiler
cannot change by reordering gates on different qubits.
"""

from __future__ import annotations

import random
from math import pi

from qiskit import QuantumCircuit

from ._common import QK_NAME, STEP

PHASE_ANGLE = {"z": pi, "s": pi / 2, "sdg": -pi / 2, "t": pi / 4, "tdg": -pi / 4}
PHASE_NAMES = frozenset(PHASE_ANGLE) | {"p", "rz"}


def key_phase(bits: str) -> float:
    """3-bit string -> angle ``k * pi/4`` (``'000'`` -> 0, ``'001'`` -> pi/4, ...)."""
    return int(bits, 2) * STEP


def _kappa(op) -> int:
    angle = PHASE_ANGLE[op.name] if op.name in PHASE_ANGLE else float(op.params[0])
    k = angle / STEP
    if abs(k - round(k)) > 1e-9:
        raise ValueError(
            f"{op.name}({angle:.4f}) is not a multiple of pi/4 and cannot be encoded in 3 key bits"
        )
    return round(k) % 8


def _bits3(k: int) -> list[int]:
    return [int(b) for b in format(k, "03b")]


def phase_obfuscate(
    circuit: QuantumCircuit, dummy_rate: float = 0.3, seed: int | None = None
) -> tuple[QuantumCircuit, list[int]]:
    """Return ``(obfuscated_circuit, phase_key)`` (3 key bits per ``P`` gate).

    Args:
        dummy_rate: Probability of adding a dummy ``P`` on each idle qubit in a layer.
        seed: Seed for reproducible decoys and dummies.
    """
    rng = random.Random(seed)
    qk_bits = {r[0] for r in circuit.qregs if r.name == QK_NAME}

    depth: dict = {}
    layers: list[list] = []
    for ins in circuit.data:
        bits = [*ins.qubits, *ins.clbits]
        layer = max((depth.get(b, 0) for b in bits), default=0)
        for b in bits:
            depth[b] = layer + 1
        while len(layers) <= layer:
            layers.append([])
        layers[layer].append(ins)

    out = QuantumCircuit(*circuit.qregs, *circuit.cregs)
    out.global_phase = circuit.global_phase
    entries: list[tuple[int, int, list[int]]] = []
    seq: dict[int, int] = {}
    measured: set = set()  # no dummies after a qubit has been measured

    def emit_p(q, beta: int, kappa: int) -> None:
        out.barrier(q)
        out.p(beta * STEP, q)
        out.barrier(q)
        qi = circuit.find_bit(q).index
        entries.append((qi, seq.get(qi, 0), _bits3(kappa)))
        seq[qi] = seq.get(qi, 0) + 1

    for layer in layers:
        used, has_measure = set(), False
        for ins in layer:
            op, qargs, cargs = ins.operation, ins.qubits, ins.clbits
            used.update(qargs)
            if op.name == "measure":
                has_measure = True
                measured.update(qargs)
            if op.name in PHASE_NAMES and len(qargs) == 1:
                kappa = _kappa(op)
                decoy = rng.choice([b for b in range(8) if b != kappa])
                emit_p(qargs[0], decoy, kappa)
            else:
                out.append(op, qargs, cargs)
        if not has_measure:
            for q in circuit.qubits:
                if (
                    q not in used
                    and q not in qk_bits
                    and q not in measured
                    and rng.random() < dummy_rate
                ):
                    emit_p(q, rng.randrange(1, 8), 0)

    key = [b for _, _, bits in sorted(entries, key=lambda e: e[:2]) for b in bits]
    return out, key


def phase_deobfuscate(circuit: QuantumCircuit, key: list[int]) -> QuantumCircuit:
    """Set every ``P`` gate to ``kappa * pi/4`` from its key bits (``kappa = 0`` removes it)."""
    count: dict[int, int] = {}
    for ins in circuit.data:
        if ins.operation.name == "p" and len(ins.qubits) == 1:
            qi = circuit.find_bit(ins.qubits[0]).index
            count[qi] = count.get(qi, 0) + 1
    offset, total = {}, 0
    for qi in sorted(count):
        offset[qi] = total
        total += count[qi]
    if 3 * total != len(key):
        raise ValueError(f"phase key has {len(key)} bits but the circuit has {total} P gates")

    out = QuantumCircuit(*circuit.qregs, *circuit.cregs)
    out.global_phase = circuit.global_phase
    seen: dict[int, int] = {}
    for ins in circuit.data:
        op = ins.operation
        if op.name == "p" and len(ins.qubits) == 1:
            qi = circuit.find_bit(ins.qubits[0]).index
            j = offset[qi] + seen.get(qi, 0)
            seen[qi] = seen.get(qi, 0) + 1
            kappa = int("".join(map(str, key[3 * j : 3 * j + 3])), 2)
            if kappa:
                out.p(kappa * STEP, ins.qubits[0])
        else:
            out.append(op, ins.qubits, ins.clbits)
    return out
