"""Evaluation helpers: total variation distance, exact equivalence, simulation."""

from __future__ import annotations

from qiskit import QuantumCircuit, transpile


def tvd(counts_a: dict[str, int], counts_b: dict[str, int]) -> float:
    """Total variation distance ``0.5 * sum_i |p_i - q_i|`` in [0, 1] from raw counts."""
    na, nb = sum(counts_a.values()), sum(counts_b.values())
    keys = set(counts_a) | set(counts_b)
    return 0.5 * sum(abs(counts_a.get(k, 0) / na - counts_b.get(k, 0) / nb) for k in keys)


def functionally_equivalent(a: QuantumCircuit, b: QuantumCircuit) -> bool:
    """Exact unitary equality up to global phase, ignoring measurements and barriers."""
    from qiskit.quantum_info import Operator

    def strip(c: QuantumCircuit) -> QuantumCircuit:
        out = QuantumCircuit(*c.qregs)
        for ins in c.data:
            if ins.operation.name not in ("measure", "barrier"):
                out.append(ins.operation, ins.qubits)
        return out

    return Operator(strip(a)).equiv(Operator(strip(b)))


def simulate(circuit: QuantumCircuit, shots: int = 4096, seed: int | None = None) -> dict[str, int]:
    """Run ``circuit`` on the Aer simulator (requires ``qiskit-aer``) and return counts."""
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:  # pragma: no cover
        raise ImportError("simulate() needs qiskit-aer: pip install 'cloaq[sim]'") from exc
    backend = AerSimulator()
    compiled = transpile(circuit, backend, optimization_level=0)
    return backend.run(compiled, shots=shots, seed_simulator=seed).result().get_counts()
