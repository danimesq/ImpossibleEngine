#!/usr/bin/env bash
# Build and assemble the Flappy Madruga WebAssembly package.
# Third-party JavaScript loader/shims must be supplied locally and are never
# silently downloaded or vendored by this script.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TARGET="wasm32-unknown-unknown"
BUILD_DIR="$PROJECT_DIR/target/$TARGET/release"
OUTPUT_DIR="$SCRIPT_DIR/dist"

log() {
    printf '[flappy-web] %s\n' "$*"
}

die() {
    printf '[flappy-web] ERROR: %s\n' "$*" >&2
    exit 1
}

trap 'status=$?; if [[ $status -ne 0 ]]; then printf "[flappy-web] FAILED (exit %s)\n" "$status" >&2; fi' EXIT

for command in cargo rustup; do
    command -v "$command" >/dev/null 2>&1 || die "Required command not found: $command"
done

for vendor_file in mq_js_bundle.js sapp_jsutils.js quad-storage.js; do
    [[ -s "$SCRIPT_DIR/$vendor_file" ]] || die \
        "Missing $vendor_file. Follow web/README.md to obtain the matching upstream file."
done

if ! rustup target list --installed | grep -qx "$TARGET"; then
    log "Installing Rust target $TARGET"
    rustup target add "$TARGET"
fi

log "Compiling Flappy Madruga for $TARGET"
cd -- "$PROJECT_DIR"
cargo build --release --features graphics --target "$TARGET"

WASM_FILE="$(find "$BUILD_DIR" -maxdepth 1 -type f -name '*.wasm' -print -quit)"
[[ -s "$WASM_FILE" ]] || die "No WebAssembly binary found in $BUILD_DIR"

log "Preparing output directory $OUTPUT_DIR"
rm -rf -- "$OUTPUT_DIR"
mkdir -p -- "$OUTPUT_DIR"

cp -- "$SCRIPT_DIR/index.html" "$OUTPUT_DIR/index.html"
cp -- "$WASM_FILE" "$OUTPUT_DIR/flappy-madruga.wasm"
cp -- "$SCRIPT_DIR/mq_js_bundle.js" "$OUTPUT_DIR/mq_js_bundle.js"
cp -- "$SCRIPT_DIR/sapp_jsutils.js" "$OUTPUT_DIR/sapp_jsutils.js"
cp -- "$SCRIPT_DIR/quad-storage.js" "$OUTPUT_DIR/quad-storage.js"

# Copy the project-relative asset tree. README placeholders are harmless;
# missing source media remains visibly pending and is logged by the game.
cp -a -- "$PROJECT_DIR/assets" "$OUTPUT_DIR/assets"

log "Web package assembled at $OUTPUT_DIR"
log "Serve this directory over HTTP; browsers do not load WASM from file://."
