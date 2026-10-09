"""Run with: python -m experiments.workbook.app"""

from copy import deepcopy
import json
from pathlib import Path

from nicegui import ui

from . import config as model


CSS = Path(__file__).with_name("workbook.css").read_text(encoding="utf-8")


def chrome():
    ui.colors(primary="#9cdbc5")
    ui.add_css(CSS)
    with ui.element("header").classes("masthead"):
        ui.label("R").classes("mark")
        with ui.column().classes("brand"):
            ui.label("Ravel").classes("brand-name")
            ui.label("Compose the data you need.").classes("muted")
        ui.label("WORKBOOK / INTERACTION EXPERIMENT").classes("edition")
        ui.label("Local only").classes("local-badge")


@ui.page("/")
def home():
    chrome()
    with ui.element("main").classes("welcome"):
        ui.label("A place to define your data.").classes("hero")
        ui.label("Begin with explicit field settings or an invented sample. Both open the same workbook.").classes("intro")
        with ui.row().classes("entry-cards"):
            with ui.card().classes("entry-card"):
                ui.label("01 / EXPLICIT RULES").classes("eyebrow")
                ui.label("Start with a blank definition").classes("section-title")
                ui.label("Edit a numeric field with clearly marked defaults.")
                ui.button("Create from scratch", on_click=lambda: ui.navigate.to("/scratch")).props("text-color=dark")
            with ui.card().classes("entry-card"):
                ui.label("02 / EXAMPLE ASSUMPTIONS").classes("eyebrow")
                ui.label("Start with something to inspect").classes("section-title")
                ui.label("Ten invented CSV rows and precomputed suggestions. No profiling runs.")
                ui.button("Start from a sample", on_click=lambda: ui.navigate.to("/sample")).props("text-color=dark")
        ui.label("Evaluation only: fixed illustrations, no generated data. Save files use a provisional format.").classes("notice")


