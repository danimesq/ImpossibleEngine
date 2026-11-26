# Native Rust game source

- game.rs — hand-authored gameplay/state-machine port of the original legacy visual-editor event sheets.
- geometry.rs — source collision polygons, hotspot transforms and convex SAT collision.
- renderer.rs — temporary 400×500 vector renderer used while original media is pending.
- services.rs — audio, persistent Highscore storage, font loading and external-service policies.
- main.rs — Macroquad native/web host loop, input normalization and effect dispatch.

The game crate itself is independent of GTK and the Impossible editor prototype. No generic the source editor importer is implemented in this migration round.
