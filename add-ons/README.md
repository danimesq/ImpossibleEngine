# 🌈 Third-party add-on packages

Place each third-party package in its own vendor/package directory:

```text
add-ons/
└── example-vendor/
    └── example-addon/
        ├── addon.json
        ├── README.md
        └── runtime.js
```

The `addon.json` manifest contains:

- `format`: `impossible.addon-package`
- `manifestVersion`: `1`
- `addon`: the same typed add-on descriptor shape used by the built-in registry
- `package.entrypoints`: relative paths to package files
- `package.permissions`: declared permission identifiers

Use `schemas/addon-package-v1.schema.json` as the manifest envelope reference.
The embedded add-on descriptor must also satisfy the built-in registry rules.

The registry reads package metadata only. It never evaluates JavaScript,
loads WASM, imports native libraries or invokes entrypoints. Every declared
entrypoint must resolve to a regular file inside its package directory.
Absolute paths, traversal paths and symlinks that escape the package directory
are rejected.

Inspect discovered packages with:

```sh
impossible addons list --third-party-dir ./add-ons --format json
impossible addons show plugin.example-addon --third-party-dir ./add-ons
```

Selecting a third-party descriptor in a project records `bundled: false`
metadata in `usedAddons`. Runtime installation and execution are separate
capabilities and are not implied by discovery or selection.
