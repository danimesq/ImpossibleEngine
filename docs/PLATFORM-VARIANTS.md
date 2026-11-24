# Platform-specific asset and object variants

Platform variants are a first-class authoring feature, not a late export option.

## Logical identity, multiple realizations

An asset keeps one stable logical ID and may provide a different physical source
for each platform profile. For example, one logical Hero 3D mesh can resolve to
a high-detail GLB for a modern PC, a compact PS1 model, and a separately
prepared Nintendo 64 model. A 2D character can resolve to a modern mobile sprite
sheet, a GBA-oriented sheet, or a GBC-oriented sheet.

Objects follow the same pattern for properties. Base properties are merged
with sparse target-specific overrides. The same logical object can therefore
use different collision shapes, scales, rendering flags, animation settings,
palette choices or other backend-supported properties.

## Initial target profiles

| Profile | Intended use | Example variant strategy |
|---|---|---|
| Modern PC | Modern 2D and 3D | High-detail meshes, large textures, advanced materials |
| PlayStation 1 | Retro 2D and 3D | Low-poly meshes, compact textures, constrained effects |
| Nintendo 64 | Retro 2D and 3D | N64-specific model, texture and rendering preparation |
| Modern mobile | Mobile 2D and 3D | Scalable assets, touch-aware object settings |
| Game Boy Advance | 2D handheld | Tile/sprite-sheet and palette-aware source |
| Game Boy Color | 2D handheld | Compact sprite sheets and limited palettes |

These profiles are authoring presets, not claims that a runtime or SDK already
supports each target. Actual hardware budgets, formats, compression, texture
constraints, rendering rules and SDK requirements must be verified against
the selected toolchain and backend.

## Resolution and fallback

The intended resolver order is:

1. Exact platform variant, such as ps1.
2. Generic/base variant, when provided.
3. The asset's default source.

A missing explicit override is therefore visible and predictable, rather than
requiring duplicated logical objects throughout a project.

## Why this exists from day one

The Impossible Engine's endgame includes moving existing games through the
editor without losing established behavior, followed by more demanding
cross-platform projects. Platform-specific asset preparation must be possible
without forking the game's logical object model or event logic.

Project JSON stores IDs and source paths. Runtime-specific import, conversion,
validation and packaging remain responsibilities of platform adapters and
build backends.
