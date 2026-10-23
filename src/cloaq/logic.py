"""Step 1 - logic obfuscation with an ancilla key qubit ``qk``.

For every selected gate position one ``H`` is placed on ``qk`` (one key bit per ``H``):

* key bit 1 (*real*):  an ``X``/``CX`` is replaced by a ``CX``/``CCX`` controlled by ``qk``.
* key bit 0 (*dummy*): a ``CX(qk, t)`` is inserted; it is the identity while ``qk = |0>``.

With the wrong key ``qk`` is left in superposition and entangles with the data qubits.
De-obfuscation removes the ``H`` gates, sets ``qk`` to the key bit, strips the control from
real gates, drops dummy gates and removes ``qk``.
"""

from __future__ import annotations

import random

from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import ControlledGate, Gate

from ._common import QK_NAME, qk_index, without_qk

#: Gates that may be converted to a controlled version (X -> CX, CX -> CCX).
LOGIC_ELIGIBLE = frozenset({"x", "cx"})


def _strip_one_control(op):
    if not isinstance(op, ControlledGate):
        raise ValueError(f"gate '{op.name}' acting on qk is not a controlled gate")
    n = op.num_ctrl_qubits
    return op.base_gate if n == 1 else op.base_gate.control(n - 1)


def logic_obfuscate(
    circuit: QuantumCircuit,
    n_bits: int | None = None,
    seed: int | None = None,
    p_real: float = 0.5,
) -> tuple[QuantumCircuit, list[int]]:
    """Insert the ancilla ``qk`` and return ``(locked_circuit, logic_key)``.

    Args:
        circuit: Circuit to protect (measurements are left untouched).
        n_bits: Number of key bits / ``H`` gates. Defaults to half the gate count and is
            capped at the number of gates.
        seed: Seed for reproducible key generation.
        p_real: Probability that an eligible ``X``/``CX`` slot carries key bit 1.
    """
    rng = random.Random(seed)
    data = list(circuit.data)
    gate_idx = [i for i, ins in enumerate(data) if isinstance(ins.operation, Gate)]
    if not gate_idx:
        raise ValueError("circuit has no gates to obfuscate")
    eligible = {i for i in gate_idx if data[i].operation.name in LOGIC_ELIGIBLE}
    n_bits = max(1, len(gate_idx) // 2) if n_bits is None else min(n_bits, len(gate_idx))
    slots = sorted(rng.sample(gate_idx, n_bits))
    bit_at = {i: int(i in eligible and rng.random() < p_real) for i in slots}

    qk_reg = QuantumRegister(1, QK_NAME)
    qk = qk_reg[0]
    out = QuantumCircuit(*circuit.qregs, qk_reg, *circuit.cregs)
    out.global_phase = circuit.global_phase

    for i, ins in enumerate(data):
        op, qargs, cargs = ins.operation, ins.qubits, ins.clbits
        if i not in bit_at:
            out.append(op, qargs, cargs)
            continue
        if bit_at[i]:
            touched = list(dict.fromkeys(qargs))
            out.barrier(qk, *touched)
            out.h(qk)
            out.append(op.control(1), [qk, *qargs])
        else:
            tgt = rng.choice(list(circuit.qubits))
            touched = list(dict.fromkeys([*qargs, tgt]))
            out.barrier(qk, *touched)
            out.h(qk)
            out.cx(qk, tgt)
            out.append(op, qargs, cargs)
        out.barrier(qk, *touched)
    return out, [bit_at[i] for i in slots]


def logic_deobfuscate(
    circuit: QuantumCircuit,
    key: list[int],
    qk_idx: int | None = None,
    keep_qk: bool = False,
) -> QuantumCircuit:
    """Undo :func:`logic_obfuscate` with ``key``.

    By default the result is simplified and ``qk`` is removed. With ``keep_qk=True`` the
    ``H`` gates are replaced by ``X`` gates that prepare ``qk`` and the controlled gates are
    kept. Slot order is read along the ``qk`` wire, so it is invariant under compiler
    reordering of gates on other qubits.
    """
    qk_i = qk_index(circuit) if qk_idx is None else qk_idx
    out, qmap = without_qk(circuit, qk_i, keep_qk)
    k, state, cur = 0, 0, 0
    for ins in circuit.data:
        op = ins.operation
        qidx = [circuit.find_bit(q).index for q in ins.qubits]
        cl = [out.clbits[circuit.find_bit(c).index] for c in ins.clbits]
        if op.name == "barrier" and qk_i in qidx:
            continue
        if qk_i in qidx:
            if op.name == "h" and qidx == [qk_i]:
                if k >= len(key):
                    raise ValueError("logic key is shorter than the number of key slots")
                state = key[k]
                k += 1
                if keep_qk and state != cur:
                    out.x(qmap[qk_i])
                    cur = state
                continue
            if keep_qk:
                out.append(op, [qmap[i] for i in qidx], cl)
            elif state == 1:
                out.append(_strip_one_control(op), [qmap[i] for i in qidx[1:]])
            continue
        out.append(op, [qmap[i] for i in qidx], cl)
    if k != len(key):
        raise ValueError("logic key is longer than the number of key slots")
    return out
