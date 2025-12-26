from os import walk
from pathlib import Path
from types import ModuleType
from typing import Dict, List
import importlib


MODULE_NAMES: List[str] = []
_src = Path(__file__).parent / "src"
for _, _, filenames in walk(_src):
    for filename in filenames:
        if filename.startswith("jv_") and filename.endswith(".py"):
            MODULE_NAMES.append(Path(filename).stem)


_should_reload = "bpy" in locals()
MODULES: Dict[str, ModuleType] = {}

import bpy

def register():
    global MODULES

    if _should_reload:
        for name, mod in list(MODULES.items()):
            MODULES[name] = importlib.reload(mod)
    else:
        for name in MODULE_NAMES:
            MODULES[name] = importlib.import_module(
                f".src.{name}",
                package=__package__
            )

    for mod in MODULES.values():
        if (reg := getattr(mod, "register", None)) is not None:
            reg()


def unregister():
    global MODULES

    for module in MODULES.values():
        if (unreg := getattr(module, "unregister", None)) is not None:
            unreg()
