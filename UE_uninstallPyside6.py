# UninstallPyside6.py by AurifexChandra

# This script uninstalls PySide6 from the Unreal Engine's embedded Python environment by getting engine's python directory and executes uninstall command through cmd terminal.
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
    If that's the case, use it. Otherwise, resolve from process argv[0].
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


def pip_uninstall_from_engine_sitepackages(package: str = "PySide6", extra_args: Optional[List[str]] = None) -> bool:
    """
    Uninstalls from the Engine's embedded Python site-packages (requires write permission to Engine install).
    """
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return False

    cmd = [str(py), "-m", "pip", "uninstall", "--yes", package]
    if extra_args:
        cmd.extend(extra_args)
    unreal.log(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        unreal.log(f"Successfully uninstalled {package} from Engine Python site-packages.")
        return True
    except subprocess.CalledProcessError as e:
        unreal.log_error(f"pip uninstall failed: {e}")
        return False


def check_pyside6_installed() -> bool:
    """
    Checks if PySide6 is currently installed in the engine's embedded Python environment.
    """
    import importlib.util
    if importlib.util.find_spec("PySide6"):
        return True
    return False


def get_pyside6_installation_info() -> Optional[str]:
    """
    Gets information about the currently installed PySide6 package.
    """
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return None

    cmd = [str(py), "-m", "pip", "show", "PySide6"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def uninstall_pyside6():
    """
    Uninstalls PySide6 from the engine's embedded Python environment.
    """
    if not check_pyside6_installed():
        unreal.log("❌ PySide6 is not installed in the engine's Python environment.")
        return False

    # Show installation info before uninstalling
    info = get_pyside6_installation_info()
    if info:
        unreal.log("📋 Current PySide6 installation info:")
        unreal.log(info)

    unreal.log_warning("🗑️ Attempting to uninstall PySide6...")
    success = pip_uninstall_from_engine_sitepackages("PySide6")
    
    if success:
        # Verify uninstall
        if not check_pyside6_installed():
            unreal.log("✅ PySide6 successfully uninstalled and verified.")
            return True
        else:
            unreal.log_warning("⚠️ Uninstall command completed but PySide6 still appears to be available.")
            return False
    else:
        unreal.log_error("❌ Failed to uninstall PySide6.")
        return False


def cleanup_pyside6_cache():
    """
    Attempts to clean up any remaining PySide6 cache files and directories.
    """
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return False

    # Get site-packages directory
    cmd = [str(py), "-c", "import site; print(site.getsitepackages()[0])"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        site_packages = Path(result.stdout.strip())
        
        # Look for PySide6 related directories and files
        pyside_paths = []
        patterns = ["PySide6*", "shiboken6*", "*pyside6*"]
        
        for pattern in patterns:
            pyside_paths.extend(site_packages.glob(pattern))
        
        if pyside_paths:
            unreal.log("🧹 Found potential PySide6 remnants:")
            for path in pyside_paths:
                unreal.log(f"  - {path}")
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                        unreal.log(f"  ✅ Removed directory: {path}")
                    else:
                        path.unlink()
                        unreal.log(f"  ✅ Removed file: {path}")
                except Exception as e:
                    unreal.log_warning(f"  ⚠️ Could not remove {path}: {e}")
            return True
        else:
            unreal.log("✅ No PySide6 remnants found.")
            return True
            
    except subprocess.CalledProcessError as e:
        unreal.log_error(f"Failed to get site-packages directory: {e}")
        return False


# --- Optional utilities to assist users ---

def open_python_folder_in_explorer():
    """
    Opens the engine's Python folder in the system file explorer.
    """
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
    """
    Opens a command prompt at the engine's Python directory (Windows only).
    """
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


def list_installed_packages():
    """
    Lists all packages installed in the engine's embedded Python environment.
    """
    py = get_embedded_python_exe()
    if not py:
        unreal.log_error("No embedded Python found.")
        return

    cmd = [str(py), "-m", "pip", "list"]
    unreal.log("📦 Packages installed in engine Python:")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        unreal.log(result.stdout)
    except subprocess.CalledProcessError as e:
        unreal.log_error(f"Failed to list packages: {e}")


# Main execution
if __name__ == "__main__":
    unreal.log("🚀 PySide6 Uninstaller for Unreal Engine")
    unreal.log("=" * 50)
    
    # Check current status
    if check_pyside6_installed():
        unreal.log("📋 PySide6 is currently installed.")
        
        # Perform uninstall
        if uninstall_pyside6():
            # Clean up any remaining files
            cleanup_pyside6_cache()
            unreal.log("🎉 PySide6 uninstallation completed successfully!")
        else:
            unreal.log("❌ PySide6 uninstallation failed.")
    else:
        unreal.log("ℹ️ PySide6 is not currently installed in the engine's Python environment.")
    
    unreal.log("=" * 50)

# Execute the uninstall process
uninstall_pyside6()
