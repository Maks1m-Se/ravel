"""Run with: python -m experiments.workbook.app"""

from copy import deepcopy
import json
from pathlib import Path

from nicegui import app, ui

from . import config as model


CSS = Path(__file__).with_name("workbook.css").read_text(encoding="utf-8")
app.add_static_files("/workbook-icons", Path(__file__).with_name("icons"))


def action_icon(name):
    ui.element("img").props(f'src=/workbook-icons/{name}.svg alt="" aria-hidden=true').classes("action-icon")


def display_number(value):
    return str(value).removesuffix(".0")


def context_help(title, text):
    """One explanation, available by hover, focus, or a pinned click/tap."""
    with ui.element("div").classes("context-help") as root:
        button = ui.button("?", color=None).props(f'flat dense no-caps aria-label="{title} help" aria-expanded=false')
        note = ui.label(text).classes("help-content").props('role=note')
        button.props(f'aria-describedby={note.html_id} aria-controls={note.html_id}')
        button.on("click", js_handler='''e => {
            const root = e.currentTarget.parentElement;
            const open = root.dataset.open !== 'true';
            root.dataset.open = String(open);
            root.dataset.dismissed = String(!open);
            e.currentTarget.setAttribute('aria-expanded', String(open));
        }''')
        root.on("keydown.escape", js_handler='''e => {
            e.currentTarget.dataset.open = 'false';
            e.currentTarget.dataset.dismissed = 'true';
            e.currentTarget.querySelector('button').setAttribute('aria-expanded', 'false');
        }''')
        for event in ("mouseenter", "focusin"):
            root.on(event, js_handler="e => { e.currentTarget.dataset.dismissed = 'false'; }")


def chrome(theme="dark"):
    ui.add_css(CSS)
    dark = ui.dark_mode(theme != "light")
    with ui.element("header").classes("toolbar") as toolbar:
        ui.label("R").classes("mark")
        ui.label("Ravel").classes("brand-name")
        ui.label("Prototype").classes("muted edition")
        theme_choice = ui.select(["Light", "Dark"], value="Light" if theme == "light" else "Dark",
                                 label="Theme", on_change=lambda e: dark.set_value(e.value == "Dark")).props(
                                     "outlined dense options-dense").classes("theme-select")
    return toolbar, theme_choice


@ui.page("/")
def home(theme: str = "dark"):
    _, theme_choice = chrome(theme)
    with ui.element("main").classes("welcome"):
        ui.label("A place to define your data.").classes("hero")
        ui.label("Begin with explicit field settings or an invented sample. Both open the same workbook.").classes("intro")
        with ui.row().classes("entry-cards"):
            with ui.card().classes("entry-card"):
                ui.label("01 / EXPLICIT RULES").classes("eyebrow")
                ui.label("Start with a blank definition").classes("section-title")
                ui.label("Edit a numeric field with clearly marked defaults.")
                ui.button("Create from scratch", color=None, on_click=lambda: ui.navigate.to(f"/scratch?theme={theme_choice.value.lower()}")).classes("primary-action")
            with ui.card().classes("entry-card"):
                ui.label("02 / EXAMPLE ASSUMPTIONS").classes("eyebrow")
                ui.label("Start with something to inspect").classes("section-title")
                ui.label("Ten invented CSV rows and precomputed suggestions. No profiling runs.")
                ui.button("Start from a sample", color=None, on_click=lambda: ui.navigate.to(f"/sample?theme={theme_choice.value.lower()}")).classes("primary-action")
        ui.label("Evaluation only: fixed illustrations, no generated data. Save files use a provisional format.").classes("notice")


