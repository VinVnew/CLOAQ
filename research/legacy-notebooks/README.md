# Legacy research notebooks (archive)

These notebooks are the experiments that led to the `cloaq` package. They are kept **for
provenance and understanding only**; the maintained implementation is in [`src/cloaq/`](../../src/cloaq).

* Saved outputs were cleared (28.7 MB -> 0.6 MB) and local file paths removed. Re-run them to
  regenerate results; QASMBench paths (`QASMBench/small/<name>/<name>.qasm`) are relative to your
  own checkout of [QASMBench](https://github.com/pnnl/QASMBench).
* Each notebook starts with an "ARCHIVED" banner cell; nothing else in the code was changed.
* Most notebooks repeat the same helper functions (copy-paste per circuit), which is one reason
  the package exists.
* Requires `qiskit`, `qiskit-aer`; some also import `qiskit_ibm_runtime` (`FakeManila`).

## Evolution of the approach

1. **XOR baseline** (`xor_only/`) - wrap every gate in `X` gates on its qubits.
2. **Phase walls** (`phase_only/`) - split the circuit into phase-only and non-phase-only layers
   separated by barriers, plus a random `U3` layer at the start; later variants add `add_u3` /
   `add_xor` flags and report mean TVD over many trials.
3. **Combined** (`combined/`) - XOR + phase walls, then ancilla-key logic locking ("QLL": `H` on `qk`,
   controlled gates, dummy gates) + phase walls, culminating in the integrated "CLOAQ" prototype.
4. **`cloaq` package** - the corrected, tested, keyed implementation of the poster's scheme.

## Contents

### `xor_only/` - XOR locking baseline
`xor_{adder_n4, basis_change_n3, basis_trotter_n4, fredkin_n3, wstate_n3}.ipynb`
Applies "XOR obfuscation" by wrapping each gate with `X` gates on all its qubits (the notebooks
report the number of qubits involved as the "key bits"). Compares the obfuscated circuit's output
to the original via TVD over repeated runs.

### `phase_only/` - phase walls (+ random U3)
| notebook | what it is |
|---|---|
| `phase_walls_{basis_change_n3, basis_trotter_n4, fredkin_n3, wstate_n3}.ipynb` | `transform_circuit` puts phase gates (Rz, P, S, T, ...) and non-phase gates in separate layers with barriers; optional random `U3` prefix. |
| `u3_phase_xor_adder_n4.ipynb`, `u3_phase_xor_wstate_n3_tvd.ipynb` | later variant: `add_u3`, phase walls and `add_xor` in one function; mean TVD over trials. |
| `batch_tvd_script_BROKEN.ipynb` | batch TVD histogram (100 trials x 5 circuits) for the random-`U3` prefix. Does not run as saved (see below). |

### `combined/`
| notebook | what it is |
|---|---|
| `xor_plus_phase_adaptive.ipynb` | XOR + phase walls with an adaptive intensity "knob" and dummy `I` gates. |
| `qll_plus_phase_walls.ipynb` | ancilla-key logic locking + phase walls on `adder_n4` (the notebook reviewed and rewritten as the package). |
| `qll_plus_phase_small_test.ipynb` | small-circuit test of the same QLL + phase-wall pipeline. |
| `cloaq_integrated_prototype.ipynb` | integrated QLL + per-gate phase randomization prototype ("CLOAQ"). |

## How the notebooks map to the package

| notebook idea | in `cloaq` |
|---|---|
| ancilla `qk`, `H` per key bit, `X -> CX`, dummy `CX` | `logic_obfuscate` / `logic_deobfuscate` |
| phase walls, per-gate angle randomisation | `phase_obfuscate` / `phase_deobfuscate` (3-bit keys, decoy angles, dummy `P`) |
| per-notebook TVD helper | `cloaq.tvd` (standard `0.5*sum|p-q|`) |
| "restored == original" check by gate counts / `Match` printouts | `functionally_equivalent` (exact unitary check) |
| per-circuit notebooks | `benchmarks/run_benchmarks.py` |

The XOR baseline and `basis_trotter_n4` are **not** yet in the package benchmarks.

## Known issues (why these are archived, not maintained)

Verified while reviewing the notebooks:

* **`combined/qll_plus_phase_walls.ipynb`** - de-obfuscation did not restore the circuit:
  an extra `X` is inserted instead of converting the gate to a controlled one, the non-first dummy
  `CX, X(qk), CX` is not identity, the phase lock only edits `rz` while the circuit contains `p`,
  the phase unlock is a no-op after barriers are stripped, the TVD "original" is the already
  obfuscated circuit, and the TVD formula divides by `2^bits`. All fixed in the package.
* **`combined/xor_plus_phase_adaptive.ipynb`** - the "Original vs Restored" TVD uses a placeholder
  (`qc_restored = transform_circuit(qc_locked)`), which re-obfuscates the locked circuit instead of
  restoring it, so that number is not a restoration result.
* **`phase_only/phase_walls_basis_trotter_n4.ipynb`** - `qc_original` is loaded from `adder_n4`
  while `qc` is `basis_trotter_n4`, so the comparison cell mixes circuits.
* **`phase_only/batch_tvd_script_BROKEN.ipynb`** - hard-coded Windows path (replaced by a
  placeholder here), the first `main()` references an undefined `benchmark_files` and is
  overridden by a second `main()`, the obfuscation is a random `U3` prefix with no key or restore,
  and TVD divides by the shot count assuming both runs used the same number of shots.
* XOR / `U3`-prefix variants have no secret key and no de-obfuscation step.

**Not audited line by line:** `combined/cloaq_integrated_prototype.ipynb`,
`combined/qll_plus_phase_small_test.ipynb` and the per-circuit phase/XOR notebooks. They share
lineage (and function names such as `decrypt_qll`) with the notebooks above, so treat their
results with the same caution until re-run against the package.
