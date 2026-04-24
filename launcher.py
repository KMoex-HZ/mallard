"""
launcher.py — Entry point for MALLARD .exe
PyInstaller bundles this file as the entry point.
This script runs Streamlit internally (without opening a new CMD window).
"""

import sys
import os
import threading
import webbrowser
import time
from pathlib import Path
import psutil


def get_base_dir():
    """Get base directory: .exe folder when frozen, script folder during development."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def ensure_dirs(base: Path):
    """Create data/ folder and ensure mallard.duckdb can be created."""
    (base / "data").mkdir(exist_ok=True)


def open_browser():
    """Open browser after Streamlit is ready (3-second delay)."""
    time.sleep(3)
    webbrowser.open("http://localhost:8501")


def main():
    base = get_base_dir()
    ensure_dirs(base)

    # Change to base dir so mallard.duckdb & data/ stay relative to the .exe
    os.chdir(base)

    # Add base dir to sys.path so mallard.py can be imported
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    for proc in psutil.process_iter(['pid']):
        try:
            for conn in proc.net_connections():
                if conn.laddr.port == 8501:
                    proc.kill()
                    break
        except:
            continue

    # Open browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Streamlit
    from streamlit.web import cli as stcli

    app_path = base / "mallard.py"
    if not app_path.exists():
        app_path = base / "_internal" / "mallard.py"
    app_path = str(app_path)
    sys.argv = [
        "streamlit", "run", app_path,
        "--global.developmentMode=false",  # ← Critical flag to disable development mode
        "--server.port=8501",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
