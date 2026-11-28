# Windows portable package

ImpossibleEngine uses GTK3 through PyGObject. The supported packaging path in
this repository is an MSYS2 MINGW64 runtime bundle, not pip/PyInstaller.
The target machine does not need MSYS2 installed.

## Build prerequisites

1. Install MSYS2 from https://www.msys2.org/.
2. Open the **MSYS2 MinGW 64-bit** shell.
3. Update packages, then install:

```sh
pacman -Syu
pacman -S --needed mingw-w64-x86_64-gtk3 \
  mingw-w64-x86_64-python \
  mingw-w64-x86_64-python-gobject \
  mingw-w64-x86_64-adwaita-icon-theme \
  mingw-w64-x86_64-gettext
```

## Build the portable ZIP

From the repository root in the MINGW64 shell:

```sh
python pack/windows/build_portable.py
```

Output:

`dist/ImpossibleEngine-<version>-windows-x86_64-portable.zip`

Extract the ZIP anywhere and launch `ImpossibleEngine.bat`. The package
bundles the active MINGW64 `bin`, `lib` and `share` runtime directories,
Python, GTK3, PyGObject, typelibs, icon/theme data and the ImpossibleEngine
Python package. The launcher configures DLL search, Python, GI typelib, GTK,
GIO, GdkPixbuf and fontconfig paths relative to the extracted directory.

## GitHub Actions

- `.github/workflows/windows-package.yml` builds the portable ZIP on pushes,
  pull requests and manual dispatch, uploads CI artifacts, and attaches the ZIP
  to a GitHub Release when a `v*` tag is pushed. It can also be run manually to
  validate packaging without publishing a release.

To publish: push a version tag such as `v0.2.0`. The release workflow uses
`contents: write` and creates the GitHub Release after the package build.

## Scope and verification

This is a self-contained GUI package. It does not claim to bundle or enable
the native Rust runtime, game renderer, or RustMultiConsoleFoundation host.
Those components need their own Windows target build and DLL/resource staging
when the native host integration is ready.

CI validates Python bytecode compilation and package creation. A real Windows
GUI smoke test still requires a display session and should be added when the
Windows runner can exercise the application interactively.
