# Changelog

## 0.1.0 - unreleased
- Archive of the original research notebooks in `research/legacy-notebooks/` (outputs cleared,
  documented, known issues listed).
- Initial packaged release: logic obfuscation (ancilla `qk`, X->CX / CX->CCX, dummy CX),
  phase obfuscation (3-bit angle keys, decoy angles, dummy P gates), combined pipeline,
  standard TVD metric, exact-equivalence check, CLI, tests and CI.
- Fixes over the original research notebook: real controlled-gate conversion, identity dummies,
  phase lock/unlock acting on the same gates, compile-proof key ordering, standard TVD against
  the untouched benchmark.
