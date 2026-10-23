import random

import pytest
from qiskit import transpile

from cloaq import deobfuscate, functionally_equivalent, obfuscate, wrong_key

aer = pytest.importorskip("qiskit_aer")


@pytest.mark.parametrize("mode", ["both", "logic", "phase"])
@pytest.mark.parametrize("seed", range(8))
def test_roundtrip(sample, mode, seed):
    res = obfuscate(sample, mode=mode, seed=seed)
    assert functionally_equivalent(deobfuscate(res.circuit, res.logic_key, res.phase_key), sample)


def test_mode_keys(sample):
    assert obfuscate(sample, "logic", seed=0).phase_key is None
    assert obfuscate(sample, "phase", seed=0).logic_key is None
    both = obfuscate(sample, "both", seed=0)
    assert both.logic_key and both.phase_key
    circuit, lk, pk = both  # tuple-style unpacking
    assert circuit is both.circuit and lk is both.logic_key and pk is both.phase_key


def test_unknown_mode_raises(sample):
    with pytest.raises(ValueError):
        obfuscate(sample, mode="nope")


@pytest.mark.parametrize("seed", range(8))
def test_survives_untrusted_compile(sample, seed):
    """Gate reordering by the compiler (opt level 0) must not break the key."""
    res = obfuscate(sample, seed=seed)
    compiled = transpile(res.circuit, aer.AerSimulator(), optimization_level=0)
    restored = deobfuscate(compiled, res.logic_key, res.phase_key)
    assert functionally_equivalent(restored, sample)


def test_wrong_keys_corrupt_output(sample):
    from cloaq import simulate, tvd

    ref = simulate(sample, 4096, seed=1)
    res = obfuscate(sample, seed=2)
    rng = random.Random(0)
    bad = deobfuscate(res.circuit, wrong_key(res.logic_key, rng), wrong_key(res.phase_key, rng))
    good = deobfuscate(res.circuit, res.logic_key, res.phase_key)
    assert tvd(ref, simulate(good, 4096, seed=1)) < 0.05
    assert not functionally_equivalent(bad, sample)


def test_wrong_key_differs():
    rng = random.Random(0)
    key = [0, 1, 1, 0]
    for _ in range(20):
        assert wrong_key(key, rng) != key
    assert wrong_key([], rng) == []
