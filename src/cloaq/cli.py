"""Command line interface: ``cloaq obfuscate | deobfuscate | evaluate``."""

from __future__ import annotations

import argparse
import json
import random
import sys

from qiskit import QuantumCircuit, qasm2

from .pipeline import deobfuscate, obfuscate, wrong_key


def _load(path: str) -> QuantumCircuit:
    return qasm2.load(path, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)


def _cmd_obfuscate(a: argparse.Namespace) -> int:
    res = obfuscate(_load(a.input), a.mode, a.logic_bits, a.dummy_rate, a.seed)
    qasm2.dump(res.circuit, a.output)
    with open(a.key, "w") as fh:
        json.dump(res.key_dict(), fh)
    print(
        f"wrote {a.output} and {a.key} "
        f"(logic bits: {len(res.logic_key or [])}, phase bits: {len(res.phase_key or [])})"
    )
    return 0


def _cmd_deobfuscate(a: argparse.Namespace) -> int:
    with open(a.key) as fh:
        key = json.load(fh)
    out = deobfuscate(_load(a.input), key.get("logic"), key.get("phase"))
    qasm2.dump(out, a.output)
    print(f"wrote {a.output}")
    return 0


def _cmd_evaluate(a: argparse.Namespace) -> int:
    from .metrics import functionally_equivalent, simulate, tvd

    qc = _load(a.input)
    ref = simulate(qc, a.shots, a.seed)
    rng = random.Random(a.seed)
    print(f"{'mode':<8}{'bits L/P':>10}{'exact':>8}{'TVD (ok)':>10}{'TVD (wrong)':>13}")
    for mode in ("logic", "phase", "both"):
        res = obfuscate(qc, mode, seed=a.seed)
        lk, pk = res.logic_key, res.phase_key
        restored = deobfuscate(res.circuit, lk, pk)
        wrong = []
        for _ in range(a.trials):
            bad = deobfuscate(
                res.circuit,
                wrong_key(lk, rng) if lk is not None else None,
                wrong_key(pk, rng) if pk is not None else None,
            )
            wrong.append(tvd(ref, simulate(bad, a.shots, a.seed)))
        bits = f"{len(lk or [])}/{len(pk or [])}"
        ok = tvd(ref, simulate(restored, a.shots, a.seed))
        print(
            f"{mode:<8}{bits:>10}{functionally_equivalent(restored, qc)!s:>8}"
            f"{ok:>10.3f}{sum(wrong) / len(wrong):>13.3f}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cloaq", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("obfuscate", help="obfuscate an OpenQASM 2 circuit")
    o.add_argument("input")
    o.add_argument("-o", "--output", required=True)
    o.add_argument("-k", "--key", required=True, help="where to write the JSON key")
    o.add_argument("--mode", choices=["both", "logic", "phase"], default="both")
    o.add_argument("--logic-bits", type=int, default=None)
    o.add_argument("--dummy-rate", type=float, default=0.3)
    o.add_argument("--seed", type=int, default=None)
    o.set_defaults(func=_cmd_obfuscate)

    d = sub.add_parser("deobfuscate", help="restore a circuit with its key")
    d.add_argument("input")
    d.add_argument("-k", "--key", required=True)
    d.add_argument("-o", "--output", required=True)
    d.set_defaults(func=_cmd_deobfuscate)

    e = sub.add_parser("evaluate", help="TVD / equivalence report (needs qiskit-aer)")
    e.add_argument("input")
    e.add_argument("--shots", type=int, default=4096)
    e.add_argument("--trials", type=int, default=10, help="wrong keys per mode")
    e.add_argument("--seed", type=int, default=1)
    e.set_defaults(func=_cmd_evaluate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
