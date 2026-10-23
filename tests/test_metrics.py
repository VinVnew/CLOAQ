import pytest

from cloaq import simulate, tvd

pytest.importorskip("qiskit_aer")


def test_tvd_identical_and_disjoint():
    assert tvd({"00": 10}, {"00": 10}) == 0
    assert tvd({"00": 10}, {"11": 10}) == 1


def test_tvd_normalises_shot_counts():
    assert tvd({"0": 5, "1": 5}, {"0": 500, "1": 500}) == pytest.approx(0)


def test_tvd_partial_overlap_is_standard():
    # p=(0.5,0.5,0), q=(0.5,0,0.5) -> 0.5 * (0 + 0.5 + 0.5) = 0.5
    assert tvd({"a": 50, "b": 50}, {"a": 50, "c": 50}) == pytest.approx(0.5)


def test_tvd_in_unit_interval_for_wide_outputs():
    # 4-bit outputs must still be able to reach 1 (not 1/2**b)
    assert tvd({"0000": 1024}, {"1111": 1024}) == 1


def test_simulate_deterministic_circuit():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.x(0)
    qc.measure([0, 1], [0, 1])
    assert simulate(qc, 256, seed=1) == {"01": 256}
