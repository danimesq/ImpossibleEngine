"""Platform-neutral project model; deliberately independent from GTK."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlatformProfile:
    id: str
    name: str
    family: str
    dimension: str
    renderer: str
    description: str
    budget_hint: str


PLATFORM_PROFILES = (
    PlatformProfile("pc-modern", "Modern PC", "desktop", "2D + 3D", "Native / Vulkan / DX12",
                    "Contemporary desktop target.", "High-resolution assets, detailed meshes and broad material support."),
    PlatformProfile("ps1", "PlayStation 1", "console", "2D + 3D", "Console adapter",
                    "Retro 3D target with a constrained asset profile.", "Low-poly meshes, compact textures and careful effect budgets."),
    PlatformProfile("n64", "Nintendo 64", "console", "2D + 3D", "Console adapter",
                    "Retro 3D target with distinct rendering and asset constraints.", "N64-specific model, texture and rendering preparation."),
    PlatformProfile("mobile-modern", "Modern mobile", "mobile", "2D + 3D", "Native / Vulkan / GLES",
                    "Contemporary Android and iOS devices.", "Battery-aware rendering, scalable textures and touch-first input."),
    PlatformProfile("web-wasm", "WebAssembly / Browser", "web", "2D + 3D", "Canvas 2D / WebGL 2",
                    "Rust game logic running as WebAssembly inside a browser host.", "Browser sandbox, asynchronous assets, memory budgets and browser API boundaries."),
    PlatformProfile("gba", "Game Boy Advance", "handheld", "2D", "Console adapter",
                    "Classic handheld 2D target.", "Tile/sprite-sheet planning, palette-aware art and compact animation sets."),
    PlatformProfile("gbc", "Game Boy Color", "handheld", "2D", "Console adapter",
                    "Classic color handheld 2D target.", "Very compact sprite sheets and limited palettes."),
)
PROFILE_BY_ID = {profile.id: profile for profile in PLATFORM_PROFILES}


@dataclass
class Asset:
    id: str
    name: str
    kind: str
    source: str
    variants: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def source_for(self, platform_id: str) -> str:
        return self.variants.get(platform_id) or self.variants.get("base") or self.source


@dataclass
class GameObject:
    id: str
    name: str
    asset_id: str
    base_properties: dict[str, Any] = field(default_factory=dict)
    platform_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    def properties_for(self, platform_id: str) -> dict[str, Any]:
        return {**self.base_properties, **self.platform_overrides.get(platform_id, {})}


@dataclass
class Event:
    id: str
    name: str
    conditions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    enabled: bool = True
    # Stable source provenance and hierarchy survive editor round-trips.
    source_id: str | None = None
    parent_id: str | None = None
    group: str | None = None
    source_order: int = 0
    source_status: str | None = None


@dataclass
class EventSheet:
    id: str
    name: str
    events: list[Event] = field(default_factory=list)
    source_path: str | None = None
    includes: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)


@dataclass
class ObjectInstance:
    """Placed instance of a logical object type inside a project layout."""

    id: str
    object_id: str
    source_uid: int
    position: list[float] = field(default_factory=lambda: [0.0, 0.0])
    size: list[float] = field(default_factory=lambda: [0.0, 0.0])
    hotspot: list[float] | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    behaviors: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Layout:
    """Source-ordered scene with an explicit Event Sheet/include relationship."""

    id: str
    name: str
    event_sheet_id: str
    includes: list[str] = field(default_factory=list)
    instances: list[ObjectInstance] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    name: str
    schema_version: int = 1
    active_platform: str = "pc-modern"
    event_sheets: list[EventSheet] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    objects: list[GameObject] = field(default_factory=list)
    layouts: list[Layout] = field(default_factory=list)
    # The editor and CLI share this project-level add-on selection.
    used_addons: list[dict[str, Any]] = field(default_factory=list)
    # Import/build provenance is project data, not GUI widget state.
    metadata: dict[str, Any] = field(default_factory=dict)
    # Unknown top-level fields survive edits by older editor/CLI versions.
    extra_fields: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        # These are model internals, not serialized project-index keys.
        used_addons = result.pop("used_addons", [])
        extra_fields = result.pop("extra_fields", {})
        # Preserve future/foreign project metadata before writing current fields.
        result.update(extra_fields)
        # Keep the canonical project-index spelling documented by the format.
        result["usedAddons"] = used_addons
        return result

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Project":
        if not isinstance(raw, dict):
            raise ValueError("Project root must be a JSON object.")
        version = raw.get("schema_version", 1)
        if version != 1:
            raise ValueError(f"Unsupported project schema: {version}")
        def model_list(name: str) -> list[Any]:
            value = raw.get(name, [])
            return value if isinstance(value, list) else []

        sheets = []
        for item in model_list("event_sheets"):
            events = [Event(**event) for event in item.get("events", [])]
            sheets.append(EventSheet(
                id=str(item["id"]),
                name=str(item["name"]),
                events=events,
                source_path=item.get("source_path"),
                includes=list(item.get("includes", [])),
                groups=list(item.get("groups", [])),
            ))
        known_fields = {
            "name", "schema_version", "active_platform", "usedAddons", "used_addons",
        }
        # Canonical project indexes use object trees under keys such as "layouts".
        # Only claim fields that match the inline editor model; preserve all others.
        known_fields.update(
            key for key in ("event_sheets", "assets", "objects", "layouts")
            if key not in raw or isinstance(raw[key], list)
        )
        if "metadata" not in raw or isinstance(raw["metadata"], dict):
            known_fields.add("metadata")
        used_addons_raw = raw.get("usedAddons", raw.get("used_addons", []))
        if not isinstance(used_addons_raw, list):
            raise ValueError("usedAddons must be a JSON array.")
        project = cls(
            name=str(raw.get("name", "Untitled Project")),
            schema_version=1,
            active_platform=str(raw.get("active_platform", "pc-modern")),
            event_sheets=sheets,
            assets=[Asset(**item) for item in model_list("assets")],
            objects=[GameObject(**item) for item in model_list("objects")],
            layouts=[
                Layout(
                    id=str(item["id"]),
                    name=str(item["name"]),
                    event_sheet_id=str(item["event_sheet_id"]),
                    includes=list(item.get("includes", [])),
                    instances=[ObjectInstance(**instance) for instance in item.get("instances", [])],
                    properties=dict(item.get("properties", {})),
                )
                for item in model_list("layouts")
            ],
            used_addons=[dict(item) for item in used_addons_raw],
            metadata=dict(raw.get("metadata", {})) if isinstance(raw.get("metadata", {}), dict) else {},
            extra_fields={key: value for key, value in raw.items() if key not in known_fields},
        )
        if project.active_platform not in PROFILE_BY_ID:
            project.active_platform = "pc-modern"
        return project


def make_demo_project() -> Project:
    return Project(
        name="Impossible Sandbox",
        event_sheets=[EventSheet("sheet-gameplay", "Gameplay", [
            Event("event-start", "When scene starts", ["On scene start"],
                  ["Set Player.visible = true", "Set score = 0"]),
            Event("event-input", "Player movement", ["Keyboard / gamepad movement input"],
                  ["Move Player using movement vector"]),
            Event("event-hit", "Player receives a hit", ["Player overlaps Enemy attack"],
                  ["Subtract 1 health", "Play hit reaction"]),
        ])],
        assets=[
            Asset("asset-hero-mesh", "Hero · 3D mesh", "mesh", "assets/hero/hero.glb", {
                "pc-modern": "assets/hero/hero-high.glb",
                "ps1": "assets/hero/hero-ps1.obj",
                "n64": "assets/hero/hero-n64.obj",
            }, "One logical character, three platform-appropriate mesh builds."),
            Asset("asset-hero-sprite", "Hero · 2D sprites", "sprite", "assets/hero/hero-master.png", {
                "mobile-modern": "assets/hero/hero-mobile.png",
                "gba": "assets/hero/hero-gba.png",
                "gbc": "assets/hero/hero-gbc.png",
            }, "Separate sprite sheets can be authored for each hardware generation."),
        ],
        objects=[
            GameObject("object-hero-3d", "Hero3D", "asset-hero-mesh",
                       {"scale": 1.0, "collision": "capsule", "shadow": True}, {
                "ps1": {"scale": 0.92, "collision": "box", "shadow": False},
                "n64": {"scale": 1.0, "collision": "capsule", "shadow": False},
            }),
            GameObject("object-hero-2d", "Hero2D", "asset-hero-sprite",
                       {"pixels_per_unit": 100, "filter": "linear"}, {
                "gba": {"pixels_per_unit": 1, "filter": "nearest", "palette": "gba-15bit"},
                "gbc": {"pixels_per_unit": 1, "filter": "nearest", "palette": "gbc-limited"},
            }),
        ],
    )
