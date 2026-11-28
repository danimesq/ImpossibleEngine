"""Headless command-line interface for ImpossibleEngine.

Importing this module never imports GTK. The GUI is loaded only when explicitly
requested or when the launcher is invoked without a command.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .addons import AddonRegistry, AddonRegistryError
from .model import PROFILE_BY_ID, EventSheet, Project, PLATFORM_PROFILES
from .operations import (
    add_event,
    add_event_action,
    add_event_condition,
    add_project_addon,
    remove_event,
    remove_project_addon,
    set_active_platform,
    set_asset_variant,
    set_event_enabled,
    set_object_override,
)
from .storage import load_project, save_project


def _launch_gui() -> int:
    """Import the GTK application lazily so headless CLI use has no GTK dependency."""
    from .app import main as gui_main

    return gui_main([sys.argv[0]])


def _format_option(parser: argparse.ArgumentParser, default: str = "table") -> None:
    parser.add_argument(
        "--format", choices=("table", "json"), default=default,
        help="Output format (table or machine-readable JSON).",
    )


def _emit_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def _emit_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    if not rows:
        print("(no results)")
        return
    headers = [title for _, title in columns]
    values = [[str(row.get(key, "")) for key, _ in columns] for row in rows]
    widths = [max(len(headers[i]), *(len(row[i]) for row in values)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in values:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def _emit(value: Any, output_format: str = "json", columns: list[tuple[str, str]] | None = None) -> None:
    if output_format == "json":
        _emit_json(value)
    elif isinstance(value, list) and columns:
        _emit_table(value, columns)
    elif isinstance(value, dict):
        print("\n".join(f"{key}: {item}" for key, item in value.items()))
    else:
        print(value)


def _load_project(path: str) -> Project:
    return load_project(path)


def _save_project(project: Project, path: str) -> None:
    save_project(project, path)


def _canonical_project_addon_id(entry: dict[str, Any]) -> str:
    addon_id = str(entry.get("id", ""))
    kind = str(entry.get("type", entry.get("kind", "")))
    if addon_id and "." not in addon_id and kind:
        return f"{kind}.{addon_id.lower().replace(' ', '-')}"
    return addon_id


def _project_summary(project: Project, path: str) -> dict[str, Any]:
    summary = {
        "path": str(Path(path).expanduser()),
        "name": project.name,
        "schema_version": project.schema_version,
        "active_platform": project.active_platform,
        "event_sheets": len(project.event_sheets),
        "events": sum(len(sheet.events) for sheet in project.event_sheets),
        "layouts": len(project.layouts),
        "objects": len(project.objects),
        "assets": len(project.assets),
        "used_addons": len(project.used_addons),
        "native_index": project.native_index,
    }
    if project.native_index:
        index_counts: dict[str, int] = {}
        for kind, key in RESOURCE_INDEX_KINDS.items():
            index_counts[kind] = len(_walk_index_items(project.extra_fields.get(key), kind))
        root_folders = project.extra_fields.get("rootFileFolders", {})
        if isinstance(root_folders, dict):
            for kind in ("script", "sound", "music", "video", "font", "icon", "file"):
                index_counts[kind] = len(_walk_index_items(root_folders.get(kind), kind))
        summary["indexed_resources"] = index_counts
        summary["indexed_resource_count"] = sum(index_counts.values())
        summary["indexed_layouts"] = index_counts.get("layout", 0)
        summary["indexed_event_sheets"] = index_counts.get("event-sheet", 0)
    return summary


def _project_diagnostics(project: Project) -> tuple[list[str], list[str]]:
    """Return conservative structural errors and non-fatal reference warnings."""
    errors: list[str] = []
    warnings: list[str] = []

    def duplicates(values: list[str], label: str) -> None:
        seen: set[str] = set()
        for value in values:
            if value in seen:
                errors.append(f"Duplicate {label} ID: {value}")
            seen.add(value)

    duplicates([item.id for item in project.event_sheets], "Event Sheet")
    duplicates([item.id for item in project.assets], "asset")
    duplicates([item.id for item in project.objects], "object")
    duplicates([item.id for item in project.layouts], "layout")
    for sheet in project.event_sheets:
        duplicates([item.id for item in sheet.events], f"event in {sheet.id}")

    sheet_ids = {item.id for item in project.event_sheets}
    object_ids = {item.id for item in project.objects}
    asset_ids = {item.id for item in project.assets}
    for layout in project.layouts:
        if layout.event_sheet_id not in sheet_ids:
            warnings.append(
                f"Layout {layout.id} references missing Event Sheet {layout.event_sheet_id}."
            )
        for instance in layout.instances:
            if instance.object_id not in object_ids:
                warnings.append(
                    f"Instance {instance.id} in layout {layout.id} references missing object {instance.object_id}."
                )
    for obj in project.objects:
        if obj.asset_id and obj.asset_id not in asset_ids:
            warnings.append(f"Object {obj.id} references missing asset {obj.asset_id}.")
    if project.active_platform not in PROFILE_BY_ID:
        errors.append(f"Unknown active platform: {project.active_platform}")
    return errors, warnings


def _addon_summary(addon: Any) -> dict[str, Any]:
    return {
        "id": addon.id,
        "kind": addon.kind,
        "name": addon.name,
        "category": addon.category,
        "version": addon.version,
        "implementation_status": addon.implementation_status,
        "engine_runtime": addon.engine_runtime,
        "deprecated": bool(addon.raw.get("isDeprecated", False)),
        "author": addon.raw.get("author", "Unknown"),
        "conditions": len(addon.conditions),
        "actions": len(addon.actions),
        "expressions": len(addon.expressions),
        "requires": list(addon.requires),
        "provides": list(addon.provides),
    }


def _event_rows(project: Project, sheet_id: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for sheet in project.event_sheets:
        if sheet_id and sheet.id != sheet_id:
            continue
        for index, event in enumerate(sheet.events, start=1):
            rows.append({
                "sheet_id": sheet.id,
                "sheet": sheet.name,
                "index": index,
                "id": event.id,
                "name": event.name,
                "enabled": event.enabled,
                "conditions": len(event.conditions),
                "actions": len(event.actions),
            })
    return rows


def _handle_project(args: argparse.Namespace) -> int:
    if args.project_action == "create":
        destination = Path(args.path).expanduser()
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite existing project: {destination}")
        project = Project(
            name=args.name,
            event_sheets=[] if args.no_default_sheet else [EventSheet("sheet-main", "Gameplay", [])],
        )
        _save_project(project, str(destination))
        _emit({"created": True, **_project_summary(project, str(destination))}, args.format)
        return 0

    project = _load_project(args.project)
    if args.project_action == "inspect":
        summary = _project_summary(project, args.project)
        summary.update({
            "event_sheet_details": [
                {
                    "id": sheet.id, "name": sheet.name,
                    "events": len(sheet.events), "includes": list(sheet.includes),
                }
                for sheet in project.event_sheets
            ],
            "used_addons_details": project.used_addons,
        })
        _emit(summary, args.format)
        return 0

    if args.project_action == "validate":
        errors, warnings = _project_diagnostics(project)
        report = {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "summary": _project_summary(project, args.project),
        }
        _emit(report, args.format)
        return 0 if not errors else 1

    if args.project_action == "set-platform":
        if project.native_index:
            raise ValueError(
                "Target editing for native resource-index projects is not yet supported; "
                "this command currently edits the GTK prototype's inline project model."
            )
        set_active_platform(project, args.platform)
        _save_project(project, args.project)
        _emit({
            "updated": True, "active_platform": project.active_platform,
            "project": str(Path(args.project).expanduser()),
        }, args.format)
        return 0

    raise ValueError(f"Unsupported project command: {args.project_action}")


def _handle_addons(args: argparse.Namespace) -> int:
    registry = AddonRegistry.load(args.registry, args.third_party_dir)
    if args.addon_action == "list" and args.project:
        project = _load_project(args.project)
        rows = []
        for entry in project.used_addons:
            addon_id = _canonical_project_addon_id(entry)
            try:
                addon = registry.get(addon_id)
                name, kind, category = addon.name, addon.kind, addon.category
                origin, available = registry.origin(addon_id), True
            except KeyError:
                name = str(entry.get("name", addon_id))
                kind = str(entry.get("type", entry.get("kind", "unknown")))
                category, origin, available = "", "missing", False
            if args.kind and kind != args.kind:
                continue
            if args.category and category.casefold() != args.category.casefold():
                continue
            if args.search and args.search.casefold() not in (addon_id + " " + name).casefold():
                continue
            rows.append({
                "id": addon_id, "name": name, "kind": kind, "category": category,
                "bundled": bool(entry.get("bundled", False)), "origin": origin,
                "available": available,
            })
        result = {
            "project": str(Path(args.project).expanduser()),
            "count": len(rows),
            "addons": rows,
        }
        _emit(result if args.format == "json" else rows, args.format, [
            ("id", "ID"), ("kind", "TYPE"), ("name", "NAME"),
            ("bundled", "BUNDLED"), ("origin", "ORIGIN"), ("available", "AVAILABLE"),
        ])
        return 0

    if args.addon_action == "list":
        addons = registry.search(args.search or "", kind=args.kind)
        if args.category:
            addons = tuple(a for a in addons if a.category.casefold() == args.category.casefold())
        if not args.include_deprecated:
            addons = tuple(a for a in addons if not a.raw.get("isDeprecated", False))
        rows = [_addon_summary(addon) for addon in addons]
        for row in rows:
            row["origin"] = registry.origin(row["id"])
        result = {
            "count": len(rows),
            "registry": str(registry.source or ""),
            "addons": rows,
            "diagnostics": list(registry.diagnostics),
        }
        _emit(result if args.format == "json" else rows, args.format,
              [("id", "ID"), ("kind", "TYPE"), ("name", "NAME"),
               ("category", "CATEGORY"), ("origin", "ORIGIN"),
               ("implementation_status", "STATUS")])
        return 0

    if args.addon_action == "show":
        addon = registry.get(args.addon_id)
        _emit({**addon.raw, "origin": registry.origin(addon.id)}, args.format)
        return 0

    if args.addon_action in ("add", "remove"):
        project = _load_project(args.project)
        if args.addon_action == "add":
            added = add_project_addon(project, args.addon_id, registry)
            _save_project(project, args.project)
            result = {
                "updated": bool(added),
                "requested_addon": args.addon_id,
                "added": added,
                "already_present": not bool(added),
                "project": str(Path(args.project).expanduser()),
                "note": "This records add-on metadata only; catalogue descriptors are not runtime implementations.",
            }
        else:
            removed = remove_project_addon(project, args.addon_id, registry)
            if removed:
                _save_project(project, args.project)
            result = {
                "updated": removed,
                "removed": args.addon_id if removed else None,
                "already_absent": not removed,
                "project": str(Path(args.project).expanduser()),
            }
        _emit(result, args.format)
        return 0

    raise ValueError(f"Unsupported add-on command: {args.addon_action}")


def _handle_events(args: argparse.Namespace) -> int:
    if args.events_action == "list":
        project = _load_project(args.project)
        if project.native_index:
            raise ValueError(
                "Native Event Sheet documents are separate resources. Use the resources list command "
                "to inspect them; event contents are not parsed by this CLI yet."
            )
        rows = _event_rows(project, args.sheet)
        if args.format == "json":
            _emit(rows, "json")
        else:
            _emit_table(rows, [
                ("sheet_id", "SHEET ID"), ("id", "EVENT ID"), ("name", "NAME"),
                ("enabled", "ENABLED"), ("conditions", "CONDITIONS"), ("actions", "ACTIONS"),
            ])
        return 0

    project = _load_project(args.project)
    if project.native_index:
        raise ValueError(
            "Event Sheet documents are separate resources in native .ieproj files. "
            "The current CLI edits Event Sheets only in the GTK prototype's inline project model."
        )
    if args.events_action == "add":
        event = add_event(project, args.name, args.sheet)
        _save_project(project, args.project)
        _emit({"created": True, "sheet": args.sheet or project.event_sheets[0].id,
               "event": {"id": event.id, "name": event.name}}, args.format)
        return 0

    if args.events_action in ("enable", "disable"):
        event = set_event_enabled(project, args.event_id, args.events_action == "enable", args.sheet)
        _save_project(project, args.project)
        _emit({"updated": True, "id": event.id, "enabled": event.enabled}, args.format)
        return 0

    if args.events_action == "remove":
        event = remove_event(project, args.event_id, args.sheet)
        _save_project(project, args.project)
        _emit({"removed": True, "id": event.id}, args.format)
        return 0

    if args.events_action in ("condition", "action"):
        expression = args.text
        if args.events_action == "condition":
            event = add_event_condition(project, args.event_id, expression, args.sheet)
        else:
            event = add_event_action(project, args.event_id, expression, args.sheet)
        _save_project(project, args.project)
        key = "conditions" if args.events_action == "condition" else "actions"
        _emit({"updated": True, "event_id": event.id, key: getattr(event, key)}, args.format)
        return 0

    raise ValueError(f"Unsupported Event Sheet command: {args.events_action}")


def _handle_layouts(args: argparse.Namespace) -> int:
    project = _load_project(args.project)
    if project.native_index:
        rows = _walk_index_items(project.extra_fields.get("layouts"), "layout")
        _emit(rows, args.format, [
            ("name", "NAME"), ("folder", "FOLDER"),
        ])
        return 0
    rows = [{
        "id": layout.id,
        "name": layout.name,
        "event_sheet_id": layout.event_sheet_id,
        "instances": len(layout.instances),
        "includes": len(layout.includes),
    } for layout in project.layouts]
    _emit(rows if args.format == "json" else rows, args.format, [
        ("id", "ID"), ("name", "NAME"), ("event_sheet_id", "EVENT SHEET"),
        ("instances", "INSTANCES"), ("includes", "INCLUDES"),
    ])
    return 0


def _handle_objects(args: argparse.Namespace) -> int:
    project = _load_project(args.project)
    if project.native_index:
        raise ValueError(
            "Native object-type resources are separate files. Use the resources list command "
            "to inspect them; editing is not yet implemented for the native resource format."
        )
    if args.objects_action == "list":
        rows = [{
            "id": obj.id, "name": obj.name, "asset_id": obj.asset_id,
            "base_properties": obj.base_properties,
            "platform_overrides": obj.platform_overrides,
        } for obj in project.objects]
        _emit(rows, args.format, [
            ("id", "ID"), ("name", "NAME"), ("asset_id", "ASSET"),
        ])
        return 0

    try:
        values = json.loads(args.values)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --values JSON: {exc}") from exc
    set_object_override(project, args.object_id, args.platform, values)
    _save_project(project, args.project)
    _emit({
        "updated": True, "object_id": args.object_id, "platform": args.platform,
        "overrides": values,
    }, args.format)
    return 0


def _handle_assets(args: argparse.Namespace) -> int:
    project = _load_project(args.project)
    if project.native_index:
        raise ValueError(
            "Native assets are indexed separately from the GTK prototype model. "
            "Use the resources list command to inspect indexed resource files."
        )
    if args.assets_action == "list":
        rows = [{
            "id": asset.id, "name": asset.name, "kind": asset.kind,
            "source": asset.source, "variants": asset.variants, "notes": asset.notes,
        } for asset in project.assets]
        _emit(rows, args.format, [
            ("id", "ID"), ("name", "NAME"), ("kind", "TYPE"), ("source", "SOURCE"),
        ])
        return 0

    set_asset_variant(project, args.asset_id, args.platform, None if args.clear else args.path)
    _save_project(project, args.project)
    asset = next(item for item in project.assets if item.id == args.asset_id)
    _emit({
        "updated": True, "asset_id": asset.id, "platform": args.platform,
        "variant": asset.variants.get(args.platform),
    }, args.format)
    return 0


RESOURCE_INDEX_KINDS = {
    "object-type": "objectTypes",
    "family": "families",
    "layout": "layouts",
    "event-sheet": "eventSheets",
    "timeline": "timelines",
    "flowchart": "flowcharts",
    "3d-model": "3dmodels",
    "palette": "palettes",
    "tilemap-brush": "tilemapBrushes",
}


def _walk_index_items(node: Any, kind: str, folder: str = "") -> list[dict[str, Any]]:
    """Flatten an ordered project-index folder tree without discarding its path."""
    if not isinstance(node, dict):
        return []
    rows: list[dict[str, Any]] = []
    items = node.get("items", [])
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                name = str(item.get("name", item.get("id", item.get("fileName", "Untitled"))))
                row = {"kind": kind, "name": name, "folder": folder, "metadata": item}
            else:
                row = {"kind": kind, "name": str(item), "folder": folder}
            rows.append(row)
    children = node.get("subfolders", [])
    if isinstance(children, list):
        for child in children:
            if not isinstance(child, dict):
                continue
            child_name = str(child.get("name", ""))
            child_folder = "/".join(part for part in (folder, child_name) if part)
            rows.extend(_walk_index_items(child, kind, child_folder))
    return rows


def _handle_resources(args: argparse.Namespace) -> int:
    project = _load_project(args.project)
    rows: list[dict[str, Any]] = []
    for kind, key in RESOURCE_INDEX_KINDS.items():
        rows.extend(_walk_index_items(project.extra_fields.get(key), kind))
    root_folders = project.extra_fields.get("rootFileFolders", {})
    if isinstance(root_folders, dict):
        for kind in ("script", "sound", "music", "video", "font", "icon", "file"):
            rows.extend(_walk_index_items(root_folders.get(kind), kind))

    # Include resources from the current GTK editor model as well as index-based projects.
    for kind, collection in (
        ("asset", project.assets),
        ("object-type", project.objects),
        ("layout", project.layouts),
        ("event-sheet", project.event_sheets),
    ):
        for item in collection:
            rows.append({
                "kind": kind, "name": item.name, "folder": "",
                "id": item.id,
            })

    if args.kind:
        rows = [row for row in rows if row["kind"] == args.kind]
    if args.search:
        needle = args.search.casefold()
        rows = [
            row for row in rows
            if needle in (row.get("name", "") + " " + row.get("folder", "")).casefold()
        ]
    result = {
        "project": str(Path(args.project).expanduser()),
        "count": len(rows),
        "resources": rows,
    }
    _emit(result if args.format == "json" else rows, args.format, [
        ("kind", "TYPE"), ("name", "NAME"), ("folder", "FOLDER"), ("id", "ID"),
    ])
    return 0


def _handle_platforms(args: argparse.Namespace) -> int:
    rows = [{
        "id": item.id, "name": item.name, "family": item.family,
        "dimension": item.dimension, "renderer": item.renderer,
        "description": item.description, "budget_hint": item.budget_hint,
    } for item in PLATFORM_PROFILES]
    _emit(rows, args.format, [
        ("id", "ID"), ("name", "NAME"), ("family", "FAMILY"),
        ("dimension", "DIMENSION"), ("renderer", "RENDERER"),
    ])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="impossible",
        description="Inspect and edit ImpossibleEngine projects without opening the GUI.",
        epilog=(
            "Examples:\n"
            "  impossible addons list --kind behavior\n"
            "  impossible addons add plugin.sprite --project game.ieproj\n"
            "  impossible events add --project game.ieproj --name \"Player jumps\"\n"
            "  impossible events condition add --project game.ieproj --event event-1 --text \"On jump\"\n"
            "  impossible project validate --project game.ieproj\n"
            "  impossible gui"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    gui = commands.add_parser("gui", help="Open the graphical editor.")
    gui.set_defaults(handler=lambda _args: _launch_gui())

    project = commands.add_parser("project", help="Create, inspect and validate projects.")
    project_commands = project.add_subparsers(dest="project_action", required=True)
    create = project_commands.add_parser("create", help="Create a new editable project.")
    create.add_argument("--path", required=True, help="Destination .ieproj path.")
    create.add_argument("--name", required=True, help="Project display name.")
    create.add_argument("--no-default-sheet", action="store_true", help="Do not create the default Gameplay sheet.")
    _format_option(create)
    create.set_defaults(handler=_handle_project)
    for action, description in (
        ("inspect", "Show project metadata and resource counts."),
        ("validate", "Check the editable project model and references."),
    ):
        sub = project_commands.add_parser(action, help=description)
        sub.add_argument("--project", required=True, help="Path to the .ieproj file.")
        _format_option(sub)
        sub.set_defaults(handler=_handle_project)
    set_platform = project_commands.add_parser("set-platform", help="Change the active target profile.")
    set_platform.add_argument("--project", required=True)
    set_platform.add_argument("--platform", required=True, choices=sorted(PROFILE_BY_ID))
    _format_option(set_platform)
    set_platform.set_defaults(handler=_handle_project)

    addons = commands.add_parser("addons", help="Browse and select add-ons.")
    addon_commands = addons.add_subparsers(dest="addon_action", required=True)
    addon_list = addon_commands.add_parser("list", help="List built-in and third-party add-on descriptors.")
    addon_list.add_argument("--kind", choices=("plugin", "behavior", "effect"))
    addon_list.add_argument("--category")
    addon_list.add_argument("--search")
    addon_list.add_argument("--include-deprecated", action="store_true")
    addon_list.add_argument("--project", help="List the add-ons selected in this project instead of the full catalogue.")
    addon_list.add_argument("--registry", help="Path to an alternate built-in registry JSON file.")
    addon_list.add_argument("--third-party-dir", help="Directory containing third-party addon.json packages (default: ./add-ons).")
    _format_option(addon_list)
    addon_list.set_defaults(handler=_handle_addons)
    addon_show = addon_commands.add_parser("show", help="Show an add-on descriptor and its ACEs.")
    addon_show.add_argument("addon_id")
    addon_show.add_argument("--registry")
    addon_show.add_argument("--third-party-dir")
    _format_option(addon_show, "json")
    addon_show.set_defaults(handler=_handle_addons)
    for action, description in (
        ("add", "Add an add-on descriptor to a project."),
        ("remove", "Remove an add-on descriptor from a project."),
    ):
        sub = addon_commands.add_parser(action, help=description)
        sub.add_argument("addon_id")
        sub.add_argument("--project", required=True)
        sub.add_argument("--registry")
        sub.add_argument("--third-party-dir")
        _format_option(sub, "json")
        sub.set_defaults(handler=_handle_addons)

    events = commands.add_parser("events", help="Inspect and edit Event Sheets.")
    event_commands = events.add_subparsers(dest="events_action", required=True)
    event_list = event_commands.add_parser("list", help="List events in a project.")
    event_list.add_argument("--project", required=True)
    event_list.add_argument("--sheet")
    _format_option(event_list)
    event_list.set_defaults(handler=_handle_events)
    event_add = event_commands.add_parser("add", help="Add an event to an Event Sheet.")
    event_add.add_argument("--project", required=True)
    event_add.add_argument("--sheet")
    event_add.add_argument("--name", required=True)
    _format_option(event_add, "json")
    event_add.set_defaults(handler=_handle_events)
    for action in ("enable", "disable", "remove"):
        sub = event_commands.add_parser(action, help=f"{action.capitalize()} or remove an event.")
        sub.add_argument("--project", required=True)
        sub.add_argument("--event-id", required=True)
        sub.add_argument("--sheet")
        _format_option(sub, "json")
        sub.set_defaults(handler=_handle_events)
    for action in ("condition", "action"):
        parent = event_commands.add_parser(action, help=f"Manage event {action}s.")
        nested = parent.add_subparsers(dest=f"{action}_action", required=True)
        sub = nested.add_parser("add", help=f"Append an event {action}.")
        sub.add_argument("--project", required=True)
        sub.add_argument("--event-id", required=True)
        sub.add_argument("--sheet")
        sub.add_argument("--text", required=True)
        _format_option(sub, "json")
        sub.set_defaults(handler=_handle_events)

    layouts = commands.add_parser("layouts", help="List project layouts and their instances.")
    layouts.add_argument("--project", required=True)
    _format_option(layouts)
    layouts.set_defaults(handler=_handle_layouts)

    objects = commands.add_parser("objects", help="Inspect objects or edit platform overrides.")
    object_commands = objects.add_subparsers(dest="objects_action", required=True)
    object_list = object_commands.add_parser("list", help="List logical project objects.")
    object_list.add_argument("--project", required=True)
    _format_option(object_list)
    object_list.set_defaults(handler=_handle_objects)
    object_override = object_commands.add_parser("set-override", help="Replace an object's JSON overrides for a target.")
    object_override.add_argument("--project", required=True)
    object_override.add_argument("--object-id", required=True)
    object_override.add_argument("--platform", required=True, choices=sorted(PROFILE_BY_ID))
    object_override.add_argument("--values", required=True, help="JSON object, for example '{\"scale\": 0.8}'.")
    _format_option(object_override, "json")
    object_override.set_defaults(handler=_handle_objects)

    assets = commands.add_parser("assets", help="Inspect assets or manage target-specific asset variants.")
    asset_commands = assets.add_subparsers(dest="assets_action", required=True)
    asset_list = asset_commands.add_parser("list", help="List project assets.")
    asset_list.add_argument("--project", required=True)
    _format_option(asset_list)
    asset_list.set_defaults(handler=_handle_assets)
    asset_variant = asset_commands.add_parser("set-variant", help="Set or clear an asset source for one target.")
    asset_variant.add_argument("--project", required=True)
    asset_variant.add_argument("--asset-id", required=True)
    asset_variant.add_argument("--platform", required=True, choices=sorted(PROFILE_BY_ID))
    variant_source = asset_variant.add_mutually_exclusive_group(required=True)
    variant_source.add_argument("--path", help="Project-relative or absolute source path.")
    variant_source.add_argument("--clear", action="store_true", help="Remove the explicit variant and use fallback resolution.")
    _format_option(asset_variant, "json")
    asset_variant.set_defaults(handler=_handle_assets)

    resources = commands.add_parser("resources", help="Inspect indexed project resources.")
    resource_commands = resources.add_subparsers(dest="resources_action", required=True)
    resource_list = resource_commands.add_parser("list", help="List resources from the project index and editor model.")
    resource_list.add_argument("--project", required=True)
    resource_list.add_argument("--kind", choices=(
        "object-type", "family", "layout", "event-sheet", "timeline",
        "flowchart", "3d-model", "palette", "tilemap-brush",
        "script", "sound", "music", "video", "font", "icon", "file", "asset",
    ))
    resource_list.add_argument("--search")
    _format_option(resource_list)
    resource_list.set_defaults(handler=_handle_resources)

    platforms = commands.add_parser("platforms", help="List supported target profiles.")
    _format_option(platforms)
    platforms.set_defaults(handler=_handle_platforms)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a CLI command, or preserve the historic GUI launch when no args are given."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        return _launch_gui()

    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.command == "gui":
        return _launch_gui()

    try:
        return int(args.handler(args) or 0)
    except (AddonRegistryError, OSError, ValueError, KeyError) as exc:
        print(f"[impossible] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
