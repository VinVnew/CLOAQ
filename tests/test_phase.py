from math import pi

import pytest
from qiskit import QuantumCircuit

from cloaq import functionally_equivalent, key_phase, phase_deobfuscate, phase_obfuscate

PHASE_ORIG = {"t", "tdg", "s", "sdg", "z", "rz"}


@pytest.mark.parametrize("seed", range(15))
def test_correct_key_restores_exactly(sample, seed):
    obf, key = phase_obfuscate(sample, seed=seed)
    assert functionally_equivalent(phase_deobfuscate(obf, key), sample)


def test_all_phase_gates_replaced_by_p(sample):
    obf, key = phase_obfuscate(sample, dummy_rate=0.0, seed=0)
    ops = obf.count_ops()
    assert not PHASE_ORIG & set(ops)
    assert ops["p"] == 7  # t,t,t,tdg,s,z,sdg
    assert len(key) == 3 * 7


def test_decoys_never_equal_true_angle(sample):
    obf, _ = phase_obfuscate(sample, dummy_rate=0.0, seed=4)
    assert not functionally_equivalent(obf, sample)


@pytest.mark.parametrize("seed", range(6))
def test_any_single_bit_flip_breaks_function(sample, seed):
    obf, key = phase_obfuscate(sample, seed=seed)
    for i in range(len(key)):
        bad = list(key)
        bad[i] ^= 1
        assert not functionally_equivalent(phase_deobfuscate(obf, bad), sample)


def test_dummies_removed_and_none_after_measure():
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.t(0)
    qc.cx(0, 1)
    qc.measure(0, 0)
    for _ in range(4):
        qc.x(2)
    qc.measure([1, 2], [1, 2])
    obf, key = phase_obfuscate(qc, dummy_rate=1.0, seed=0)
    restored = phase_deobfuscate(obf, key)
    assert restored.count_ops().get("p", 0) == 1  # only the real T survives
    # no P gate may follow the measurement of its qubit
    measured = set()
    for ins in obf.data:
        if ins.operation.name == "measure":
            measured.update(obf.find_bit(q).index for q in ins.qubits)
        elif ins.operation.name == "p":
            assert obf.find_bit(ins.qubits[0]).index not in measured


def test_key_order_survives_gate_reordering():
    """Key must not depend on the order of gates on different qubits."""
    qc = QuantumCircuit(2)
    qc.t(0)
    qc.s(1)
    qc.h(0)
    qc.h(1)
    qc.tdg(0)
    qc.z(1)
    obf, key = phase_obfuscate(qc, dummy_rate=0.0, seed=2)
    # swap the instruction order of independent gates on q0 and q1
    swapped = QuantumCircuit(*obf.qregs)
    q0 = [i for i in obf.data if obf.find_bit(i.qubits[0]).index == 0]
    q1 = [i for i in obf.data if obf.find_bit(i.qubits[0]).index == 1]
    for ins in q1 + q0:
        swapped.append(ins.operation, ins.qubits)
    assert functionally_equivalent(phase_deobfuscate(swapped, key), qc)


def test_unsupported_angle_raises():
    qc = QuantumCircuit(1)
    qc.rz(0.123, 0)
    with pytest.raises(ValueError, match="multiple of pi/4"):
        phase_obfuscate(qc)


def test_rz_and_p_supported():
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.rz(pi / 2, 0)
    qc.p(3 * pi / 4, 0)
    qc.h(0)
    obf, key = phase_obfuscate(qc, dummy_rate=0, seed=1)
    assert functionally_equivalent(phase_deobfuscate(obf, key), qc)


def test_key_length_mismatch_raises(sample):
    obf, key = phase_obfuscate(sample, seed=0)
    with pytest.raises(ValueError):
        phase_deobfuscate(obf, key[:-3])


def test_key_phase_mapping():
    assert key_phase("000") == 0
    assert key_phase("001") == pi / 4
    assert key_phase("111") == 7 * pi / 4
