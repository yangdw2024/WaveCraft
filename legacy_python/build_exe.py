import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist_v3")

from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "gui"

include_files = [
    ("D:/Multiwfn/Multiwfn_3.8_bin_Win64/Multiwfn.exe", "Multiwfn_3.8_bin_Win64/Multiwfn.exe"),
    ("config", "config"),
    ("source", "source"),
]

packages = [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "matplotlib",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.figure",
    "numpy",
    "source",
    "source.core",
    "source.tabs",
    "source.utils",
    "source.dialogs",
    "openpyxl",
    "psutil",
]

includes = [
    "source.core.logger",
    "source.core.worker",
    "source.core.multiwfn_service",
    "source.core.config_manager",
    "source.core.system_manager",
    "source.core.health_checker",
    "source.core.error_handler",
    "source.core.calculation_worker",
    "source.core.resource_monitor",
    "source.core.workflow_engine",
    "source.core.event_bus",
    "source.tabs.realspace_analyzer",
    "source.tabs.charge_analysis",
    "source.tabs.bond_analysis",
    "source.tabs.dos_spectrum",
    "source.tabs.weak_interaction",
    "source.tabs.file_manager",
    "source.tabs.structure_viewer",
    "source.tabs.spectrum_analyzer",
    "source.tabs.advanced_tools",
    "source.tabs.orbital_bond",
    "source.tabs.function_menu",
    "source.utils.input_generator",
    "source.utils.output_parser",
    "source.utils.export_manager",
    "source.utils.export_utils",
    "source.utils.cube_parser",
    "source.utils.menu_data",
    "source.dialogs.export_dialog",
    "source.dialogs.result_preview",
    "source.dialogs.settings_dialog",
]

excludes = [
    "tkinter",
    "unittest",
    "test",
    "distutils",
    "setuptools",
    "PyQt6",
    "PyQt5.QtQml",
    "PyQt5.QtQuick",
    "PyQt5.QtQuick3D",
    "PyQt5.QtBluetooth",
    "PyQt5.QtNfc",
    "PyQt5.QtSensors",
    "PyQt5.QtLocation",
    "PyQt5.QtWebEngine",
    "PyQt5.QtHelp",
    "PyQt5.QtSql",
    "PyQt5.QtDBus",
    "PyQt5.QtDesigner",
    "PyQt5.uic",
    "scipy",
    "pandas",
    "lxml",
    "cairo",
    "pytest",
    "_pytest",
    "pluggy",
    "pygments",
    "sqlalchemy",
    "greenlet",
    "brotlicffi",
    "pycparser",
    "cffi",
]

build_exe_options = {
    "build_exe": build_dir,
    "packages": packages,
    "includes": includes,
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 0,
    "silent": False,
    "include_msvcr": True,
    "zip_include_packages": [],
    "zip_exclude_packages": ["source"],
}

executables = [
    Executable(
        "wavecraft.py",
        base=base,
        target_name="WaveCraft.exe",
        icon=None,
    )
]

setup(
    name="WaveCraft",
    version="1.0.0",
    description="Multiwfn Visualization Suite",
    options={"build_exe": build_exe_options},
    executables=executables,
    script_args=["build", "--force"],
)

print("打包完成!")
