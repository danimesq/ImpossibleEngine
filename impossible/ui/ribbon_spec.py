"""Declarative ImpossibleEngine ribbon specification.

Adapted from RibbonFM GTK3 ribbon design under Apache-2.0.
RibbonFM: https://github.com/ysnx64523/Ribbon-File-Manager
"""

from __future__ import annotations


def _btn(id_, label, icon, action, *, large=True, check=False):
    return {"kind": "button", "id": id_, "label_key": label, "icon": icon,
            "action": action, "large": large, "check": check}


def _group(label, buttons, large=False, columns=0):
    return {"kind": "group", "label_key": label, "buttons": buttons,
            "large": large, "columns": columns}


TABS = [
    {"id": "home", "label_key": "Home", "groups": [
        _group("Project", [
            _btn("open", "Open", "document-open-symbolic", "open_project"),
            _btn("save", "Save", "document-save-symbolic", "save_project"),
            _btn("new", "New", "document-new-symbolic", "new_project"),
        ]),
        _group("History", [
            _btn("undo", "Undo", "edit-undo-symbolic", "undo", large=False),
            _btn("redo", "Redo", "edit-redo-symbolic", "redo", large=False),
        ], columns=1),
        _group("Event Sheet", [
            _btn("event", "Add event", "list-add-symbolic", "add_event"),
            _btn("condition", "Condition", "emblem-ok-symbolic", "add_condition", large=False),
            _btn("action", "Action", "system-run-symbolic", "add_action", large=False),
        ], columns=1),
        _group("Build", [
            _btn("validate", "Validate", "emblem-default-symbolic", "validate_project"),
            _btn("compile", "Compile logic", "applications-engineering-symbolic", "compile_logic"),
            _btn("preview", "Preview", "media-playback-start-symbolic", "run_project"),
        ]),
    ]},
    {"id": "view", "label_key": "View", "groups": [
        _group("Workspace", [
            _btn("events", "Event Sheets", "view-list-symbolic", "show:events", large=False),
            _btn("layouts", "Layouts", "view-grid-symbolic", "show:layouts", large=False),
            _btn("objects", "Objects", "applications-engineering-symbolic", "show:objects", large=False),
            _btn("assets", "Assets", "folder-symbolic", "show:assets", large=False),
            _btn("platforms", "Platforms", "computer-symbolic", "show:platforms", large=False),
        ], columns=3),
        _group("Panels", [
            _btn("sidebar", "Navigation", "view-sidebar-symbolic", "toggle:sidebar", large=False, check=True),
            _btn("ribbon", "Ribbon", "view-more-symbolic", "toggle:ribbon", large=False, check=True),
        ], columns=1),
    ]},
    {"id": "events", "label_key": "Events", "groups": [
        _group("Insert", [
            _btn("event", "Add event", "list-add-symbolic", "add_event"),
            _btn("condition", "Add condition", "emblem-ok-symbolic", "add_condition", large=False),
            _btn("action", "Add action", "system-run-symbolic", "add_action", large=False),
            _btn("comment", "Add comment", "comment-symbolic", "add_comment", large=False),
        ], columns=1),
        _group("Event state", [
            _btn("enable", "Enable/disable", "emblem-ok-symbolic", "toggle:event_enabled", large=False, check=True),
        ]),
    ]},
    {"id": "project", "label_key": "Project", "groups": [
        _group("Project", [
            _btn("open", "Open project", "document-open-symbolic", "open_project"),
            _btn("save", "Save project", "document-save-symbolic", "save_project"),
        ]),
        _group("Targets", [
            _btn("platforms", "Platforms", "computer-symbolic", "show:platforms", large=False),
            _btn("assets", "Assets", "folder-symbolic", "show:assets", large=False),
        ], columns=1),
    ]},
]

BACKSTAGE_ITEMS = [
    {"label": "New project", "action": "new_project"},
    {"label": "Open project…", "action": "open_project"},
    {"label": "Save project", "action": "save_project"},
    {"separator": True},
    {"label": "Validate project", "action": "validate_project"},
    {"label": "Compile logic", "action": "compile_logic"},
    {"separator": True},
    {"label": "About ImpossibleEngine", "action": "about"},
    {"label": "Close", "action": "close"},
]

QUICK_ACCESS = [
    {"label": "Open project", "icon": "document-open-symbolic", "action": "open_project"},
    {"label": "Save project", "icon": "document-save-symbolic", "action": "save_project"},
    {"label": "Undo", "icon": "edit-undo-symbolic", "action": "undo"},
    {"label": "Redo", "icon": "edit-redo-symbolic", "action": "redo"},
]
