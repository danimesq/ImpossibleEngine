"""Toolkit-independent editing operations shared by the GUI and CLI.

These functions are the editor's command surface. UI adapters should collect input,
call an operation here, and then refresh their presentation.
"""
from __future__ import annotations

from typing import Any

from .model import (
    PROFILE_BY_ID,
    Event,
    EventSheet,
    Project,
)


def _required_text(value: str, label: str) -> str:
    result = value.strip()
    if not result:
        raise ValueError(f"{label} cannot be empty.")
    return result


def _unique_id(prefix: str, existing: set[str]) -> str:
    index = 1
    while f"{prefix}-{index}" in existing:
        index += 1
    return f"{prefix}-{index}"


def get_event_sheet(project: Project, sheet_id: str | None = None, *, create: bool = False) -> EventSheet:
    """Return a selected sheet, optionally creating the GUI's default Gameplay sheet."""
    if sheet_id:
        for sheet in project.event_sheets:
            if sheet.id == sheet_id:
                return sheet
        raise KeyError(f"Unknown Event Sheet ID: {sheet_id}")

    if project.event_sheets:
        return project.event_sheets[0]
    if not create:
        raise ValueError("The project has no Event Sheets.")
    sheet = EventSheet("sheet-main", "Gameplay", [])
    project.event_sheets.append(sheet)
    return sheet


def find_event(project: Project, event_id: str, sheet_id: str | None = None) -> Event:
    """Find an event by stable ID, rejecting ambiguous IDs across sheets."""
    matches: list[Event] = []
    sheets = project.event_sheets
    if sheet_id:
        sheets = [get_event_sheet(project, sheet_id)]
    for sheet in sheets:
        matches.extend(event for event in sheet.events if event.id == event_id)
    if not matches:
        raise KeyError(f"Unknown Event ID: {event_id}")
    if len(matches) > 1:
        raise ValueError(f"Event ID {event_id!r} exists in multiple sheets; specify --sheet.")
    return matches[0]


def add_event(project: Project, name: str, sheet_id: str | None = None) -> Event:
    """Create an event in the requested sheet, or the first/default sheet."""
    name = _required_text(name, "Event name")
    sheet = get_event_sheet(project, sheet_id, create=True)
    existing = {event.id for event in sheet.events}
    event = Event(_unique_id("event", existing), name)
    sheet.events.append(event)
    return event


def add_event_condition(
    project: Project, event_id: str, expression: str, sheet_id: str | None = None
) -> Event:
    event = find_event(project, event_id, sheet_id)
    event.conditions.append(_required_text(expression, "Condition"))
    return event


def add_event_action(
    project: Project, event_id: str, expression: str, sheet_id: str | None = None
) -> Event:
    event = find_event(project, event_id, sheet_id)
    event.actions.append(_required_text(expression, "Action"))
    return event


def set_event_enabled(
    project: Project, event_id: str, enabled: bool, sheet_id: str | None = None
) -> Event:
    event = find_event(project, event_id, sheet_id)
    event.enabled = bool(enabled)
    return event


def remove_event(project: Project, event_id: str, sheet_id: str | None = None) -> Event:
    event = find_event(project, event_id, sheet_id)
    for sheet in project.event_sheets:
        if sheet_id and sheet.id != sheet_id:
            continue
        if event in sheet.events:
            sheet.events.remove(event)
            return event
    raise KeyError(f"Unknown Event ID: {event_id}")


def set_active_platform(project: Project, platform_id: str) -> None:
    if platform_id not in PROFILE_BY_ID:
        choices = ", ".join(PROFILE_BY_ID)
        raise ValueError(f"Unknown platform {platform_id!r}. Available: {choices}")
    project.active_platform = platform_id


def set_asset_variant(project: Project, asset_id: str, platform_id: str, path: str | None) -> None:
    if platform_id not in PROFILE_BY_ID:
        raise ValueError(f"Unknown platform ID: {platform_id}")
    asset = next((item for item in project.assets if item.id == asset_id), None)
    if asset is None:
        raise KeyError(f"Unknown asset ID: {asset_id}")
    value = path.strip() if path is not None else ""
    if value:
        asset.variants[platform_id] = value
    else:
        asset.variants.pop(platform_id, None)


