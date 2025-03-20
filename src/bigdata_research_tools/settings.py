import importlib.util
import os
from pathlib import Path
from typing import List


def check_libraries_installed(libraries: List[str]) -> bool:
    """
    Check if the received Python libraries are installed.
    """
    return all(importlib.util.find_spec(lib) is not None for lib in libraries)


def get_library_root() -> str:
    spec = importlib.util.find_spec("bigdata_research_tools")
    if spec and spec.origin:
        return os.path.dirname(os.path.abspath(spec.origin))
    return os.path.dirname(os.path.abspath(__file__))


def get_resources_path() -> str:
    return str(Path(get_library_root()).resolve() / "res")
