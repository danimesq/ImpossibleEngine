# Browser/WebAssembly package

The gameplay core is compiled to WebAssembly with Macroquad. The repository includes a minimal HTML5 runner and a Bash packaging script. The WebAssembly binary and third-party JavaScript runtime files are build/vendor inputs, not committed assets.

## 1. Install the WebAssembly target

    rustup target add wasm32-unknown-unknown

## 2. Supply the browser runtime files

Place these files next to this README:

- mq_js_bundle.js: Macroquad/miniquad browser loader matching the pinned Macroquad 0.4.16 dependency.
- sapp_jsutils.js: upstream miniquad browser utility shim.
- quad-storage.js: upstream quad-storage browser storage shim.

The storage shims are required by quad-storage 0.1.3. Load them after the miniquad GL/browser loader and before the WASM module starts.

Upstream references:

- Macroquad 0.4.16 build and HTML5 loader: https://docs.rs/crate/macroquad/0.4.16/source/README.md
- quad-storage 0.1.3 and required JavaScript shims: https://docs.rs/quad-storage/0.1.3/quad_storage/
- quad-storage source: https://github.com/optozorax/quad-storage
- miniquad browser utilities: https://github.com/not-fl3/sapp-jsutils

Do not replace these files with arbitrary newer loader builds without testing them against the pinned Cargo dependencies.

## 3. Build the WASM package

From any working directory:

    bash projects/flappy-ramon/web/build-web.sh

The script verifies the vendor files, installs the Rust target if missing, compiles the game, copies the WASM, HTML runner, JavaScript runtime files and project-relative assets into web/dist/.

The script does not download third-party code. This keeps dependency provenance explicit.

## 4. Serve locally

For example:

    cd projects/flappy-ramon/web/dist
    python3 -m http.server 8000

Open http://localhost:8000/ in a browser. Use HTTP rather than opening the HTML file with file://.

## 5. What is and is not validated

The CI WebAssembly job checks that the Rust game compiles for wasm32-unknown-unknown. It does not yet prove that a browser package has been assembled or tested in a real browser.

The original game media remains pending. The current renderer is a vector fallback, and missing audio/font files are reported rather than silently replaced with invented media.