@ui.page("/{entry}")
def workbook(entry: str):
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
    chrome()

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
            field_notice.set_text("Field switch refused. Correct the highlighted settings, then select the field again.")
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
        await provenance.refresh()
        report("Field applied. The fixed illustration has not changed.")

    def output_settings():
        try:
            return dict(mode=output_controls["mode"].value,
                        count=int(output_controls["count"].value))
        except (ValueError, TypeError):
            raise model.ValidationError({"count": "Row count must be a whole number from 1 to 1,000,000."}) from None

    def update_output():
        nonlocal config
        was_invalid = any(c.error for c in output_controls.values())
        clear_errors(output_controls)
        try:
            candidate = deepcopy(config)
            candidate["output"] = output_settings()
            config = model.validate(candidate)
            count_note.set_text(count_description())
            count_note.classes(remove="error")
            if was_invalid:
                report("Output settings corrected.")
        except model.ValidationError as exc:
            for key, message in exc.issues.items():
                set_error(key, output_controls[key], message)
            count_note.set_text(str(exc))
            count_note.classes(add="error")

    def count_description():
        c = model.counts(config)
        if config["output"]["mode"] == "new":
            return f"{c['generated']:,} generated rows + 0 retained rows = {c['total']:,} output rows. Source rows are not appended."
        return f"{c['retained']:,} retained source rows + {c['generated']:,} generated rows = {c['total']:,} total rows."

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
        await provenance.refresh()
        count_note.set_text(count_description())
        count_note.classes(remove="error")
        ui.download.content(content, "ravel-workbook.json", "application/json")
        report("Configuration downloaded. Provisional format; no output data was generated.")

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
        report("Configuration reloaded, including setting origins and output counts.")

    def open_upload():
        upload_status.set_text("")
        upload_dialog.open()

    with ui.dialog() as upload_dialog, ui.card().classes("load-dialog"):
        ui.label("Reload experiment configuration").classes("section-title")
        ui.label("Loading replaces the current workbook. Save your edits first.")
        ui.label("Accepts only ravel-workbook-experiment/1 JSON, up to 64 KiB.").classes("muted")
        uploader = ui.upload(label="Choose configuration JSON", auto_upload=True,
                             max_file_size=65536, on_upload=reload_file,
                             on_rejected=lambda: upload_status.set_text("Choose one JSON file up to 64 KiB.")).props("accept=.json")
        upload_status = ui.label("").props('role=alert').classes("error")
        ui.button("Cancel", on_click=upload_dialog.close).props("flat")

    with ui.row().classes("toolbar"):
        ui.link("Workbook home", "/").classes("home-link")
        ui.label("Unsaved work stays in this page. Download before leaving.").classes("muted toolbar-note")
        ui.button("Save configuration", on_click=save).props("outline no-caps")
        ui.button("Reload configuration", on_click=open_upload).props("flat no-caps")
    status = ui.label("Provisional configuration / fixed illustrations / no generation").props('role=status aria-live=polite').classes("status-line")

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
        report("Field selected. Settings remain in the shared configuration.")

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
                for heading in ("Field / select to edit", "Type", "Settings source"):
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
                        with ui.element("td"):
                            ui.label("User override" if "user override" in field["origins"].values() else
                                     "Sample suggestion" if config["entry"] == "sample" else "Default").classes("source-tag")

    @ui.refreshable
    def center():
        if view == "fields":
            definitions()
            ui.label("Select a field to edit its settings. Field count is fixed in this experiment.").classes("muted panel-note")
            with ui.element("div").classes("assumption-note"):
                ui.label("A starting point, not a fitted model").classes("note-title")
                ui.label("Sample suggestions are precomputed examples: text IDs, three material labels, length range 9.8–12.2, and 0% missing. IDs are not fitted. Ten rows do not establish population properties or associations."
                         if config["entry"] == "sample" else
                         "Defaults define one numeric field with range 0–100 and 0% missing. Edit these explicit settings in the field panel.")
        else:
            ui.label("FIXED ILLUSTRATION — NOT GENERATED OUTPUT").classes("preview-warning")
            ui.label("Edits do not regenerate these rows or rename these headers. The illustration is independent of your settings.").classes("muted panel-note")
            rows = model.source_rows() if config["entry"] == "sample" else [{"value": "25"}, {"value": "50"}, {"value": "75"}]
            with ui.element("div").classes("preview-scroll").props('tabindex=0 role=region aria-label="Fixed illustration table; use arrow keys to scroll"'):
                with ui.element("table").classes("preview-table"):
                    with ui.element("caption"):
                        ui.label("Bundled invented CSV / 10 source rows" if config["entry"] == "sample" else "Three invented display values / no source rows")
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
    def provenance():
        field = next(f for f in config["table"]["fields"] if f["id"] == selected)
        with ui.element("div").classes("provenance"):
            ui.label("APPLIED SETTING ORIGINS").classes("eyebrow")
            for key, label in (("name", "Name"), ("kind", "Type"), ("minimum", "Minimum"),
                               ("maximum", "Maximum"), ("missing_percent", "Missing %")):
                if field["settings"]["kind"] == "text" and key in {"minimum", "maximum"}:
                    continue
                ui.label(f"{label}: {field['origins'][key]}")

    @ui.refreshable
    def properties():
        nonlocal field_notice
        field = next(f for f in config["table"]["fields"] if f["id"] == selected)
        values = field["settings"]
        ui.label("FIELD SETTINGS").classes("eyebrow")
        ui.label(field["id"]).classes("section-title mono")
        field_notice = ui.label("").props('role=alert').classes("error help")
        field_notice.set_visibility(False)
        controls.clear()
        controls["name"] = ui.input("Field name", value=values["name"]).props("outlined dense maxlength=40")
        controls["kind"] = ui.select(["number", "text"], label="Field type", value=values["kind"]).props("outlined dense")
        with ui.row().classes("bounds"):
            for key, label in (("minimum", "Minimum"), ("maximum", "Maximum")):
                controls[key] = ui.input(label, value=str(values[key] if values[key] is not None else 0)).props("outlined dense inputmode=decimal")
                controls[key].bind_visibility_from(controls["kind"], "value", backward=lambda v: v == "number")
        controls["missing_percent"] = ui.input("Missing percent", value=str(values["missing_percent"])).props("outlined dense inputmode=decimal")
        for key, control in controls.items():
            wire_error(key, control)
        ui.button("Apply field", on_click=apply_field).props("no-caps text-color=dark")
        ui.label("Apply commits these settings to the workbook. Save also applies valid edits.").classes("muted help")
        provenance()

    @ui.refreshable
    def shell():
        nonlocal count_note
        with ui.element("main").classes("workbook-grid"):
            with ui.element("nav").classes("navigator").props('aria-label="Workbook tables"'):
                ui.label("NAVIGATOR").classes("eyebrow")
                ui.label("Tables / 1").classes("muted")
                ui.button(config["table"]["name"], color=None, on_click=lambda: report("Table selected. Use Field definitions to choose a field.")).props('flat no-caps aria-pressed=true').classes("table-button")
                ui.label("10 source rows" if config["entry"] == "sample" else "No source rows").classes("muted")
                ui.label("Generic workbook").classes("navigator-foot")
            with ui.column().classes("main-column"):
                with ui.element("section").classes("sheet"):
                    with ui.row().classes("sheet-heading"):
                        with ui.column().classes("title-stack"):
                            ui.label("WORKBOOK / TABLE 01").classes("eyebrow")
                            ui.label(config["table"]["name"]).classes("sheet-title")
                        ui.label("From sample" if config["entry"] == "sample" else "From scratch").classes("route-tag")
                    view_buttons.clear()
                    with ui.row().classes("view-bar"):
                        for key, text in (("fields", "Field definitions"), ("preview", "Illustrative preview")):
                            view_buttons[key] = ui.button(text, color=None, on_click=lambda _, k=key: change_view(k)).props(
                                f'flat no-caps aria-pressed={str(view == key).lower()}').classes("view-button active-view" if key == view else "view-button")
                    center()
                with ui.element("section").classes("output-panel"):
                    ui.label("Output intent").classes("section-title")
                    ui.label("Count arithmetic only. This experiment does not generate rows.").classes("muted")
                    with ui.row().classes("output-controls"):
                        modes = {"new": "Generate new rows"}
                        if config["entry"] == "sample":
                            modes["extend"] = "Extend source to total"
                        output_controls["mode"] = ui.select(modes, label="Output mode", value=config["output"]["mode"], on_change=update_output).props("outlined dense")
                        output_controls["count"] = ui.input("Requested rows (new or total)", value=str(config["output"]["count"]), on_change=update_output).props("outlined dense inputmode=numeric")
                        for key, control in output_controls.items():
                            wire_error(key, control)
                    count_note = ui.label(count_description()).props('role=status aria-live=polite').classes("count-note")
            with ui.element("aside").classes("properties").props('aria-label="Selected field settings"'):
                properties()
        ui.label("Provisional format: ravel-workbook-experiment/1 • NiceGUI evaluation • No data leaves this local server").classes("footer-note")

    count_note = None
    field_notice = None
    shell()


if __name__ == "__main__":
    ui.run(host="127.0.0.1", port=8080, title="Ravel | Workbook experiment",
           dark=True, reload=False, show=False, prod_js=True, on_air=False)
