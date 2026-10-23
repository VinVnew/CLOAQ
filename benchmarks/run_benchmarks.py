"""Reproduce the evaluation on QASMBench circuits and print a Markdown table.

    python benchmarks/run_benchmarks.py [--trials 20] [--shots 4096] [--seed 1]

QASMBench (https://github.com/pnnl/QASMBench) circuits are downloaded on first use into
``benchmarks/qasm/`` (git-ignored) and are not redistributed with this repository.
"""

from __future__ import annotations

import argparse
import random
import urllib.request
from pathlib import Path

from qiskit import qasm2, transpile
from qiskit_aer import AerSimulator

from cloaq import deobfuscate, functionally_equivalent, obfuscate, simulate, tvd, wrong_key

CIRCUITS = ["adder_n4", "basis_change_n3", "fredkin_n3", "wstate_n3"]
URL = "https://raw.githubusercontent.com/pnnl/QASMBench/master/small/{n}/{n}.qasm"
CACHE = Path(__file__).with_name("qasm")


def fetch(name: str) -> Path:
    path = CACHE / f"{name}.qasm"
    if not path.exists():
        CACHE.mkdir(exist_ok=True)
        urllib.request.urlretrieve(URL.format(n=name), path)
    return path


def evaluate(name: str, a: argparse.Namespace, rng: random.Random) -> str:
    qc = qasm2.load(str(fetch(name)), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    ref = simulate(qc, a.shots, a.seed)
    circ, lk, pk = obfuscate(qc, seed=a.seed)
    comp = transpile(circ, AerSimulator(), optimization_level=0)  # untrusted compile
    restored = deobfuscate(comp, lk, pk)

    def mean_tvd(bad_logic: bool, bad_phase: bool) -> float:
        vals = []
        for _ in range(a.trials):
            logic = wrong_key(lk, rng) if bad_logic else lk
            phase = wrong_key(pk, rng) if bad_phase else pk
            vals.append(tvd(ref, simulate(deobfuscate(comp, logic, phase), a.shots, a.seed)))
        return sum(vals) / len(vals)

    ok = tvd(ref, simulate(restored, a.shots, a.seed))
    return (
        f"| {name} | {len(lk)} | {len(pk)} | {functionally_equivalent(restored, qc)} | {ok:.3f} "
        f"| {mean_tvd(True, False):.3f} | {mean_tvd(False, True):.3f} "
        f"| {mean_tvd(True, True):.3f} |"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=20, help="wrong keys per cell")
    ap.add_argument("--shots", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    print(
        "| circuit | logic bits | phase bits | exact restore | TVD correct key "
        "| TVD wrong logic | TVD wrong phase | TVD wrong both |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for name in CIRCUITS:
        print(evaluate(name, a, rng))


if __name__ == "__main__":
    main()
