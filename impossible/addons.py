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
        *,
        include_third_party: bool = True,
        third_party_dir: str | Path | None = None,
    ) -> "AddonRegistry":
        source = Path(path) if path else DEFAULT_REGISTRY
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AddonRegistryError(f"Cannot read {source}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise AddonRegistryError(f"Invalid registry JSON: {exc}") from exc

        registry = cls(raw, source)
        if include_third_party:
            registry.load_third_party(
                Path(third_party_dir) if third_party_dir is not None else DEFAULT_THIRD_PARTY_DIR
            )
        return registry

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
        if not isinstance(ui.get("markers"), list) or any(not isinstance(marker, str) for marker in ui["markers"]):
            raise AddonRegistryError(f"Invalid ACE markers on {item['id']}")
        flags = ui.get("flags")
        required_flags = {
            "trigger", "fake_trigger", "static", "looping", "invertible",
            "incompatible_with_triggers", "deprecated", "highlight",
        }
        if not isinstance(flags, dict) or not required_flags <= flags.keys():
            raise AddonRegistryError(f"Incomplete ACE flags on {item['id']}")
        if any(not isinstance(flags[name], bool) for name in required_flags):
            raise AddonRegistryError(f"ACE flags must be boolean on {item['id']}")
        if item["execution"] == "trigger" and ("trigger" not in ui["markers"] or not flags["trigger"]):
            raise AddonRegistryError(f"Trigger marker/flag missing on {item['id']}")
        if flags["fake_trigger"] and (section != "conditions" or item["execution"] != "predicate"):
            raise AddonRegistryError(f"Fake triggers must remain passive conditions on {item['id']}")
        if flags["static"] and section != "conditions":
            raise AddonRegistryError(f"Static is only valid for conditions on {item['id']}")
        if flags["looping"] and section != "conditions":
            raise AddonRegistryError(f"Looping is only valid for conditions on {item['id']}")
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

    @staticmethod
    def _package_file(package_dir: Path, relative_path: Any, label: str) -> Path:
        """Resolve a package asset while refusing absolute paths and traversal."""
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise AddonRegistryError(f"{label} must be a non-empty relative path.")
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise AddonRegistryError(f"Unsafe {label} path: {relative_path!r}")
        try:
            package_root = package_dir.resolve(strict=True)
            candidate = (package_root / relative).resolve(strict=True)
            candidate.relative_to(package_root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise AddonRegistryError(f"Invalid or out-of-package {label}: {relative_path!r}") from exc
        if not candidate.is_file():
            raise AddonRegistryError(f"{label} is not a file: {relative_path!r}")
        return candidate

    def load_third_party(self, directory: str | Path = DEFAULT_THIRD_PARTY_DIR) -> int:
        """Load metadata-only packages from add-ons/**/addon.json.

        Package entrypoints and permissions are validated as metadata only. No
        JavaScript, Python, native library or WASM code is imported or executed.
        A malformed package is skipped and recorded in diagnostics; built-ins
        remain available.
        """
        root = Path(directory)
        if not root.exists():
            return 0
        if not root.is_dir():
            self.diagnostics.append(f"Third-party add-on path is not a directory: {root}")
            return 0

        try:
            root_resolved = root.resolve(strict=True)
            manifests = sorted(root.rglob("addon.json"))
        except OSError as exc:
            self.diagnostics.append(f"Cannot scan third-party add-ons in {root}: {exc}")
            return 0

        candidates: list[tuple[AddonDefinition, Path, str]] = []
        seen_aces = {
            ace.id
            for existing in self._addons.values()
            for section in SECTIONS
            for ace in getattr(existing, section)
        }

        for manifest_path in manifests:
            try:
                if manifest_path.is_symlink():
                    raise AddonRegistryError("Manifest symlinks are not allowed.")
                package_dir = manifest_path.parent.resolve(strict=True)
                manifest_resolved = manifest_path.resolve(strict=True)
                package_dir.relative_to(root_resolved)
                manifest_resolved.relative_to(package_dir)
                if not manifest_resolved.is_file():
                    raise AddonRegistryError("addon.json is not a regular file.")

                payload = json.loads(manifest_resolved.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise AddonRegistryError("Package manifest root must be an object.")
                if payload.get("format") != "impossible.addon-package" or payload.get("manifestVersion") != 1:
                    raise AddonRegistryError("Unsupported third-party add-on package format/version.")

                addon_data = payload.get("addon")
                package = payload.get("package", {})
                if not isinstance(package, dict):
                    raise AddonRegistryError("Package metadata must be an object.")
                permissions = package.get("permissions", [])
                if not isinstance(permissions, list) or any(not isinstance(p, str) or not p.strip() for p in permissions):
                    raise AddonRegistryError("Package permissions must be an array of non-empty strings.")
                entrypoints = package.get("entrypoints", {})
                if not isinstance(entrypoints, dict) or set(entrypoints) - {"editor", "runtime"}:
                    raise AddonRegistryError("Only editor and runtime entrypoint references are supported.")
                for entrypoint in entrypoints.values():
                    if entrypoint is not None:
                        self._package_file(package_dir, entrypoint, "entrypoint")

                if isinstance(addon_data, dict):
                    icon = addon_data.get("icon", {})
                    if isinstance(icon, dict) and icon.get("kind") == "asset":
                        self._package_file(package_dir, icon.get("name"), "icon asset")

                if not isinstance(addon_data, dict):
                    raise AddonRegistryError("Package must contain an addon descriptor object.")
                declared_id = addon_data.get("id")
                if declared_id in self._addons or any(existing.id == declared_id for existing, _, _ in candidates):
                    raise AddonRegistryError(f"Add-on ID conflicts with an already registered add-on: {declared_id}")
                candidate_seen_aces = set(seen_aces)
                addon = self._parse_addon(addon_data, candidate_seen_aces)
                relative_package = package_dir.relative_to(root_resolved).as_posix()
                candidates.append((addon, package_dir, relative_package))
                seen_aces.update(candidate_seen_aces)
            except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
                self.diagnostics.append(f"Skipped {manifest_path}: {exc}")

        # Resolve package dependencies after discovery so packages may depend on
        # other packages regardless of filesystem traversal order.
        accepted = list(candidates)
        while True:
            known_ids = set(self._addons) | {addon.id for addon, _, _ in accepted}
            known_capabilities = {
                capability
                for addon in self._addons.values()
                for capability in addon.provides
            } | {
                capability
                for addon, _, _ in accepted
                for capability in addon.provides
            }
            rejected = [
                record for record in accepted
                if any(req not in known_ids and req not in known_capabilities for req in record[0].requires)
            ]
            if not rejected:
                break
            for addon, _, relative_package in rejected:
                missing = [
                    req for req in addon.requires
                    if req not in known_ids and req not in known_capabilities
                ]
                self.diagnostics.append(
                    f"Skipped third-party add-on {addon.id} ({relative_package}): unresolved dependencies {missing}"
                )
            accepted = [record for record in accepted if record not in rejected]

        for addon, _, relative_package in accepted:
            self._addons[addon.id] = addon
            self._origins[addon.id] = f"third-party:{relative_package}"

        self._validate_dependencies()
        return len(accepted)

    def origin(self, addon_id: str) -> str:
        """Return 'builtin' or the package-relative third-party origin."""
        self.get(addon_id)
        return self._origins[addon_id]

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
