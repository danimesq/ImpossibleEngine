# 🌈 Third-party add-ons

This directory is the user/vendor drop-in location for ImpossibleEngine add-on packages.

The built-in catalogue is stored separately in `../addons/builtin-v1.json`. Do not place vendor packages in that built-in directory.

## 🌈 Package layout

Place each package in its own directory. Vendor nesting is recommended to prevent name collisions:

```text
add-ons/
  vendor-name/
    addon-name/
      addon.json
      icon.svg
      editor.js
      runtime.js
      README.md
```

The package manifest uses `format: impossible.addon-package` and `manifestVersion: 1`. Its `addon` member must be a complete descriptor matching `../schemas/addon-registry-v1.schema.json`; optional package metadata can list editor/runtime entrypoint paths and requested permissions.

An asset icon can use `icon: { kind: asset, name: icon.svg }`. The referenced file must remain inside its package directory.

## 🌈 Current loader behavior

ImpossibleEngine recursively discovers `addon.json` manifests and registers their metadata in the add-on registry. It validates package format, descriptor shape, ID uniqueness, dependencies and relative file references. Malformed packages are skipped with a diagnostic; they do not prevent built-in add-ons from loading.

**Package code is not executed yet.** The editor/runtime entrypoints and permissions are metadata only. Do not expect a copied JavaScript, Python, native or WASM module to run. Executable third-party extensions require a separately versioned ABI, explicit capability grants and sandboxing. The loader does not import or evaluate package code.

Construct 2 `.c2addon` and Construct 3 `.c3addon` packages are not directly compatible with this format. They require a source-aware importer/port.

Only install packages from vendors you trust. When executable extensions are introduced, ImpossibleEngine must preserve this trust boundary and present requested capabilities to the user before granting them.
