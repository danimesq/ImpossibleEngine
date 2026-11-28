#!/usr/bin/env python3
"""Build a self-contained GTK3 + PyGObject Windows portable ZIP with MSYS2."""
from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "impossible"


def mingw_prefix() -> Path:
    configured = os.environ.get("MINGW_PREFIX")
    candidates = [Path(configured)] if configured else []
    candidates += [Path("/mingw64"), Path("C:/msys64/mingw64")]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "bin" / "python.exe").exists():
            return candidate
    raise SystemExit("MINGW64 prefix not found; run in an MSYS2 MINGW64 shell")


def version() -> str:
    tag = os.environ.get("GITHUB_REF_NAME", "")
    return tag[1:] if tag.startswith("v") else "0.1.0-dev"


def main() -> int:
    prefix = mingw_prefix()
    stage = ROOT / "build" / "windows-portable"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "app").mkdir(parents=True)
    shutil.copytree(APP, stage / "app" / "impossible")
    for folder in ("bin", "lib", "share"):
        source = prefix / folder
        if not source.is_dir():
            raise SystemExit(f"Required MSYS2 runtime directory missing: {source}")
        print(f"Bundling {folder}/ from {prefix}")
        shutil.copytree(source, stage / "runtime" / folder, dirs_exist_ok=True)

    (stage / "README-Windows.txt").write_text(
        "ImpossibleEngine Windows portable build\n"
        "========================================\n\n"
        "Extract this folder and run ImpossibleEngine.bat.\n"
        "This package bundles GTK3, PyGObject and the MSYS2 MINGW64 runtime.\n"
        "The current package contains the Python authoring GUI; native Rust\n"
        "runtime/renderer integration is a separate build capability.\n",
        encoding="utf-8",
    )
    notices = ROOT / "THIRD_PARTY_NOTICES"
    if notices.exists():
        shutil.copytree(notices, stage / "THIRD_PARTY_NOTICES")

    launcher = r"""@echo off
setlocal
set "H=%~dp0"
set "PATH=%H%runtime\bin;%PATH%"
set "PYTHONPATH=%H%app"
set "GI_TYPELIB_PATH=%H%runtime\lib\girepository-1.0"
set "GTK_EXE_PREFIX=%H%runtime"
set "GTK_DATA_PREFIX=%H%runtime"
set "XDG_DATA_DIRS=%H%runtime\share"
set "GDK_PIXBUF_MODULE_FILE=%H%runtime\lib\gdk-pixbuf-2.0\2.10.0\loaders.cache"
set "GIO_MODULE_DIR=%H%runtime\lib\gio\modules"
set "FONTCONFIG_PATH=%H%runtime\etc\fonts"
set "FONTCONFIG_FILE=%H%runtime\etc\fonts\fonts.conf"
"%H%runtime\bin\python.exe" -m impossible %*
endlocal
"""
    (stage / "ImpossibleEngine.bat").write_text(launcher, encoding="utf-8")

    python = stage / "runtime" / "bin" / "python.exe"
    if not python.is_file():
        raise SystemExit("Bundled python.exe missing")
    env = os.environ.copy()
    env["PATH"] = str(stage / "runtime" / "bin") + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(stage / "app")
    env["GI_TYPELIB_PATH"] = str(stage / "runtime" / "lib" / "girepository-1.0")
    env["GTK_EXE_PREFIX"] = str(stage / "runtime")
    env["GTK_DATA_PREFIX"] = str(stage / "runtime")
    env["XDG_DATA_DIRS"] = str(stage / "runtime" / "share")
    # Import GTK from the staged runtime before creating the distributable ZIP.
    subprocess.run(
        [str(python), "-c",
         "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print(Gtk.get_major_version(), Gtk.get_minor_version())"],
        check=True,
        env=env,
    )
    subprocess.run(
        [str(python), "-m", "compileall", "-q", str(stage / "app" / "impossible")],
        check=True,
        env=env,
    )

    output = ROOT / "dist" / f"ImpossibleEngine-{version()}-windows-x86_64-portable.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(stage))
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
