# Windows packaging and releases

## Supported bundle

ImpossibleEngine can be distributed on Windows without asking end users to
install MSYS2. The repository builds a portable ZIP that includes a by-directory copy of the MSYS2 MINGW64 runtime (`bin`, `lib`, `share`), the
Python authoring package, GTK3, PyGObject and its runtime data.

The bundle is intentionally independent of pip and PyInstaller: the MSYS2
Python environment is supplied by pacman, and the package carries that
runtime alongside the application.

## Reproduce locally

Follow [pack/windows/README.md](../pack/windows/README.md), then run:

```sh
python pack/windows/build_portable.py
```

The result is written to `dist/ImpossibleEngine-<version>-windows-x86_64-portable.zip`.
Extract it and run `ImpossibleEngine.bat`.

## Continuous integration

`windows-package.yml` builds the portable ZIP on pull requests, pushes to
`main` and manual dispatch. The artifact is retained by GitHub Actions for
download and inspection.

## GitHub Releases

`windows-package.yml` also handles tags matching `v*`. It builds the ZIP and
attaches it to a GitHub Release using the repository `GITHUB_TOKEN` with
`contents: write`. To publish a release, push a version tag, for example:

```sh
git tag v0.2.0
git push origin v0.2.0
```

The workflow can also be manually dispatched to validate the build without
publishing a release.

## Current boundary

This package distributes the GTK/Python authoring GUI. It does not yet bundle
the native Rust runtime, renderer, or RustMultiConsoleFoundation host. Those
will need a separate Windows target build, DLL staging, resource packaging
and smoke tests once the host integration exists.

## Third-party ribbon attribution

The ribbon widget implementation is adapted from RibbonFM by the RibbonFM
contributors under Apache-2.0. See
[NOTICE-RibbonFM.txt](../THIRD_PARTY_NOTICES/NOTICE-RibbonFM.txt) and the
complete [license](../THIRD_PARTY_NOTICES/RibbonFM-LICENSE).
