"""CLOAQ: combined logic and angle obfuscation for quantum circuits."""

from importlib.metadata import PackageNotFoundError, version

from .logic import logic_deobfuscate, logic_obfuscate
from .metrics import functionally_equivalent, simulate, tvd
from .phase import key_phase, phase_deobfuscate, phase_obfuscate
from .pipeline import ObfuscationResult, deobfuscate, obfuscate, wrong_key

try:
    __version__ = version("cloaq")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "ObfuscationResult",
    "deobfuscate",
    "functionally_equivalent",
    "key_phase",
    "logic_deobfuscate",
    "logic_obfuscate",
    "obfuscate",
    "phase_deobfuscate",
    "phase_obfuscate",
    "simulate",
    "tvd",
    "wrong_key",
]
