import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "init_engine", Path(__file__).resolve().parent.parent / "scripts" / "init.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules.update({"init_engine": _mod, "init": _mod})
_spec.loader.exec_module(_mod)