@ui.page("/{entry}")
def workbook(entry: str, theme: str = "dark"):
    if entry not in {"scratch", "sample"}:
        ui.navigate.to("/")
        return
    config = model.new_config(entry)
    client = ui.context.client
    selected = config["table"]["fields"][-1]["id"]
    view = "fields"
    controls = {}
    output_controls = {}
    view_buttons = {}
    error_messages = {}
    badges = {}
    drafts = {}
    toolbar, theme_choice = chrome(theme)

    def update_drafts():
        if not controls or not badges:
            return
        field = next(f for f in config["table"]["fields"] if f["id"] == selected)
        changed = []
        for key, control in controls.items():
            value = control.value
            if key == "name":
                value = value.strip()
            elif key in {"minimum", "maximum", "missing_percent"}:
                if key != "missing_percent" and controls["kind"].value == "text":
                    value = None
                else:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        pass
            different = value != field["settings"][key]
            drafts[key].set_visibility(different)
            changed.append(different)
            origin = field["origins"][key]
            badges[key].set_text({"default": "Default", "sample suggestion": "Sample", "user override": "Edited"}[origin])
            badges[key].props(f'data-origin="{origin}"')
        field_state.set_text("Unapplied field edits" if any(changed) else "Field applied")

    def report(text, error=False):
        status.set_text(text)
        status.classes(add="error" if error else "", remove="" if error else "error")

    def field_settings():
        def number(key, label):
            try:
                return float(controls[key].value)
            except (ValueError, TypeError):
                raise model.ValidationError({key: f"{label} needs a number. Correct it and apply again."}) from None

        kind = controls["kind"].value
        return dict(name=controls["name"].value.strip(), kind=kind,
                    minimum=number("minimum", "Minimum") if kind == "number" else None,
                    maximum=number("maximum", "Maximum") if kind == "number" else None,
                    missing_percent=number("missing_percent", "Missing percent"))

    def wire_error(key, control):
        control.without_auto_validation()
        with control.add_slot("error"):
            error_messages[key] = ui.label("").props("role=alert")

    def set_error(key, control, message):
        control.error = message
        # QField prefers error-message over its error slot; use the labelled slot.
        control.props(remove="error-message")
        error_messages[key].set_text(message or "")
        control.props(f'aria-invalid={str(bool(message)).lower()}')
        if message:
            control.props(f'aria-describedby={error_messages[key].html_id}')
        else:
            control.props(remove="aria-describedby")

    def clear_errors(group):
        for key, control in group.items():
            set_error(key, control, None)

    async def focus_controls(targets):
        # Cancel queued Quasar selector focus before moving to an edited field.
        for control in (theme_choice, controls.get("kind"), output_controls.get("mode")):
            if control is not None:
                control.run_method("blur")
        # Wait for Vue's render flush, then focus the first affected DOM input.
        await client.run_javascript(f'''
            await Vue.nextTick();
            const targets = {json.dumps([c.html_id for c in targets])}.map(id => getHtmlElement(id));
            const input = [...document.querySelectorAll('input, [role="combobox"]')]
                .find(node => targets.includes(node) || targets.some(root => root?.contains(node)));
            if (input) {{
                input.focus({{preventScroll: true}});
                (input.closest('.q-field') || input).scrollIntoView({{block: 'center', behavior: 'instant'}});
            }}
        ''')

    async def show_errors(exc, *, switching=False):
        all_controls = {**controls, **output_controls}
        for key, message in exc.issues.items():
            set_error(key, all_controls[key], message)
        if switching:
            field_notice.set_text("Field switch refused. Correct this field first.")
            field_notice.set_visibility(True)
        report(str(exc), True)
        await focus_controls([all_controls[key] for key in exc.issues])

    async def apply_field():
        nonlocal config
        clear_errors(controls)
        try:
            candidate = model.update_field(config, selected, field_settings())
        except model.ValidationError as exc:
            await show_errors(exc)
            return
        config = candidate
        field_notice.set_visibility(False)
        await definitions.refresh()
        update_drafts()
        report("Field applied.")

    def output_settings():
        try:
            return dict(mode=output_controls["mode"].value,
                        count=int(output_controls["count"].value))
        except (ValueError, TypeError):
            raise model.ValidationError({"count": "Row count must be a whole number from 1 to 1,000,000."}) from None

    def update_output():
        nonlocal config
        if "count" not in output_controls:
            return
        output_controls["count"].set_label("New rows" if output_controls["mode"].value == "new" else "Total rows")
        was_invalid = any(c.error for c in output_controls.values())
        clear_errors(output_controls)
        try:
            candidate = deepcopy(config)
            candidate["output"] = output_settings()
            config = model.validate(candidate)
            count_note.set_text(count_description())
            count_state.set_text("Applied counts")
            if was_invalid:
                report("Output settings corrected.")
        except model.ValidationError as exc:
            for key, message in exc.issues.items():
                set_error(key, output_controls[key], message)
            count_state.set_text("Invalid draft; counts unchanged")

    def count_description():
        c = model.counts(config)
        return f"Retained {c['retained']:,} + New {c['generated']:,} = Total {c['total']:,}"

    async def save():
        nonlocal config
        clear_errors({**controls, **output_controls})
        try:
            candidate = model.update_field(config, selected, field_settings(), output=output_settings())
            content = model.dumps(candidate)
        except model.ValidationError as exc:
            await show_errors(exc)
            return
        config = candidate
        field_notice.set_visibility(False)
        await definitions.refresh()
        update_drafts()
        count_note.set_text(count_description())
        count_state.set_text("Applied counts")
        ui.download.content(content, "ravel-workbook.json", "application/json")
        report("Configuration downloaded. No data generated.")

    async def reload_file(event):
        nonlocal config, selected
        try:
            candidate = model.loads(await event.file.read())
        except ValueError as exc:
            upload_status.set_text(str(exc) + " Current workbook preserved.")
            uploader.reset()
            return
        config = candidate
        selected = config["table"]["fields"][-1]["id"]
        upload_dialog.close()
        uploader.reset()
        await shell.refresh()
        report("Configuration reloaded.")

    def open_upload():
        upload_status.set_text("")
        upload_dialog.open()

    with ui.dialog() as upload_dialog, ui.card().classes("load-dialog"):
        ui.label("Reload configuration").classes("section-title")
        ui.label("Loading replaces the current workbook. Save your edits first.")
        ui.label("Accepts only ravel-workbook-experiment/1 JSON, up to 64 KiB.").classes("muted")
        uploader = ui.upload(label="Choose configuration JSON", auto_upload=True,
                             max_file_size=65536, on_upload=reload_file,
                             on_rejected=lambda: upload_status.set_text("Choose one JSON file up to 64 KiB.")).props("accept=.json")
        upload_status = ui.label("").props('role=alert').classes("error")
        ui.button("Cancel", color=None, on_click=upload_dialog.close).props("flat")

    with ui.element("div").classes("action-toolbar").props('role=toolbar aria-label="Workbook actions"'):
        with ui.link(target=f"/?theme={theme_choice.value.lower()}").classes("home-link") as home_link:
            action_icon("home")
            ui.label("Home")
        theme_choice.on_value_change(lambda e: home_link.props(f'href=/?theme={e.value.lower()}'))
        with ui.button(color=None, on_click=save).props('flat no-caps aria-label="Save configuration"'):
            action_icon("save")
            ui.label("Save")
        with ui.button(color=None, on_click=open_upload).props('flat no-caps aria-label="Reload configuration"'):
            action_icon("reload")
            ui.label("Reload")
        with ui.row().classes("label-help session-note"):
            ui.label("Session only · Download to keep").classes("muted")
            context_help("Configuration", "Save applies valid field edits and downloads provisional ravel-workbook-experiment/1 JSON. Failed Save keeps applied settings and drafts. Reload replaces the workbook only after validation. No automatic persistence.")
    status = ui.label("Ready").props('role=status aria-live=polite').classes("status-line")

    async def select_field(identifier):
        nonlocal config, selected
        clear_errors(controls)
        try:
            candidate = model.update_field(config, selected, field_settings())
        except model.ValidationError as exc:
            await show_errors(exc, switching=True)
            return
        config = candidate
        selected = identifier
        await properties.refresh()
        await definitions.refresh()
        await focus_controls([controls["name"]])
        report("Field selected.")

    def change_view(value):
        nonlocal view
        view = value
        for key, button in view_buttons.items():
            button.props(f'aria-pressed={str(key == view).lower()}')
            button.classes(add="active-view" if key == view else "",
                           remove="" if key == view else "active-view")
        center.refresh()

    @ui.refreshable
    def definitions():
        with ui.element("table").classes("definition-table"):
            with ui.element("thead"), ui.element("tr"):
                for heading in ("Field", "Type", "Settings", "Applied origin"):
                    with ui.element("th").props("scope=col"):
                        ui.label(heading)
            with ui.element("tbody"):
                for field in config["table"]["fields"]:
                    with ui.element("tr").classes("selected-row" if field["id"] == selected else ""):
                        with ui.element("td"):
                            ui.button(field["settings"]["name"], color=None, on_click=lambda _, i=field["id"]: select_field(i)).props(
                                f'flat no-caps aria-pressed={str(field["id"] == selected).lower()}').classes("field-button")
                        with ui.element("td"):
                            ui.label(field["settings"]["kind"]).classes("mono")
                        with ui.element("td").classes("applied-settings"):
                            settings = field["settings"]
                            summary = (f"{display_number(settings['minimum'])}–{display_number(settings['maximum'])}"
                                       if settings["kind"] == "number" else "Text")
                            ui.label(f"{summary} · {display_number(settings['missing_percent'])}% missing")
                        with ui.element("td"):
                            ui.label("Edited" if "user override" in field["origins"].values() else
                                     "Sample" if config["entry"] == "sample" else "Default").classes("source-tag")

    @ui.refreshable
    def center():
        if view == "fields":
            definitions()
        else:
            with ui.row().classes("preview-heading"):
                ui.label("Fixed preview — not generated").classes("preview-warning")
                context_help("Preview", "These invented rows and headers stay fixed when settings change. Scratch displays three illustrative values; sample displays the bundled ten-row CSV. No profiling or generation runs.")
            rows = model.source_rows() if config["entry"] == "sample" else [{"value": "25"}, {"value": "50"}, {"value": "75"}]
            with ui.element("div").classes("preview-scroll").props('tabindex=0 role=region aria-label="Fixed illustration table; use arrow keys to scroll"'):
                with ui.element("table").classes("preview-table"):
                    with ui.element("caption"):
                        ui.label("10 invented source rows" if config["entry"] == "sample" else "3 illustrative rows · No source")
                    with ui.element("thead"), ui.element("tr"):
                        for key in rows[0]:
                            with ui.element("th").props("scope=col"):
                                ui.label(key)
                    with ui.element("tbody"):
                        for row in rows:
                            with ui.element("tr"):
                                for value in row.values():
                                    with ui.element("td"):
                                        ui.label(value)

    @ui.refreshable
    def properties():
        nonlocal field_notice, field_state
        field = next(f for f in config["table"]["fields"] if f["id"] == selected)
        values = field["settings"]
        with ui.row().classes("pane-heading"):
            with ui.row().classes("label-help"):
                ui.label("Properties").classes("pane-title")
                context_help("Properties", "Badges describe applied settings: Default, precomputed Sample, or Edited. Draft marks an unapplied change. Apply or selecting another field applies valid edits; Save applies valid edits before download. Text fields have no numeric bounds.")
            ui.label(field["id"]).classes("section-title mono")
        field_state = ui.label("Field applied").classes("field-state").props('role=status')
        field_notice = ui.label("").props('role=alert').classes("error help")
        field_notice.set_visibility(False)
        controls.clear()
        badges.clear()
        drafts.clear()
        with ui.element("div").classes("property-fields"):
            for key, label in (("name", "Field name"), ("kind", "Type"), ("minimum", "Minimum"),
                               ("maximum", "Maximum"), ("missing_percent", "Missing %")):
                with ui.element("div").classes("setting-row").props(f'data-setting={key}'):
                    if key == "kind":
                        controls[key] = ui.select(["number", "text"], label=label, value=values[key]).props("outlined dense options-dense")
                    else:
                        controls[key] = ui.input(label, value=str(values[key]) if values[key] is not None else "").props("outlined dense")
                        controls[key].props("maxlength=40" if key == "name" else "inputmode=decimal")
                    with ui.row().classes("setting-state"):
                        badges[key] = ui.label("").classes("setting-origin")
                        drafts[key] = ui.label("Draft").classes("draft-mark")
                        drafts[key].set_visibility(False)
                    wire_error(key, controls[key])
        for key, control in controls.items():
            control.on_value_change(update_drafts)
            if key in {"minimum", "maximum"}:
                control.bind_enabled_from(controls["kind"], "value", backward=lambda v: v == "number")
        ui.button("Apply", color=None, on_click=apply_field).props('no-caps aria-label="Apply field"').classes("primary-action")
        with ui.element("details").classes("assumptions"):
            with ui.element("summary"):
                ui.label("Assumptions")
            ui.label("Sample suggestions are precomputed examples for individual fields, not fitted statistics. "
                     "Relationships between fields are not inferred. Changing settings does not regenerate "
                     "the fixed preview. Scratch starts from explicit defaults.")
        update_drafts()

    @ui.refreshable
    def shell():
        nonlocal count_note, count_state
        with ui.element("main").classes("workbook-grid"):
            with ui.element("nav").classes("navigator").props('aria-label="Workbook tables"'):
                ui.label("Workbook").classes("pane-title")
                ui.label("Tables / 1").classes("tree-heading muted")
                ui.button(config["table"]["name"], color=None, on_click=lambda: report("Table selected.")).props('flat no-caps aria-pressed=true').classes("table-button")
                ui.label("10 source rows" if config["entry"] == "sample" else "No source rows").classes("muted")
            with ui.column().classes("main-column"):
                with ui.element("section").classes("sheet"):
                    with ui.row().classes("sheet-heading"):
                        ui.label(config["table"]["name"]).classes("sheet-title")
                        ui.label("Precomputed sample" if config["entry"] == "sample" else "Defaults").classes("muted")
                    view_buttons.clear()
                    with ui.row().classes("view-bar"):
                        for key, text in (("fields", "Fields"), ("preview", "Preview")):
                            view_buttons[key] = ui.button(text, color=None, on_click=lambda _, k=key: change_view(k)).props(
                                f'flat no-caps aria-pressed={str(view == key).lower()}').classes("view-button active-view" if key == view else "view-button")
                            if key == "fields":
                                context_help("Fields", "Field count is fixed in this experiment. Select a field to edit. Settings summarizes applied values, never drafts. Sample assumptions are precomputed: text IDs, three material labels, length 9.8–12.2 and 0% missing. They are not fitted statistics. Scratch starts with one numeric field, range 0–100 and 0% missing.")
                    center()
                with ui.element("section").classes("output-panel"):
                    with ui.row().classes("output-controls"):
                        modes = {"new": "New rows"}
                        if config["entry"] == "sample":
                            modes["extend"] = "Extend to total"
                        output_controls.clear()
                        output_controls["mode"] = ui.select(modes, label="Output mode", value=config["output"]["mode"], on_change=update_output).props("outlined dense options-dense")
                        output_controls["count"] = ui.input("New rows" if config["output"]["mode"] == "new" else "Total rows", value=str(config["output"]["count"]), on_change=update_output).props("outlined dense inputmode=numeric")
                        for key, control in output_controls.items():
                            wire_error(key, control)
                        with ui.row().classes("label-help"):
                            ui.label("Counts only").classes("counts-only")
                            context_help("Counts", "New rows: 1,000 means 1,000 new and zero retained. Extend ten source rows to 1,000 total: 990 new plus ten retained. These are counts only; no rows are generated. Valid output edits apply immediately; invalid drafts leave applied counts unchanged.")
                    with ui.row().classes("count-strip"):
                        count_note = ui.label(count_description()).props('role=status aria-live=polite').classes("count-note")
                        count_state = ui.label("Applied counts").classes("count-state")
            with ui.element("aside").classes("properties").props('aria-label="Selected field settings"'):
                properties()
        ui.label("Provisional configuration · Local only · NiceGUI evaluation").classes("footer-note")

    count_note = None
    field_notice = None
    field_state = None
    count_state = None
    shell()


if __name__ == "__main__":
    ui.run(host="127.0.0.1", port=8080, title="Ravel | Workbook experiment",
           dark=True, reload=False, show=False, prod_js=True, on_air=False)
