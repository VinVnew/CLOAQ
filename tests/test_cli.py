import json

import pytest
from qiskit import qasm2

from cloaq.cli import main

pytest.importorskip("qiskit_aer")
from cloaq import functionally_equivalent  # noqa: E402


def test_cli_roundtrip(sample, tmp_path):
    names = ("in.qasm", "locked.qasm", "k.json", "out.qasm")
    src, locked, key, back = (tmp_path / n for n in names)
    qasm2.dump(sample, src)
    assert main(["obfuscate", str(src), "-o", str(locked), "-k", str(key), "--seed", "3"]) == 0
    k = json.loads(key.read_text())
    assert k["logic"] and k["phase"]
    assert main(["deobfuscate", str(locked), "-k", str(key), "-o", str(back)]) == 0
    load = lambda p: qasm2.load(str(p), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)  # noqa: E731
    assert functionally_equivalent(load(back), sample)


def test_cli_evaluate(sample, tmp_path, capsys):
    src = tmp_path / "in.qasm"
    qasm2.dump(sample, src)
    assert main(["evaluate", str(src), "--trials", "2", "--shots", "512"]) == 0
    out = capsys.readouterr().out
    assert "logic" in out and "both" in out and "True" in out
