# Browser WebAssembly backend

The preferred browser output direction is **Rust compiled directly to
WebAssembly**, not an Emscripten-centered pipeline.

## Initial technical path

Investigate this combination first:

- Rust target: `wasm32-unknown-unknown`
- Rust/JavaScript interop: `wasm-bindgen`
- Browser API bindings: `web-sys`
- Browser module loading: generated JavaScript glue, with a direct browser
  loading mode or a bundler chosen by the eventual web packaging workflow.
- 2D rendering: Canvas 2D for a simple/software-oriented renderer, or WebGL 2
  for a GPU-backed 2D renderer.
- 3D rendering: WebGL 2 as the initial compatibility-oriented candidate.
- WebGPU: optional future backend to investigate, not a baseline requirement.

The Rust WASM module executes game logic and engine code. The browser host owns
the canvas, browser event loop, web input, audio integration, resource fetching
and other browser APIs. The WASM module accesses those APIs through bindings;
WASM does not directly own or draw into a Canvas element.

## Renderer adapter

Avoid baking Canvas or WebGL types into the core game model. Define an
Impossible renderer boundary that can be implemented by:

1. Canvas 2D renderer.
2. WebGL 2 renderer.
3. Native renderer adapters for desktop and future console integrations.

A project may select a renderer per platform profile. A 2D game can use Canvas
2D or WebGL 2; a 3D browser game requires a 3D-capable backend such as WebGL 2.
The exact default should follow an initial performance and feature test rather
than being assumed now.

## Host services and sandbox boundary

The `wasm32-unknown-unknown` target is intentionally minimal. Do not assume
that desktop operating-system facilities are available inside the browser
module. The target documentation notes limitations including filesystem
operations and thread spawning.

Define host-service interfaces for capabilities such as:

- Asset loading and streaming.
- Persistent saves and user-selected files.
- Audio output.
- Keyboard, pointer, touch and gamepad input.
- Timing, frame scheduling and visibility changes.
- Logging and diagnostics.

The browser implementation should map these interfaces to browser APIs. Native
backends can map the same interfaces to their platform facilities.

## Build and packaging boundary

The eventual browser export is expected to contain:

- The compiled `.wasm` module.
- Generated JavaScript bindings/loader.
- HTML entry point and browser host code.
- Game assets and a manifest.
- Optional source maps and debug metadata for development builds.

This is a design target, not an implemented exporter yet. Build output should
be testable on a static web server and should not require Emscripten by default.

## First validation spike

Before choosing a rendering crate or engine adapter, build a tiny proof of
concept that:

1. Compiles a minimal Rust library for `wasm32-unknown-unknown`.
2. Exposes an initialization function through `wasm-bindgen`.
3. Acquires a Canvas 2D context through `web-sys`.
4. Draws a frame and responds to browser input.
5. Runs without Emscripten.
6. Separately tests a WebGL 2 context before committing to the 3D route.

Only after the proof works should the renderer and runtime adapter be selected.

## References

- Rust target documentation:
  https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html
- wasm-bindgen guide:
  https://wasm-bindgen.github.io/wasm-bindgen/
- web-sys browser API bindings:
  https://docs.rs/web-sys/latest/web_sys/
