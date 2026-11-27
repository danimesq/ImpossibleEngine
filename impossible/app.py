"""GTK 3 prototype GUI. Project semantics stay outside the UI toolkit."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from .model import PLATFORM_PROFILES, PROFILE_BY_ID, Event, EventSheet, Project, make_demo_project
from .storage import load_project, save_project

ROOT = Path(__file__).resolve().parent
UI_FILE = ROOT / "ui" / "main-window.ui"
CSS_FILE = ROOT / "ui" / "style.css"


def add_class(widget: Gtk.Widget, name: str) -> None:
    widget.get_style_context().add_class(name)


def label(text: str, css: Optional[str] = None, xalign: float = 0.0) -> Gtk.Label:
    result = Gtk.Label(label=text)
    result.set_xalign(xalign)
    if css:
        add_class(result, css)
    return result


def button(text: str, css: str = "secondary-action") -> Gtk.Button:
    result = Gtk.Button(label=text)
    add_class(result, css)
    return result


def card() -> Gtk.Box:
    result = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
    add_class(result, "card")
    return result


class ImpossibleWindow:
    def __init__(self, application: Gtk.Application) -> None:
        self.project = make_demo_project()
        self.project_path: Optional[Path] = None
        self.selected_event_index = 0
        self.selected_target = self.project.active_platform
        self.builder = Gtk.Builder.new_from_file(str(UI_FILE))
        self.window = self.builder.get_object("main_window")
        self.window.set_application(application)
        self.stack = self.builder.get_object("workspace_stack")
        self.project_name_label = self.builder.get_object("project_name_label")
        self._install_css()
        self._install_header_actions()
        self._build_pages()
        self._connect_navigation()
        self.project_name_label.set_text(self.project.name)
        self.show_page("events")

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_path(str(CSS_FILE))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _install_header_actions(self) -> None:
        header = self.builder.get_object("header_bar")
        self.status_label = label("Impossible project", "muted")
        header.pack_end(self.status_label)
        open_button = Gtk.Button.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        open_button.set_tooltip_text("Open an Impossible project (.ieproj or .json)")
        open_button.connect("clicked", self.on_open_project)
        header.pack_end(open_button)
        save_button = Gtk.Button.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        save_button.set_tooltip_text("Save Impossible project")
        save_button.connect("clicked", self.on_save_project)
        header.pack_end(save_button)

    def _connect_navigation(self) -> None:
        mapping = {"nav_events": "events", "nav_layouts": "layouts", "nav_objects": "objects", "nav_assets": "assets", "nav_platforms": "platforms"}
        self.nav_buttons = {}
        for widget_id, page_name in mapping.items():
            item = self.builder.get_object(widget_id)
            item.connect("clicked", lambda _button, name=page_name: self.show_page(name))
            self.nav_buttons[page_name] = item

    def _build_pages(self) -> None:
        self.events_page = self._build_events_page()
        self.layouts_page = self._build_layouts_page()
        self.objects_page = self._build_objects_page()
        self.assets_page = self._build_assets_page()
        self.platforms_page = self._build_platforms_page()
        self.stack.add_titled(self.events_page, "events", "Event Sheets")
        self.stack.add_titled(self.layouts_page, "layouts", "Layouts")
        self.stack.add_titled(self.objects_page, "objects", "Objects")
        self.stack.add_titled(self.assets_page, "assets", "Assets")
        self.stack.add_titled(self.platforms_page, "platforms", "Platform Variants")

    def show_page(self, name: str) -> None:
        self.stack.set_visible_child_name(name)
        for page_name, item in self.nav_buttons.items():
            context = item.get_style_context()
            context.add_class("active") if page_name == name else context.remove_class("active")

    def _page_shell(self, title: str, subtitle: str) -> tuple[Gtk.Box, Gtk.Box]:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        add_class(page, "page")
        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        heading.pack_start(label(title, "page-title"), False, False, 0)
        heading.pack_start(label(subtitle, "page-subtitle"), False, False, 0)
        page.pack_start(heading, False, False, 0)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(18)
        content.set_vexpand(True)
        page.pack_start(content, True, True, 0)
        return page, content

    def _build_events_page(self) -> Gtk.Widget:
        page, content = self._page_shell(
            "Event Sheets",
            "Describe game logic as readable conditions and actions, independent of the runtime engine.",
        )
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_event = button("+ Add event", "primary-action")
        add_condition = button("+ Condition")
        add_action = button("+ Action")
        for item in (add_event, add_condition, add_action):
            toolbar.pack_start(item, False, False, 0)
        toolbar.pack_end(label("LOGIC  /  GAMEPLAY", "eyebrow"), False, False, 0)
        content.pack_start(toolbar, False, False, 0)
        self.events_scroller = Gtk.ScrolledWindow()
        self.events_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.events_scroller.set_vexpand(True)
        self.events_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.events_container.set_margin_end(8)
        self.events_scroller.add(self.events_container)
        content.pack_start(self.events_scroller, True, True, 0)
        add_event.connect("clicked", self.on_add_event)
        add_condition.connect("clicked", self.on_add_condition)
        add_action.connect("clicked", self.on_add_action)
        self._render_events()
        return page

    def _render_events(self) -> None:
        for child in self.events_container.get_children():
            self.events_container.remove(child)
        sheet = self.project.event_sheets[0] if self.project.event_sheets else None
        if sheet is None:
            self.events_container.pack_start(label("No event sheet yet. Add an event to begin.", "muted"), False, False, 0)
            self.events_container.show_all()
            return
        for index, event in enumerate(sheet.events):
            panel = card()
            heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            heading.pack_start(label(f"{index + 1:02d}", "event-index"), False, False, 0)
            heading.pack_start(label(event.name, "card-title"), True, True, 0)
            heading.pack_end(label("ENABLED" if event.enabled else "DISABLED", "pill"), False, False, 0)
            panel.pack_start(heading, False, False, 0)
            columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            conditions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            conditions.set_hexpand(True)
            actions.set_hexpand(True)
            conditions.pack_start(label("CONDITIONS", "eyebrow"), False, False, 2)
            actions.pack_start(label("ACTIONS", "eyebrow"), False, False, 2)
            for item in event.conditions:
                conditions.pack_start(label("◇  " + item, "condition-row"), False, False, 0)
            for item in event.actions:
                actions.pack_start(label("↳  " + item, "action-row"), False, False, 0)
            columns.pack_start(conditions, True, True, 0)
            columns.pack_start(actions, True, True, 0)
            panel.pack_start(columns, False, False, 0)
            choose = button("Select event")
            choose.connect("clicked", self._select_event, index)
            panel.pack_start(choose, False, False, 0)
            self.events_container.pack_start(panel, False, False, 0)
        self.events_container.show_all()

    def _select_event(self, _button: Gtk.Button, index: int) -> None:
        self.selected_event_index = index
        self.status_label.set_text(f"Selected event {index + 1}")

    def _active_event(self) -> Optional[Event]:
        if not self.project.event_sheets or not self.project.event_sheets[0].events:
            return None
        events = self.project.event_sheets[0].events
        return events[min(self.selected_event_index, len(events) - 1)]

    def _text_dialog(self, title: str, prompt: str, initial: str) -> Optional[str]:
        dialog = Gtk.Dialog(title=title, transient_for=self.window, modal=True)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(8)
        area.set_margin_top(12)
        area.set_margin_bottom(12)
        area.set_margin_start(12)
        area.set_margin_end(12)
        area.pack_start(label(prompt, "field-label"), False, False, 0)
        entry = Gtk.Entry()
        entry.set_text(initial)
        entry.set_activates_default(True)
        dialog.set_default_response(Gtk.ResponseType.OK)
        area.pack_start(entry, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        result = entry.get_text().strip() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        return result or None

    def on_add_event(self, _button: Gtk.Button) -> None:
        name = self._text_dialog("Add event", "Event name", "New event")
        if not name:
            return
        if not self.project.event_sheets:
            self.project.event_sheets.append(EventSheet("sheet-main", "Gameplay", []))
        events = self.project.event_sheets[0].events
        events.append(Event(f"event-{len(events) + 1}", name))
        self.selected_event_index = len(events) - 1
        self._render_events()

    def on_add_condition(self, _button: Gtk.Button) -> None:
        event = self._active_event()
        if event is None:
            self.on_add_event(_button)
            event = self._active_event()
        if event:
            value = self._text_dialog("Add condition", "Condition expression", "Keyboard key is pressed")
            if value:
                event.conditions.append(value)
                self._render_events()

    def on_add_action(self, _button: Gtk.Button) -> None:
        event = self._active_event()
        if event is None:
            self.on_add_event(_button)
            event = self._active_event()
        if event:
            value = self._text_dialog("Add action", "Action expression", "Move Player")
            if value:
                event.actions.append(value)
                self._render_events()

    def _build_layouts_page(self) -> Gtk.Widget:
        """Show source-preserved scenes and their placed object instances."""
        page, content = self._page_shell(
            "Layouts",
            "Source-ordered scenes, Event Sheet links, includes and placed instances.",
        )
        self.layouts_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.add(self.layouts_list)
        content.pack_start(scroll, True, True, 0)
        self._render_layouts()
        return page

    def _render_layouts(self) -> None:
        for child in self.layouts_list.get_children():
            self.layouts_list.remove(child)

        sheets_by_id = {sheet.id: sheet for sheet in self.project.event_sheets}
        objects_by_id = {obj.id: obj for obj in self.project.objects}

        for index, layout in enumerate(self.project.layouts, start=1):
            panel = card()
            heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            heading.pack_start(label(f"{index:02d}", "event-index"), False, False, 0)
            heading.pack_start(label(layout.name, "card-title"), True, True, 0)
            heading.pack_end(label(f"{len(layout.instances)} INSTANCES", "pill"), False, False, 0)
            panel.pack_start(heading, False, False, 0)

            sheet = sheets_by_id.get(layout.event_sheet_id)
            sheet_name = sheet.name if sheet else f"Missing Event Sheet: {layout.event_sheet_id}"
            panel.pack_start(label(f"EVENT SHEET  {sheet_name}", "muted"), False, False, 0)

            include_names = [
                sheets_by_id[item].name if item in sheets_by_id else item
                for item in layout.includes
            ]
            panel.pack_start(
                label("INCLUDES  " + (", ".join(include_names) if include_names else "None"), "muted"),
                False, False, 0,
            )

            for instance in layout.instances:
                obj = objects_by_id.get(instance.object_id)
                object_name = obj.name if obj else instance.object_id
                x, y = instance.position
                width, height = instance.size
                details = (
                    f"UID {instance.source_uid}  ·  "
                    f"({x:g}, {y:g})  ·  {width:g} × {height:g}"
                )
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row.pack_start(label(object_name, "condition-row"), True, True, 0)
                row.pack_end(label(details, "muted"), False, False, 0)
                panel.pack_start(row, False, False, 0)

                if instance.variables:
                    panel.pack_start(
                        label("Variables  " + json.dumps(instance.variables, ensure_ascii=False), "muted"),
                        False, False, 0,
                    )
                if instance.behaviors:
                    panel.pack_start(
                        label("Behaviors  " + ", ".join(instance.behaviors.keys()), "muted"),
                        False, False, 0,
                    )

            self.layouts_list.pack_start(panel, False, False, 0)

        if not self.project.layouts:
            self.layouts_list.pack_start(
                label("This project has no imported layouts yet.", "muted"),
                False, False, 0,
            )
        self.layouts_list.show_all()

    def _build_objects_page(self) -> Gtk.Widget:
        page, content = self._page_shell("Objects", "Stable logical objects with platform-specific properties.")
        self.objects_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.pack_start(self.objects_list, False, False, 0)
        self._render_objects()
        return page

    def _render_objects(self) -> None:
        for child in self.objects_list.get_children():
            self.objects_list.remove(child)
        for obj in self.project.objects:
            panel = card()
            panel.pack_start(label(obj.name, "card-title"), False, False, 0)
            panel.pack_start(label(f"ID  {obj.id}    ·    ASSET  {obj.asset_id}", "muted"), False, False, 0)
            panel.pack_start(label("Base: " + json.dumps(obj.base_properties, ensure_ascii=False), "muted"), False, False, 0)
            overrides = "  ·  ".join(
                f"{PROFILE_BY_ID[key].name if key in PROFILE_BY_ID else key}: {value}"
                for key, value in obj.platform_overrides.items()
            ) or "No platform overrides yet"
            panel.pack_start(label("Overrides: " + overrides, "muted"), False, False, 0)
            self.objects_list.pack_start(panel, False, False, 0)
        self.objects_list.show_all()

    def _build_assets_page(self) -> Gtk.Widget:
        page, content = self._page_shell("Assets", "One logical asset can resolve to different source files per target.")
        self.assets_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.pack_start(self.assets_list, False, False, 0)
        self._render_assets()
        return page

    def _render_assets(self) -> None:
        for child in self.assets_list.get_children():
            self.assets_list.remove(child)
        for asset in self.project.assets:
            panel = card()
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.pack_start(label(asset.name, "card-title"), True, True, 0)
            row.pack_end(label(asset.kind.upper(), "pill"), False, False, 0)
            panel.pack_start(row, False, False, 0)
            panel.pack_start(label("Base source: " + asset.source, "muted"), False, False, 0)
            variants = ", ".join(f"{key}: {value}" for key, value in asset.variants.items()) or "No variants"
            panel.pack_start(label("Variants: " + variants, "muted"), False, False, 0)
            if asset.notes:
                panel.pack_start(label(asset.notes, "muted"), False, False, 0)
            self.assets_list.pack_start(panel, False, False, 0)
        self.assets_list.show_all()

    def _build_platforms_page(self) -> Gtk.Widget:
        page, content = self._page_shell(
            "Platform Variants",
            "Author once; resolve platform-specific sprites, meshes and object properties at build time.",
        )
        profiles = Gtk.FlowBox()
        profiles.set_selection_mode(Gtk.SelectionMode.NONE)
        profiles.set_max_children_per_line(3)
        profiles.set_column_spacing(10)
        profiles.set_row_spacing(10)
        for profile in PLATFORM_PROFILES:
            panel = card()
            add_class(panel, "target-card")
            panel.pack_start(label(profile.name, "target-name"), False, False, 0)
            panel.pack_start(label(profile.dimension + "  ·  " + profile.renderer, "target-meta"), False, False, 0)
            panel.pack_start(label(profile.budget_hint, "muted"), False, False, 0)
            profiles.add(panel)
        content.pack_start(profiles, False, False, 0)

        editor = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        editor.set_vexpand(True)
        left, right = card(), card()
        left.set_hexpand(True)
        right.set_hexpand(True)
        editor.pack_start(left, True, True, 0)
        editor.pack_start(right, True, True, 0)
        content.pack_start(editor, True, True, 0)

        left.pack_start(label("ASSET VARIANT", "eyebrow"), False, False, 0)
        left.pack_start(label("Set an explicit source path for one logical asset and target.", "muted"), False, False, 0)
        self.target_combo = Gtk.ComboBoxText()
        for profile in PLATFORM_PROFILES:
            self.target_combo.append(profile.id, profile.name)
        self.target_combo.set_active_id(self.selected_target)
        left.pack_start(label("Target profile", "field-label"), False, False, 0)
        left.pack_start(self.target_combo, False, False, 0)

        self.asset_combo = Gtk.ComboBoxText()
        for asset in self.project.assets:
            self.asset_combo.append(asset.id, asset.name)
        if self.project.assets:
            self.asset_combo.set_active(0)
        left.pack_start(label("Logical asset", "field-label"), False, False, 0)
        left.pack_start(self.asset_combo, False, False, 0)
        left.pack_start(label("Variant source path", "field-label"), False, False, 0)
        self.variant_entry = Gtk.Entry()
        left.pack_start(self.variant_entry, False, False, 0)
        save_asset = button("Save asset variant", "primary-action")
        left.pack_start(save_asset, False, False, 0)
        self.variant_hint = label("", "muted")
        self.variant_hint.set_line_wrap(True)
        left.pack_start(self.variant_hint, False, False, 0)

        right.pack_start(label("OBJECT OVERRIDES", "eyebrow"), False, False, 0)
        right.pack_start(label("Sparse JSON overrides are merged over base object properties.", "muted"), False, False, 0)
        self.object_combo = Gtk.ComboBoxText()
        for obj in self.project.objects:
            self.object_combo.append(obj.id, obj.name)
        if self.project.objects:
            self.object_combo.set_active(0)
        right.pack_start(label("Logical object", "field-label"), False, False, 0)
        right.pack_start(self.object_combo, False, False, 0)
        self.override_view = Gtk.TextView()
        self.override_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.override_view.set_size_request(-1, 125)
        self.override_view.get_buffer().set_text("{}")
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(125)
        scroll.add(self.override_view)
        right.pack_start(label("Target override JSON", "field-label"), False, False, 0)
        right.pack_start(scroll, True, True, 0)
        save_object = button("Save object overrides", "primary-action")
        right.pack_start(save_object, False, False, 0)
        self.override_hint = label("Only changed values belong in this object.", "muted")
        right.pack_start(self.override_hint, False, False, 0)

        self.target_combo.connect("changed", self.on_target_changed)
        self.asset_combo.connect("changed", self._load_asset_variant)
        self.object_combo.connect("changed", self._load_object_override)
        save_asset.connect("clicked", self.on_save_asset_variant)
        save_object.connect("clicked", self.on_save_object_override)
        self._load_asset_variant()
        self._load_object_override()
        return page

    def on_target_changed(self, combo: Gtk.ComboBoxText) -> None:
        self.selected_target = combo.get_active_id() or "pc-modern"
        self.project.active_platform = self.selected_target
        self._load_asset_variant()
        self._load_object_override()

    def _selected_asset(self):
        asset_id = self.asset_combo.get_active_id() if hasattr(self, "asset_combo") else None
        return next((item for item in self.project.assets if item.id == asset_id), None)

    def _selected_object(self):
        object_id = self.object_combo.get_active_id() if hasattr(self, "object_combo") else None
        return next((item for item in self.project.objects if item.id == object_id), None)

    def _load_asset_variant(self, *_args) -> None:
        if not hasattr(self, "variant_entry"):
            return
        asset = self._selected_asset()
        if not asset:
            self.variant_entry.set_text("")
            return
        value = asset.variants.get(self.selected_target, "")
        self.variant_entry.set_text(value)
        profile = PROFILE_BY_ID[self.selected_target]
        detail = "Explicit variant → " + value if value else "Fallback → " + asset.source_for(self.selected_target)
        self.variant_hint.set_text(profile.name + ": " + detail)

    def on_save_asset_variant(self, _button: Gtk.Button) -> None:
        asset = self._selected_asset()
        if not asset:
            return
        path = self.variant_entry.get_text().strip()
        if path:
            asset.variants[self.selected_target] = path
        else:
            asset.variants.pop(self.selected_target, None)
        self._load_asset_variant()
        self._render_assets()
        self.status_label.set_text("Asset variant updated")

    def _load_object_override(self, *_args) -> None:
        if not hasattr(self, "override_view"):
            return
        obj = self._selected_object()
        data = obj.platform_overrides.get(self.selected_target, {}) if obj else {}
        self.override_view.get_buffer().set_text(json.dumps(data, indent=2, ensure_ascii=False))

    def on_save_object_override(self, _button: Gtk.Button) -> None:
        obj = self._selected_object()
        if not obj:
            return
        buffer = self.override_view.get_buffer()
        start, end = buffer.get_bounds()
        try:
            value = json.loads(buffer.get_text(start, end, True))
            if not isinstance(value, dict):
                raise ValueError("Overrides must be a JSON object.")
        except (json.JSONDecodeError, ValueError) as error:
            self._show_error("Invalid object overrides", str(error))
            return
        if value:
            obj.platform_overrides[self.selected_target] = value
        else:
            obj.platform_overrides.pop(self.selected_target, None)
        self._render_objects()
        self.status_label.set_text("Object overrides updated")

    def _show_error(self, title: str, message: str) -> None:
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE, text=title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_open_project(self, _button: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(title="Open Impossible project", parent=self.window,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK)
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Impossible project (*.ieproj, *.json)")
        file_filter.add_pattern("*.ieproj")
        file_filter.add_pattern("*.json")
        dialog.add_filter(file_filter)
        response = dialog.run()
        filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not filename:
            return
        try:
            self.project = load_project(filename)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self._show_error("Could not open project", str(error))
            return
        self.project_path = Path(filename)
        self._refresh_all_pages()
        self.status_label.set_text("Opened " + self.project_path.name)

    def on_save_project(self, _button: Gtk.Button) -> None:
        if self.project_path is None:
            dialog = Gtk.FileChooserDialog(title="Save Impossible project", parent=self.window,
                                           action=Gtk.FileChooserAction.SAVE)
            dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
            dialog.set_do_overwrite_confirmation(True)
            dialog.set_current_name("impossible-project.ieproj")
            response = dialog.run()
            filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
            dialog.destroy()
            if not filename:
                return
            self.project_path = Path(filename)
        try:
            save_project(self.project, self.project_path)
        except OSError as error:
            self._show_error("Could not save project", str(error))
            return
        self.project_name_label.set_text(self.project.name)
        self.status_label.set_text("Saved " + self.project_path.name)

    def _refresh_all_pages(self) -> None:
        self.selected_target = self.project.active_platform
        self.project_name_label.set_text(self.project.name)
        self._render_events()
        self._render_layouts()
        self._render_objects()
        self._render_assets()
        self.stack.remove(self.platforms_page)
        self.platforms_page = self._build_platforms_page()
        self.stack.add_titled(self.platforms_page, "platforms", "Platform Variants")
        self.stack.show_all()


class ImpossibleApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.github.danimesq.ImpossibleEngine")

    def do_activate(self) -> None:
        if not hasattr(self, "main_window"):
            self.main_window = ImpossibleWindow(self)
        self.main_window.window.show_all()
        self.main_window.window.present()


def main() -> int:
    return ImpossibleApplication().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
