#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# Set GDAL library path for GeoDjango on Windows (must be set before Django loads)
_gdal_dll = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages" / "osgeo" / "gdal.dll"
if _gdal_dll.exists():
    # Add osgeo directory to PATH so DLL dependencies can be found
    os.environ["PATH"] = str(_gdal_dll.parent) + os.pathsep + os.environ.get("PATH", "")

    # Configure Django settings early so GDAL_LIBRARY_PATH can be read
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    # Patch Django's GDAL_LIBRARY_PATH setting before it's imported
    import django.conf
    django.conf.settings.GDAL_LIBRARY_PATH = str(_gdal_dll)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
