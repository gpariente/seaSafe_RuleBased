import sys
import os

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for both development and PyInstaller.

    When running as a bundled executable, sys._MEIPASS contains the path to the temporary folder.
    Otherwise, this returns the path relative to this file's directory.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        # Use the directory where resource_path.py is located (assumed to be the project root)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_path, relative_path))
