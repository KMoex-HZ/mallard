"""
Run with: python setup_exe.py

PyInstaller hooks already handle Streamlit & Altair automatically.
Only hidden imports are specified here; no manual add-data needed.
"""

import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent

# ── Check PyInstaller ────────────────────────────────────────────────────────
try:
    import PyInstaller
    print(f"[✓] PyInstaller {PyInstaller.__version__} found.")
except ImportError:
    print("[!] PyInstaller not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

# ── Check pyinstaller-hooks-contrib (required for Streamlit hook) ────────────
try:
    import _pyinstaller_hooks_contrib
    print(f"[✓] pyinstaller-hooks-contrib found.")
except ImportError:
    print("[!] Installing pyinstaller-hooks-contrib...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller-hooks-contrib"])

# ── Icon ─────────────────────────────────────────────────────────────────────
icon_path = BASE / "mallard_icon.ico"
icon_arg  = ["--icon", str(icon_path)] if icon_path.exists() else []

# ── Build PyInstaller arguments ──────────────────────────────────────────────
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",       
    "--windowed",     
    "--name", "MALLARD",
    *icon_arg,

    # --- Fallback fix (ensures Streamlit metadata is included) ---
    "--copy-metadata", "streamlit",
    # ----------------------------

    "--add-data", f"mallard.py{os.pathsep}.",
    "--add-data", f"{os.path.dirname(__import__('streamlit').__file__)}{os.pathsep}streamlit",

    # ── Hidden imports ────────────────────────────────────────────────────
    "--hidden-import", "streamlit",
    "--hidden-import", "streamlit.web.cli",
    "--hidden-import", "streamlit.runtime.scriptrunner.magic_funcs",
    "--hidden-import", "duckdb",
    "--hidden-import", "pandas",
    "--hidden-import", "plotly",
    "--hidden-import", "plotly.express",
    "--hidden-import", "openpyxl",
    "--hidden-import", "pyarrow",
    "--hidden-import", "xlrd",
    "--hidden-import", "tornado",
    "--hidden-import", "click",

    # ── Entry point ────────────────────────────────────────────────────────
    "launcher.py",
]

print()
print("=" * 60)
print("🦆 MALLARD — Build Executable")
print("=" * 60)
print(f"  Entry point : launcher.py")
print(f"  Icon        : {'mallard_icon.ico ✅' if icon_path.exists() else 'not found ⚠️'}")
print(f"  Mode        : --onedir")
print("=" * 60)
print()

result = subprocess.run(cmd, cwd=str(BASE))

if result.returncode == 0:
    dist_dir = BASE / "dist" / "MALLARD"
    print()
    print("=" * 60)
    print("✅ BUILD SUCCESSFUL!")
    print(f"📁 Output : {dist_dir}")
    print()
    print("Distribution:")
    print("  1. Zip the entire dist/MALLARD/ folder")
    print("  2. Extract on another machine, run MALLARD.exe")
    print("  3. Browser opens automatically at http://localhost:8501")
    print("=" * 60)
else:
    print()
    print("❌ BUILD FAILED. Try running this command first:")
    print("   pip install --upgrade pyinstaller pyinstaller-hooks-contrib")
    print("   then run again: python setup_exe.py")
    sys.exit(1)