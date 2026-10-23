"""High-level obfuscate / de-obfuscate API combining the logic and phase stages."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import RemoveBarriers

from .logic import logic_deobfuscate, logic_obfuscate
from .phase import phase_deobfuscate, phase_obfuscate

Mode = Literal["both", "logic", "phase"]


@dataclass
class ObfuscationResult:
    """Obfuscated circuit plus its secret key(s). Unpacks as ``circuit, logic_key, phase_key``."""

    circuit: QuantumCircuit
    logic_key: list[int] | None
    phase_key: list[int] | None

    def __iter__(self):
        yield self.circuit
        yield self.logic_key
        yield self.phase_key

    def key_dict(self) -> dict[str, list[int] | None]:
        """JSON-serialisable key."""
        return {"logic": self.logic_key, "phase": self.phase_key}


def obfuscate(
    circuit: QuantumCircuit,
    mode: Mode = "both",
    n_logic_bits: int | None = None,
    dummy_rate: float = 0.3,
    seed: int | None = None,
) -> ObfuscationResult:
    """Obfuscate ``circuit`` (logic stage first, then phase stage).

    Args:
        mode: ``"both"`` (CLOAQ), ``"logic"`` (logic only) or ``"phase"`` (phase only).
        n_logic_bits: Number of logic key bits (default: half the gate count).
        dummy_rate: Dummy phase-gate probability per idle qubit slot.
        seed: Seed for reproducibility.
    """
    if mode not in ("both", "logic", "phase"):
        raise ValueError(f"unknown mode {mode!r}")
    out, logic_key, phase_key = circuit, None, None
    if mode in ("both", "logic"):
        out, logic_key = logic_obfuscate(out, n_logic_bits, seed)
    if mode in ("both", "phase"):
        out, phase_key = phase_obfuscate(out, dummy_rate, seed)
    return ObfuscationResult(out, logic_key, phase_key)


def deobfuscate(
    circuit: QuantumCircuit,
    logic_key: list[int] | None = None,
    phase_key: list[int] | None = None,
    qk_idx: int | None = None,
) -> QuantumCircuit:
    """Undo obfuscation. Pass only the key(s) of the stages that were applied."""
    out = circuit
    if logic_key is not None:
        out = logic_deobfuscate(out, logic_key, qk_idx)
    if phase_key is not None:
        out = phase_deobfuscate(out, phase_key)
    return PassManager(RemoveBarriers()).run(out)


def wrong_key(key: list[int], rng: random.Random) -> list[int]:
    """Random key of the same length that differs from ``key`` in at least one bit."""
    if not key:
        return []
    while True:
        cand = [int(b ^ (rng.random() < 0.5)) for b in key]
        if cand != list(key):
            return cand
