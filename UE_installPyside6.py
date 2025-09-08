# InstallPyside6.py by AurifexChandra

# This script installs PySide6 into the Unreal Engine's embedded Python environment by getting engine's python directory and executes installation command through cmd terminal.
# The directory looks like this, so one can perform manual tasks if needed:
# C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\ThirdParty\Python3\Win64

import os
import sys
import glob
import subprocess
from pathlib import Path
from typing import Optional, List
import unreal

def _guess_embedded_python_exe_from_editor(editor_exe: Path) -> Optional[Path]:
    """
    Given .../Engine/Binaries/Win64/UnrealEditor.exe (or platform equivalent),
    return .../Engine/Binaries/ThirdParty/Python3/<plat>/python(.exe)
    """
    # Engine root: .../Engine
    try:
        engine_dir = editor_exe.parents[2]  # Win64 -> Binaries -> Engine
        thirdparty = engine_dir / "Binaries" / "ThirdParty"
        # Platform mapping
        if sys.platform.startswith("win"):
            candidates = [
                thirdparty / "Python3" / "Win64" / "python.exe",
                thirdparty / "Python3" / "Win64" / "python3.exe",
            ]
        elif sys.platform == "darwin":
            candidates = [
                thirdparty / "Python3" / "Mac" / "bin" / "python3",
            ]
        else:  # Linux
            candidates = [
                thirdparty / "Python3" / "Linux" / "bin" / "python3",
            ]

        for c in candidates:
            if c.exists():
                return c

        # Fallback: glob any python* under ThirdParty/Python*
        hits = glob.glob(str(thirdparty / "Python*" / "**" / "python*"), recursive=True)
        for h in hits:
            p = Path(h)
            if p.is_file() and os.access(p, os.X_OK):
                return p
    except Exception:
        pass
    return None


def get_unreal_editor_exe() -> Path:
    """
    In some UE versions Python reports UnrealEditor.exe as sys.executable.
    If that’s the case, use it. Otherwise, resolve from process argv[0].
    """
    exe = Path(sys.executable)
    if exe.name.lower().startswith("unrealeditor"):
        return exe
    # Fallback to argv[0]
    return Path(sys.argv[0]).resolve()


def get_embedded_python_exe() -> Optional[Path]:
    """
    Returns the engine-embedded Python interpreter path even if sys.executable is UnrealEditor.exe.
    """
    editor_exe = get_unreal_editor_exe()
    py = _guess_embedded_python_exe_from_editor(editor_exe)
    if py and py.exists():
        return py
    unreal.log_warning("Could not resolve embedded Python automatically.")
    return None


def pip_install_into_engine_sitepackages(package: str = "PySide2", extra_args: Optional[List[str]] = None) -> bool:
    """
    Installs into the Engine's embedded Python site-packages (requires write permission to Engine install).
    """
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return False

    cmd = [str(py), "-m", "pip", "install", "--no-warn-script-location", "PySide6"]
    if extra_args:
        cmd.extend(extra_args)
    unreal.log(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        unreal.log("Installed into Engine Python site-packages.")
        return True
    except subprocess.CalledProcessError as e:
        unreal.log_error(f"pip failed: {e}")
        return False

def ensure_pyside2():
    """
    Ensures PySide6 is available in the engine's embedded Python environment.
    """
    import importlib.util
    if importlib.util.find_spec("PySide6"):
        unreal.log("✅ PySide6 already available.")
        return True

    unreal.log_warning("PySide6 not found. Attempting installation...")
    return pip_install_into_engine_sitepackages("PySide6")

# --- Optional utilities to assist users ---


def open_python_folder_in_explorer():
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return
    folder = py.parent
    unreal.log(f"Python folder: {folder}")
    unreal.log(f"Opening: {folder}")
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", str(folder)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def open_cmd_at_python():
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return
    folder = py.parent
    unreal.log(f"Python folder: {folder}")
    unreal.log(f"Opening CMD at: {folder}")
    if sys.platform.startswith("win"):
        subprocess.Popen("cmd.exe", cwd=str(folder))
    else:
        unreal.log_warning("CMD helper is Windows-only.")

ensure_pyside2()