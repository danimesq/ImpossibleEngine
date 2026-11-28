"""Validated, toolkit-independent built-in add-on registry for ImpossibleEngine."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "addons" / "builtin-v1.json"
DEFAULT_THIRD_PARTY_DIR = ROOT / "add-ons"
KINDS = {"plugin", "behavior", "effect"}
SECTIONS = {"conditions": {"trigger", "predicate"}, "actions": {"command"}, "expressions": {"pure"}}
PARAMETER_TYPES = {"number", "integer", "string", "boolean", "enum", "object", "array",
    "bytes", "uri", "asset", "object_type", "object_instance", "variable", "expression",
    "layer", "layout", "camera", "animation", "font", "key", "gamepad_button", "gamepad_axis",
    "input_action", "polygon", "rectangle", "vector2", "vector3", "color", "matrix4x5",
    "shape", "path", "timeline", "flowchart", "box3"}


class AddonRegistryError(ValueError):
    """Raised when registry metadata or ACE contracts are invalid."""


@dataclass(frozen=True)
class AceDefinition:
    id: str
    name: str
    description: str
    execution: str
    parameters: tuple[dict[str, Any], ...]
    selection: str
    returns: str | None
    writes: tuple[str, ...]
    ui: dict[str, Any]


@dataclass(frozen=True)
class AddonDefinition:
    id: str
    kind: str
    name: str
    category: str
    version: str
    provides: tuple[str, ...]
    requires: tuple[str, ...]
    properties: tuple[dict[str, Any], ...]
    conditions: tuple[AceDefinition, ...]
    actions: tuple[AceDefinition, ...]
    expressions: tuple[AceDefinition, ...]
    implementation_status: str
    engine_runtime: bool
    raw: dict[str, Any]


class AddonRegistry:
    """Stable-ID lookup and filtering without importing the GUI toolkit."""

    def __init__(self, raw: dict[str, Any], source: Path | None = None) -> None:
        self.raw, self.source = raw, source
        self.diagnostics: list[str] = []
        self._origins: dict[str, str] = {}
        self._validate_root(raw)
        self._addons: dict[str, AddonDefinition] = {}
        seen: set[str] = set()
        for item in raw["addons"]:
            addon = self._parse_addon(item, seen)
            if addon.id in self._addons:
                raise AddonRegistryError(f"Duplicate add-on ID: {addon.id}")
            self._addons[addon.id] = addon
            self._origins[addon.id] = "builtin"
        self._validate_dependencies()

    @classmethod
    def load(
        cls,
        path: str | Path | None = None,
        third_party_dir: str | Path | None = None,
    ) -> "AddonRegistry":
        """Load built-ins and safe third-party descriptors without executing code."""
        source = Path(path) if path else DEFAULT_REGISTRY
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AddonRegistryError(f"Cannot read {source}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise AddonRegistryError(f"Invalid registry JSON: {exc}") from exc
        registry = cls(raw, source)
        registry._load_third_party(
            Path(third_party_dir) if third_party_dir is not None else DEFAULT_THIRD_PARTY_DIR
        )
        return registry

    @staticmethod
    def _package_entrypoints(package: Any, package_dir: Path) -> None:
        """Check package entrypoint paths; metadata loading never executes them."""
        if not isinstance(package, dict):
            raise AddonRegistryError("Package metadata must be an object.")
        entrypoints = package.get("entrypoints", {})
        if not isinstance(entrypoints, dict):
            raise AddonRegistryError("Package entrypoints must be an object.")
        root = package_dir.resolve()
        for name, relative_value in entrypoints.items():
            if not isinstance(name, str) or not isinstance(relative_value, str) or not relative_value.strip():
                raise AddonRegistryError("Entrypoint names and paths must be non-empty strings.")
            relative = Path(relative_value)
            if relative.is_absolute():
                raise AddonRegistryError(f"Unsafe entrypoint path: {relative_value}")
            resolved = (root / relative).resolve()
            if not resolved.is_relative_to(root):
                raise AddonRegistryError(f"Unsafe entrypoint path: {relative_value}")
            if not resolved.is_file():
                raise AddonRegistryError(f"Missing package entrypoint: {relative_value}")

    def _load_third_party(self, directory: Path) -> None:
        """Discover addon.json packages as untrusted metadata, never executable code."""
        if not directory.exists():
            return
        try:
            root = directory.resolve()
            manifests = sorted(directory.rglob("addon.json"))
        except OSError as exc:
            self.diagnostics.append(f"Skipped third-party directory {directory}: {exc}")
            return

        candidates: list[tuple[AddonDefinition, str]] = []
        for manifest_path in manifests:
            try:
                resolved_manifest = manifest_path.resolve()
                if not resolved_manifest.is_relative_to(root):
                    raise AddonRegistryError("Manifest path escapes the package directory.")
                package_dir = resolved_manifest.parent
                manifest = json.loads(resolved_manifest.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict) or manifest.get("format") != "impossible.addon-package":
                    raise AddonRegistryError("Unsupported add-on package format.")
                if manifest.get("manifestVersion") != 1:
                    raise AddonRegistryError("Unsupported add-on package manifest version.")
                self._package_entrypoints(manifest.get("package", {}), package_dir)
                addon_raw = manifest.get("addon")
                candidate_seen = {
                    ace.id
                    for addon in self._addons.values()
                    for section in ("conditions", "actions", "expressions")
                    for ace in getattr(addon, section)
                }
                addon = self._parse_addon(addon_raw, candidate_seen)
                if addon.id in self._addons or any(existing.id == addon.id for existing, _ in candidates):
                    raise AddonRegistryError(f"Duplicate add-on ID: {addon.id}")
                origin = "third-party:" + package_dir.relative_to(root).as_posix()
                candidates.append((addon, origin))
            except (OSError, json.JSONDecodeError, AddonRegistryError, TypeError, ValueError) as exc:
                relative = manifest_path.parent.name
                self.diagnostics.append(f"Skipped third-party package {relative}: {exc}")

        # Resolve dependencies in passes so a package can depend on another package
        # discovered later in filesystem order.
        pending = list(candidates)
        while pending:
            progress = False
            for addon, origin in pending[:]:
                ids = set(self._addons)
                capabilities = {item for current in self._addons.values() for item in current.provides}
                available = ids | capabilities | set(addon.provides) | {addon.id}
                if not all(requirement in available for requirement in addon.requires):
                    continue
                existing_ace_ids = {
                    ace.id for current in self._addons.values()
                    for section in ("conditions", "actions", "expressions")
                    for ace in getattr(current, section)
                }
                addon_ace_ids = {
                    ace.id for section in ("conditions", "actions", "expressions")
                    for ace in getattr(addon, section)
                }
                if existing_ace_ids & addon_ace_ids:
                    self.diagnostics.append(f"Skipped third-party package {addon.id}: duplicate ACE ID.")
                else:
                    self._addons[addon.id] = addon
                    self._origins[addon.id] = origin
                    self.raw["addons"].append(addon.raw)
                pending.remove((addon, origin))
                progress = True
            if not progress:
                for addon, _origin in pending:
                    self.diagnostics.append(
                        f"Skipped third-party package {addon.id}: unresolved dependency "
                        + ", ".join(addon.requires)
                    )
                break

    @staticmethod
    def _validate_root(raw: Any) -> None:
        if not isinstance(raw, dict) or raw.get("format") != "impossible.addon-registry" or raw.get("registryVersion") != 1:
            raise AddonRegistryError("Unsupported add-on registry format/version.")
        if not isinstance(raw.get("addons"), list) or not isinstance(raw.get("aceModel"), dict):
            raise AddonRegistryError("Registry must declare aceModel and addons.")

    @staticmethod
    def _validate_parameters(parameters: Any, owner: str) -> None:
        if not isinstance(parameters, list):
            raise AddonRegistryError(f"Parameters must be an array on {owner}.")
        names: set[str] = set()
        for parameter in parameters:
            required = {"name", "label", "description", "type", "required"}
            if not isinstance(parameter, dict) or not required <= parameter.keys():
                raise AddonRegistryError(f"Incomplete parameter metadata on {owner}.")
            name, kind = parameter["name"], parameter["type"]
            if not isinstance(name, str) or not name.strip():
                raise AddonRegistryError(f"Parameter name must be non-empty on {owner}.")
            if not isinstance(kind, str) or kind not in PARAMETER_TYPES:
                raise AddonRegistryError(f"Unknown parameter type {kind!r} on {owner}.{name}.")
            if name in names:
                raise AddonRegistryError(f"Duplicate parameter {name!r} on {owner}.")
            names.add(name)
            if not isinstance(parameter["required"], bool):
                raise AddonRegistryError(f"Parameter required flag must be boolean on {owner}.{name}.")
            if kind == "enum" and (not isinstance(parameter.get("options"), list) or not parameter["options"]):
                raise AddonRegistryError(f"Enum options are required on {owner}.{name}.")
            if "minimum" in parameter and "maximum" in parameter and parameter["minimum"] > parameter["maximum"]:
                raise AddonRegistryError(f"Minimum exceeds maximum on {owner}.{name}.")

    @staticmethod
    def _parse_ace(item: Any, section: str, owner: str, seen: set[str]) -> AceDefinition:
        if not isinstance(item, dict):
            raise AddonRegistryError(f"Malformed {section} entry in {owner}.")
        required = {"id", "name", "description", "execution", "parameters", "selection", "ui"}
        if not required <= item.keys():
            raise AddonRegistryError(f"Incomplete ACE in {owner}: {required - item.keys()}")
        if item["execution"] not in SECTIONS[section]:
            raise AddonRegistryError(f"Wrong execution class for {item['id']}.")
        if not isinstance(item["id"], str) or not item["id"].startswith(owner + ".") or item["id"] in seen:
            raise AddonRegistryError(f"Invalid or duplicate ACE ID: {item['id']!r}")
        seen.add(item["id"])
        AddonRegistry._validate_parameters(item["parameters"], item["id"])
        ui = item["ui"]
        ui_required = {"list_name", "display_string", "description", "category_id", "category_label", "language_key", "markers", "flags"}
        if not isinstance(ui, dict) or not ui_required <= ui.keys():
            raise AddonRegistryError(f"Incomplete ACE UI metadata on {item['id']}")
        if item["execution"] == "trigger" and "trigger" not in ui["markers"]:
            raise AddonRegistryError(f"Trigger marker missing on {item['id']}")
        if section == "expressions" and not isinstance(item.get("returns"), str):
            raise AddonRegistryError(f"Expression return type missing on {item['id']}")
        return AceDefinition(item["id"], str(item["name"]), str(item["description"]), item["execution"],
            tuple(item["parameters"]), str(item["selection"]), item.get("returns"),
            tuple(item.get("writes", ())), ui)

    @classmethod
    def _parse_addon(cls, item: Any, seen: set[str]) -> AddonDefinition:
        required = {"id", "kind", "version", "name", "category", "description", "author",
            "documentation", "icon", "object", "editor", "provides", "requires",
            "properties", "implementation", "conditions", "actions", "expressions", "isDeprecated"}
        if not isinstance(item, dict) or not required <= item.keys():
            raise AddonRegistryError(f"Malformed add-on entry; missing {required - item.keys() if isinstance(item, dict) else required}")
        if item["kind"] not in KINDS or not isinstance(item["id"], str) or not item["id"].startswith(item["kind"] + "."):
            raise AddonRegistryError(f"Invalid add-on namespace: {item['id']!r}")
        if not isinstance(item["isDeprecated"], bool):
            raise AddonRegistryError(f"isDeprecated must be boolean: {item['id']}")
        icon = item["icon"]
        if not isinstance(icon, dict) or icon.get("kind") not in {"builtin", "asset"} or not icon.get("name"):
            raise AddonRegistryError(f"Invalid icon reference: {item['id']}")
        editor = item["editor"]
        if not isinstance(editor, dict) or not isinstance(editor.get("picker"), dict):
            raise AddonRegistryError(f"Missing picker metadata: {item['id']}")
        for field in ("visible", "category", "category_label", "description_visible", "icon_visible"):
            if field not in editor["picker"]:
                raise AddonRegistryError(f"Missing picker field {field}: {item['id']}")
        cls._validate_parameters(item["properties"], item["id"])
        aces = {section: tuple(cls._parse_ace(q, section, item["id"], seen) for q in item[section]) for section in SECTIONS}
        declared = {q.get("id") for q in editor.get("ace_categories", [])}
        used = {q.ui["category_id"] for group in aces.values() for q in group}
        if not used <= declared:
            raise AddonRegistryError(f"Undeclared ACE category on {item['id']}: {used - declared}")
        impl = item["implementation"]
        if impl.get("status") != "specification_only" or impl.get("engine_runtime") is not False:
            raise AddonRegistryError(f"Unverified runtime claim on {item['id']}")
        return AddonDefinition(item["id"], item["kind"], item["name"], item["category"], item["version"],
            tuple(item["provides"]), tuple(item["requires"]), tuple(item["properties"]),
            aces["conditions"], aces["actions"], aces["expressions"], impl["status"], impl["engine_runtime"], item)

    def _validate_dependencies(self) -> None:
        ids = set(self._addons)
        capabilities = {cap for addon in self._addons.values() for cap in addon.provides}
        for addon in self._addons.values():
            for requirement in addon.requires:
                if requirement not in ids and requirement not in capabilities:
                    raise AddonRegistryError(f"Unknown dependency {requirement!r} on {addon.id}")

    def get(self, addon_id: str) -> AddonDefinition:
        try:
            return self._addons[addon_id]
        except KeyError as exc:
            raise KeyError(f"Unknown add-on ID: {addon_id}") from exc

    def find_ace(self, ace_id: str) -> tuple[AddonDefinition, AceDefinition, str] | None:
        for addon in self._addons.values():
            for section in SECTIONS:
                for ace in getattr(addon, section):
                    if ace.id == ace_id:
                        return addon, ace, section
        return None

    def of_kind(self, kind: str) -> tuple[AddonDefinition, ...]:
        if kind not in KINDS:
            raise ValueError(f"Unknown add-on kind: {kind}")
        return tuple(a for a in self._addons.values() if a.kind == kind)

    def by_category(self, category: str, kind: str | None = None) -> tuple[AddonDefinition, ...]:
        values: Iterable[AddonDefinition] = self._addons.values()
        if kind is not None:
            values = (a for a in values if a.kind == kind)
        return tuple(a for a in values if a.category == category)

    def search(self, query: str, kind: str | None = None) -> tuple[AddonDefinition, ...]:
        needle = query.casefold().strip()
        values: Iterable[AddonDefinition] = self._addons.values()
        if kind is not None:
            if kind not in KINDS:
                raise ValueError(f"Unknown add-on kind: {kind}")
            values = (a for a in values if a.kind == kind)
        return tuple(a for a in values if not needle or needle in (a.id + " " + a.name + " " + str(a.raw.get("description", "")) + " " + a.category).casefold())

    def counts(self) -> dict[str, int]:
        values = tuple(self._addons.values())
        return {"addons":len(values),"plugins":sum(a.kind=="plugin" for a in values),
            "behaviors":sum(a.kind=="behavior" for a in values),"effects":sum(a.kind=="effect" for a in values),
            "conditions":sum(len(a.conditions) for a in values),"actions":sum(len(a.actions) for a in values),
            "expressions":sum(len(a.expressions) for a in values)}

    def ids(self) -> tuple[str, ...]:
        return tuple(self._addons)

    def origin(self, addon_id: str) -> str:
        """Return whether an add-on came from the built-in registry or a package."""
        self.get(addon_id)
        return self._origins.get(addon_id, "unknown")
