# Browser/WebAssembly host notes

The gameplay model and renderer are written in Rust with Macroquad. The native desktop target is the first build gate. The browser target is a separate packaging gate.

## Persistent high-score storage

The project uses quad-storage to preserve the original Construct WebStorage behavior:

- Native builds save the Highscore key in local.data.
- WebAssembly builds use the browser Web Storage API.

The quad-storage WebAssembly host requires two JavaScript support files from their upstream projects:

- quad-storage.js from https://github.com/optozorax/quad-storage/tree/master/js
- sapp-jsutils.js from https://github.com/not-fl3/sapp-jsutils/tree/master/js

Load both scripts after the miniquad/Macroquad gl.js runner and before instantiating the game WebAssembly module, as documented by quad-storage:

https://docs.rs/quad-storage/0.1.3/quad_storage/

Do not replace these shims with a wasm-bindgen import: Macroquad/miniquad uses its own browser loader.

## WebAssembly build

Install the wasm32-unknown-unknown target, then build:

    rustup target add wasm32-unknown-unknown
    cargo build --release --target wasm32-unknown-unknown

Use the miniquad WebAssembly runner/HTML template for the selected Macroquad version. The exact runner files and script order must be pinned in the eventual web release package.

The current PR does not claim that the browser bundle has been assembled or tested. Native Rust tests/build and WebAssembly packaging are independent acceptance gates.
