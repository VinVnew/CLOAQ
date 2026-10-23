import pytest

from cloaq import functionally_equivalent, logic_deobfuscate, logic_obfuscate

SEEDS = range(15)


@pytest.mark.parametrize("seed", SEEDS)
def test_correct_key_restores_exactly(sample, seed):
    locked, key = logic_obfuscate(sample, seed=seed)
    assert functionally_equivalent(logic_deobfuscate(locked, key), sample)


def test_structure(sample):
    locked, key = logic_obfuscate(sample, n_bits=6, seed=3)
    assert locked.num_qubits == sample.num_qubits + 1
    assert locked.qregs[-1].name == "qk"
    assert len(key) == 6
    ops = locked.count_ops()
    assert ops["h"] - sample.count_ops()["h"] == 6  # one H on qk per key bit
    assert ops.get("ccx", 0) + ops.get("cx", 0) > sample.count_ops()["cx"]


def test_real_bits_use_controlled_gates(sample):
    locked, key = logic_obfuscate(sample, n_bits=12, seed=0, p_real=1.0)
    assert any(key)
    assert "ccx" in locked.count_ops()  # CX -> CCX


@pytest.mark.parametrize("seed", range(6))
def test_any_single_bit_flip_breaks_function(sample, seed):
    locked, key = logic_obfuscate(sample, seed=seed)
    for i in range(len(key)):
        bad = list(key)
        bad[i] ^= 1
        assert not functionally_equivalent(logic_deobfuscate(locked, bad), sample)


def test_keep_qk_mode_has_qk_and_x(sample):
    locked, key = logic_obfuscate(sample, seed=1)
    kept = logic_deobfuscate(locked, key, keep_qk=True)
    assert kept.num_qubits == sample.num_qubits + 1
    assert "h" in kept.count_ops()  # only the original H gates remain


def test_key_length_mismatch_raises(sample):
    locked, key = logic_obfuscate(sample, seed=0)
    with pytest.raises(ValueError):
        logic_deobfuscate(locked, key[:-1])
    with pytest.raises(ValueError):
        logic_deobfuscate(locked, [*key, 0])


def test_seed_reproducible(sample):
    a = logic_obfuscate(sample, seed=9)
    b = logic_obfuscate(sample, seed=9)
    assert a[1] == b[1] and a[0] == b[0]


def test_empty_circuit_raises():
    from qiskit import QuantumCircuit

    with pytest.raises(ValueError):
        logic_obfuscate(QuantumCircuit(2))
