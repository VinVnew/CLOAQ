# Contributing

```bash
git clone https://github.com/VinVnew/CLOAQ && cd CLOAQ
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check .          # lint
pytest --cov=cloaq    # tests
```

* Every change that touches obfuscation must keep the invariant **correct key => exact unitary
  equivalence** (`functionally_equivalent`) and, for the compiler tests, **any single wrong key
  bit => not equivalent**.
* Add tests next to the code you change (`tests/`), keep `ruff check .` clean and update
  `CHANGELOG.md`.
* Keys must never be stored inside the obfuscated circuit or its metadata.
