"""Import validation and headless compilation for native ImpossibleEngine projects.

The Flappy Madruga adapter is intentionally source-pinned and explicit. It does not
pretend to be a generic Construct 2 importer; it validates the original XML, the
normalized project model, the reviewed coverage map and the Rust handler bindings.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# Source SIDs are stable identifiers from the pinned Construct 2 project.
HANDLER_BY_SID: dict[str, str] = {
    "868568479922385": "StopAllAudioOnStart",
    "8450924142424696": "StartButtonOrReturn",
    "6960960697050587": "GooglePlaySignInRequest",
    "3050908862004944": "StartNonAndroidElse",
    "2086025640003727": "GooglePlaySignedIn",
    "2246972820014324": "CommonLayoutStart",
    "7816572494785124": "StartMusicOnce",
    "9923654974799748": "FlapInputOr",
    "2918399259058403": "FlapWhenAlive",
    "199979273240818": "RotateBird",
    "7365620846625415": "CollisionGuard",
    "170743918900562": "GroundCollision",
    "4987440076445908": "SaveHighScoreAfterGround",
    "8821406997890014": "ShowHighScoreAfterGround",
    "3130471190776897": "TopPipeCollision",
    "4999406637386386": "SaveHighScoreAfterTopPipe",
    "715855042734": "ShowHighScoreAfterTopPipe",
    "1336496314225453": "BottomPipeCollision",
    "5467540996491119": "SaveHighScoreAfterBottomPipe",
    "5644737791030659": "ShowHighScoreAfterBottomPipe",
    "9569398275688901": "OutsideLayoutNoOp",
    "2833117000651784": "ScorePipeOnce",
    "2060048028150518": "WrapBackground",
    "30454140128404": "WrapGround",
    "1385689931601852": "MoveBackgroundAndPipes",
    "6231531170117115": "DestroyTopPipe",
    "7423873857133321": "DestroyBottomPipe",
    "6640649658259165": "SpawnObstacleTimer",
    "9708342499359544": "RetryButtonOrReturn",
    "3112928811038152": "RestartAfterWait",
    "2515117097232158": "ChavesLevelProgression",
    "9305905589121505": "ChavesLayoutStart",
}

STATUS_BY_SOURCE = {
    "mapped": "Mapped",
    "mapped_with_host_limit": "HostAdapter",
    "policy_fallback": "PolicyFallback",
    "adapter_callback": "HostAdapter",
    "mapped_media_pending": "MediaPending",
    "mapped_vector_ui": "VectorUi",
    "source_no_op": "SourceNoOp",
    "mapped_with_rng_policy": "RngPolicy",
    "source_semantics_preserved": "SemanticsPreserved",
    "mapped_with_instance_lifetime_interaction": "InstanceLifetime",
}

GROUP_BY_SOURCE = {
    "Movement": "Movement",
    "Collisions": "Collisions",
    "Scoring": "Scoring",
    "Background": "Background",
    "Obstacle": "Obstacle",
    "Restart": "Restart",
    "CommonInLevels": "CommonInLevels",
}

UPDATE_GROUP_ORDER = [
    "Movement",
    "Collisions",
    "Scoring",
    "Background",
    "Obstacle",
    "Restart",
]


class ProjectCompileError(RuntimeError):
    """Raised when source data cannot be compiled without guessing."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProjectCompileError(f"Cannot read {label} at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectCompileError(f"Invalid JSON in {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectCompileError(f"{label} must be a JSON object: {path}")
    return value


def _required_file(root: Path, relative: str, label: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise ProjectCompileError(f"Missing {label}: {path}")
    return path


def _text(element: ET.Element | None, default: str = "") -> str:
    return (element.text or default).strip() if element is not None else default


def _parse_xml(path: Path, label: str) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ProjectCompileError(f"Cannot parse {label} ({path}): {exc}") from exc


def _rust_string(value: str) -> str:
    # JSON string escaping is compatible with ordinary Rust string literals.
    return json.dumps(value, ensure_ascii=False)


def _sheet_group(event: dict[str, Any], source_path: str) -> str | None:
    explicit = event.get("group")
    if explicit:
        return explicit
    if source_path.endswith("Common in-levels.xml"):
        return "CommonInLevels"
    if event.get("sid") in {"9708342499359544", "3112928811038152"}:
        return "Restart"
    return None


def validate_project(project_file: str | Path) -> dict[str, Any]:
    """Validate the native project, pinned source files and every event binding."""
    ieproj = Path(project_file).expanduser().resolve()
    if not ieproj.is_file():
        raise ProjectCompileError(f"Impossible project not found: {ieproj}")
    project_root = ieproj.parent
    project = _read_json(ieproj, "Impossible project")
    if project.get("format") != "impossible.project" or project.get("schema_version") != 1:
        raise ProjectCompileError("Unsupported Impossible project format/version.")

    metadata = project.get("metadata", {})
    upstream = metadata.get("upstream", {})
    build = metadata.get("build", {})
    expected_revision = upstream.get("revision")
    if not expected_revision:
        raise ProjectCompileError("Project does not pin an upstream source revision.")

    source_model_path = _required_file(project_root, metadata.get("source_model", ""), "source model")
    coverage_path = _required_file(project_root, metadata.get("source_coverage", ""), "source coverage")
    migration_path = _required_file(project_root, metadata.get("migration_manifest", ""), "migration manifest")
    assets_path = _required_file(project_root, metadata.get("asset_manifest", ""), "asset manifest")
    upstream_project_path = _required_file(
        project_root, upstream.get("project_file", ""), "pinned Construct 2 project"
    )

    source_model = _read_json(source_model_path, "source model")
    coverage = _read_json(coverage_path, "source coverage")
    migration = _read_json(migration_path, "migration manifest")
    asset_manifest = _read_json(assets_path, "asset manifest")

    revisions = {
        "project": expected_revision,
        "source_model": source_model.get("upstream", {}).get("revision"),
        "coverage": coverage.get("source_revision"),
        "migration": migration.get("source", {}).get("revision"),
    }
    if any(revision != expected_revision for revision in revisions.values()):
        raise ProjectCompileError(f"Source revision mismatch: {revisions}")

    caproj = _parse_xml(upstream_project_path, "Construct 2 project")
    caproj_name = _text(caproj.find("name"))
    if caproj_name != project.get("name"):
        raise ProjectCompileError(
            f"Project name mismatch: .ieproj={project.get('name')!r}, source={caproj_name!r}"
        )
    source_version = _text(caproj.find("version"))
    if source_version != upstream.get("project_version"):
        raise ProjectCompileError("Source project version does not match the pinned import metadata.")

    width = int(_text(caproj.find("./window-size/width"), "0"))
    height = int(_text(caproj.find("./window-size/height"), "0"))
    if (width, height) != (
        int(metadata.get("logical_resolution", {}).get("width", 0)),
        int(metadata.get("logical_resolution", {}).get("height", 0)),
    ):
        raise ProjectCompileError("Logical viewport dimensions differ from the original project.")

    caproj_plugins = {node.attrib.get("id") for node in caproj.findall("./used-plugins/plugin")}
    caproj_behaviors = {node.attrib.get("id") for node in caproj.findall("./used-behaviors/behavior")}
    for object_name, definition in source_model.get("objects", {}).items():
        plugin = definition.get("plugin")
        if plugin not in caproj_plugins:
            raise ProjectCompileError(f"Object {object_name} references undeclared source plugin {plugin!r}.")
        behavior = definition.get("behavior")
        if behavior and behavior not in caproj_behaviors:
            raise ProjectCompileError(f"Object {object_name} references undeclared source behavior {behavior!r}.")

    source_layout_names = [item["name"] for item in source_model.get("layouts_in_project_order", [])]
    manifest_layout_names = migration.get("source_structure", {}).get("layouts", [])
    if source_layout_names != manifest_layout_names:
        raise ProjectCompileError("Source-model layout order differs from the migration manifest.")

    layout_root = project_root / "source" / "legacy-construct2" / "Layouts"
    for layout_name in source_layout_names:
        layout_path = _required_file(layout_root, f"{layout_name}.xml", f"{layout_name} layout")
        layout_xml = _parse_xml(layout_path, f"{layout_name} layout")
        if _text(layout_xml.find("name")) != layout_name:
            raise ProjectCompileError(f"Layout identity mismatch in {layout_path}.")

    native_sheets = {sheet["name"]: sheet for sheet in project.get("event_sheets", [])}
    source_event_count = 0
    event_ids: set[str] = set()
    status_counts: dict[str, int] = {}
    resolved_sheets: list[dict[str, Any]] = []

    for source_sheet in coverage.get("event_sheets", []):
        source_relative = source_sheet["path"]
        source_path = project_root / "source" / "legacy-construct2" / source_relative
        source_path = _required_file(project_root, str(source_path.relative_to(project_root)), "source Event Sheet")
        source_xml = _parse_xml(source_path, source_relative)
        actual_ids = [
            node.attrib.get("sid", "")
            for node in source_xml.iter("event-block")
        ]
        expected_events = source_sheet.get("events", [])
        expected_ids = [str(event.get("sid", "")) for event in expected_events]
        if actual_ids != expected_ids:
            missing = sorted(set(actual_ids) - set(expected_ids))
            stale = sorted(set(expected_ids) - set(actual_ids))
            raise ProjectCompileError(
                f"Event coverage differs from original XML for {source_relative}; "
                f"unmapped={missing}, stale={stale}, order_matches={actual_ids == expected_ids}"
            )

        actual_includes = [_text(node) for node in source_xml.findall(".//include")]
        if actual_includes != source_sheet.get("includes", []):
            raise ProjectCompileError(f"Include graph mismatch in {source_relative}.")

        group_names = [node.attrib.get("title", "") for node in source_xml.findall(".//event-group")]
        expected_groups = [node.get("title", "") for node in source_sheet.get("groups", [])]
        if group_names != expected_groups:
            raise ProjectCompileError(f"Event group order mismatch in {source_relative}.")

        sheet_name = Path(source_relative).stem
        native_sheet = native_sheets.get(sheet_name)
        if native_sheet is None:
            raise ProjectCompileError(f"Native .ieproj is missing Event Sheet {sheet_name!r}.")
        native_ids = [str(event.get("source_id", "")) for event in native_sheet.get("events", [])]
        if native_ids != expected_ids:
            raise ProjectCompileError(f"Native .ieproj event rows do not match {source_relative}.")

        for event in expected_events:
            sid = str(event.get("sid", ""))
            if sid in event_ids:
                raise ProjectCompileError(f"Duplicate source event SID across sheets: {sid}")
            event_ids.add(sid)
            if sid not in HANDLER_BY_SID:
                raise ProjectCompileError(f"No executable Rust handler binding for source event {sid}.")
            status = event.get("status")
            if status not in STATUS_BY_SOURCE:
                raise ProjectCompileError(f"Unclassified source event status {status!r} on SID {sid}.")
            status_counts[status] = status_counts.get(status, 0) + 1
            source_event_count += 1

        resolved_sheets.append({
            "name": sheet_name,
            "path": source_relative,
            "event_count": len(expected_events),
            "includes": actual_includes,
            "groups": group_names,
        })

    if source_event_count != len(HANDLER_BY_SID):
        extra = sorted(set(HANDLER_BY_SID) - event_ids)
        raise ProjectCompileError(
            f"Source event inventory is incomplete: found {source_event_count}, "
            f"handler bindings={len(HANDLER_BY_SID)}, unused_handlers={extra}"
        )

    # Confirm the editor container itself retains all five original Event Sheets.
    expected_sheet_names = {Path(sheet["path"]).stem for sheet in coverage.get("event_sheets", [])}
    if set(native_sheets) != expected_sheet_names:
        raise ProjectCompileError("Native .ieproj Event Sheet list differs from the pinned source project.")

    cargo_workspace = (project_root / build.get("cargo_workspace", "../..")).resolve()
    cargo_manifest = cargo_workspace / "Cargo.toml"
    if not cargo_manifest.is_file():
        raise ProjectCompileError(f"Cargo workspace manifest not found: {cargo_manifest}")
    package_name = build.get("cargo_package")
    if package_name != "flappy-madruga":
        raise ProjectCompileError(f"Unsupported project Cargo package: {package_name!r}")

    pending_assets = [
        item for item in asset_manifest.get("assets", [])
        if item.get("status") == "pending"
    ]
    warnings = [
        f"{len(pending_assets)} original media groups are pending; this logic target does not require their bytes.",
        "Google Play Games credentials/SDK are not configured; Android sign-in remains an explicit host capability.",
        "Rendering is deliberately excluded from the headless logic target."
    ]

    return {
        "project": project.get("name"),
        "project_file": str(ieproj),
        "source_revision": expected_revision,
        "source_project_version": source_version,
        "logical_resolution": [width, height],
        "layouts": source_layout_names,
        "event_sheets": resolved_sheets,
        "source_events": source_event_count,
        "handler_bindings": len(HANDLER_BY_SID),
        "status_counts": status_counts,
        "objects": len(project.get("objects", [])),
        "assets": len(project.get("assets", [])),
        "pending_asset_groups": len(pending_assets),
        "target": "logic",
        "cargo_workspace": str(cargo_workspace),
        "cargo_package": package_name,
        "warnings": warnings,
    }


def render_source_bindings(report: dict[str, Any], coverage_path: str | Path) -> str:
    """Create statically typed Rust bindings from the validated source coverage file."""
    coverage = _read_json(Path(coverage_path), "source coverage")
    entries: list[tuple[dict[str, Any], str | None]] = []
    for sheet in coverage["event_sheets"]:
        for event in sheet.get("events", []):
            sid = str(event["sid"])
            group = _sheet_group(event, sheet["path"])
            entries.append((event, group))

    lines = [
        "// @generated by impossible-compile. Do not edit by hand.",
        "// Each SID is checked against the pinned original Event Sheet XML.",
        "use impossible_runtime::{SourceEventBinding, SourceEventHandler, SourceEventStatus, SourceGroup};",
        "",
        f"pub const SOURCE_REVISION: &str = {_rust_string(report['source_revision'])};",
        f"pub const SOURCE_EVENT_COUNT: usize = {len(entries)};",
        "",
        "pub const SOURCE_EVENTS: &[SourceEventBinding] = &[",
    ]
    for event, group in entries:
        sid = str(event["sid"])
        handler = HANDLER_BY_SID[sid]
        status = STATUS_BY_SOURCE[event["status"]]
        group_expr = "None" if group is None else f"Some(SourceGroup::{GROUP_BY_SOURCE.get(group, group)})"
        parent = event.get("parent_sid")
        parent_expr = "None" if not parent else f"Some({_rust_string(str(parent))})"
        lines.append(
            "    SourceEventBinding { "
            f"sid: {_rust_string(sid)}, "
            f"name: {_rust_string(str(event.get('meaning', '')))}, "
            f"group: {group_expr}, parent_sid: {parent_expr}, "
            f"handler: SourceEventHandler::{handler}, status: SourceEventStatus::{status} "
            "},"
        )
    lines.extend([
        "];",
        "",
        "pub const SOURCE_UPDATE_ORDER: &[SourceGroup] = &[",
        *[f"    SourceGroup::{group}," for group in UPDATE_GROUP_ORDER],
        "];",
        "",
        "pub const SOURCE_CHAVES_ORDER: &[SourceGroup] = &[SourceGroup::CommonInLevels];",
        "",
    ])
    return "\n".join(lines)


def generate_source_bindings(project_file: str | Path) -> Path:
    """Validate the import then regenerate the Rust source event table."""
    report = validate_project(project_file)
    ieproj = Path(project_file).expanduser().resolve()
    project_root = ieproj.parent
    metadata = _read_json(ieproj, "Impossible project")["metadata"]
    coverage_path = project_root / metadata["source_coverage"]
    generated = project_root / "src" / "generated" / "source_events.rs"
    generated.parent.mkdir(parents=True, exist_ok=True)
    content = render_source_bindings(report, coverage_path)
    if not generated.exists() or generated.read_text(encoding="utf-8") != content:
        generated.write_text(content, encoding="utf-8")
    return generated


def compile_project(project_file: str | Path, target: str = "logic") -> dict[str, Any]:
    """Generate the source binding table, test the headless motor and build the Rust library."""
    if target != "logic":
        raise ProjectCompileError(
            f"Target {target!r} is not available in this round. Use --target logic; graphics are deferred."
        )
    report = validate_project(project_file)
    generated = generate_source_bindings(project_file)
    workspace = Path(report["cargo_workspace"])
    commands = [
        ["cargo", "test", "--workspace"],
        ["cargo", "build", "--package", "flappy-madruga", "--lib", "--release"],
    ]
    logs: list[dict[str, Any]] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        logs.append({
            "command": " ".join(command),
            "returncode": completed.returncode,
            "output": completed.stdout,
        })
        if completed.returncode != 0:
            raise ProjectCompileError(
                f"Build command failed ({' '.join(command)}):\n{completed.stdout}"
            )
    report["generated_source_bindings"] = str(generated)
    report["commands"] = logs
    report["build_status"] = "passed"
    report["artifact"] = str(workspace / "target" / "release" / "libflappy_madruga.rlib")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="impossible-compile",
        description="Validate and compile a native ImpossibleEngine project."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "compile"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", required=True, help="Path to an .ieproj file")
        sub.add_argument("--target", default="logic", choices=["logic"],
                         help="Headless target; renderer integration is deferred")
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            result = validate_project(args.project)
        else:
            result = compile_project(args.project, args.target)
    except (ProjectCompileError, OSError, ValueError) as exc:
        print(f"[impossible-compile] ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