def set_object_override(
    project: Project, object_id: str, platform_id: str, values: dict[str, Any]
) -> None:
    if platform_id not in PROFILE_BY_ID:
        raise ValueError(f"Unknown platform ID: {platform_id}")
    if not isinstance(values, dict):
        raise ValueError("Object overrides must be a JSON object.")
    obj = next((item for item in project.objects if item.id == object_id), None)
    if obj is None:
        raise KeyError(f"Unknown object ID: {object_id}")
    if values:
        obj.platform_overrides[platform_id] = values
    else:
        obj.platform_overrides.pop(platform_id, None)


def _canonical_addon_id(entry: dict[str, Any]) -> str:
    addon_id = str(entry.get("id", ""))
    kind = str(entry.get("type", entry.get("kind", "")))
    if addon_id and "." not in addon_id and kind:
        return f"{kind}.{addon_id.lower().replace(' ', '-')}"
    return addon_id


def _dependency_addon(registry: Any, requirement: str):
    """Resolve a requirement written as an add-on ID or provided capability."""
    try:
        return registry.get(requirement)
    except KeyError:
        providers = [
            registry.get(addon_id) for addon_id in registry.ids()
            if requirement in registry.get(addon_id).provides
        ]
        if not providers:
            raise ValueError(f"No installed catalogue add-on provides dependency {requirement!r}.")
        if len(providers) > 1:
            names = ", ".join(sorted(item.id for item in providers))
            raise ValueError(f"Dependency {requirement!r} has multiple providers: {names}.")
        return providers[0]


def add_project_addon(project: Project, addon_id: str, registry: Any) -> list[str]:
    """Add a built-in add-on and any missing catalogue dependencies to a project.

    This records project metadata only. It does not execute add-on code or claim
    that a specification-only descriptor has a runtime implementation.
    """
    registry.get(addon_id)  # Fail early with the registry's stable-ID diagnostic.
    active = {_canonical_addon_id(item) for item in project.used_addons}
    ordered: list[Any] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    available_capabilities: set[str] = set()
    for active_id in active:
        try:
            available_capabilities.update(registry.get(active_id).provides)
        except KeyError:
            # Preserve project entries from registries that are not currently loaded.
            continue

    def visit(current_id: str) -> None:
        if current_id in visited or current_id in active:
            return
        if current_id in visiting:
            raise ValueError(f"Cyclic add-on dependency detected at {current_id}.")
        visiting.add(current_id)
        addon = registry.get(current_id)
        for requirement in addon.requires:
            if requirement in available_capabilities:
                continue
            dependency = _dependency_addon(registry, requirement)
            visit(dependency.id)
            available_capabilities.update(dependency.provides)
        visiting.remove(current_id)
        visited.add(current_id)
        ordered.append(addon)

    visit(addon_id)
    for addon in ordered:
        project.used_addons.append({
            "type": addon.kind,
            "id": addon.id,
            "name": addon.name,
            "author": addon.raw.get("author", "Unknown"),
            "bundled": registry.origin(addon.id) == "builtin",
        })
    return [addon.id for addon in ordered]


def remove_project_addon(project: Project, addon_id: str, registry: Any) -> bool:
    """Remove a selected add-on, even if its third-party package is now missing."""
    active_ids = {_canonical_addon_id(item) for item in project.used_addons}
    if addon_id not in active_ids:
        return False

    try:
        target = registry.get(addon_id)
    except KeyError:
        target = None

    for other_id in sorted(active_ids - {addon_id}):
        try:
            other = registry.get(other_id)
        except KeyError:
            continue
        for requirement in other.requires:
            if requirement == addon_id or (
                target is not None and requirement in target.provides
            ):
                raise ValueError(
                    f"Cannot remove {addon_id}: {other_id} depends on it. "
                    f"Remove {other_id} first."
                )

    project.used_addons = [
        item for item in project.used_addons
        if _canonical_addon_id(item) != addon_id
    ]
    return True
