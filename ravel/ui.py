"""NiceGUI adapter for the shared single-table engine."""

import json
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path

from nicegui import app, run, ui

from .engine import generate, preview_rows, run_metadata
from .recipe import MAX_BYTES, ValidationError, loads
from .sample import assumption_origin, context as sample_context, parse_csv, profile
from .workspace import Workspace, field_form, whole
from .dataset import template as devices_template
from .web import DEMO_ROWS, DemoCapacity

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).with_name("static")
PUBLIC_DEMO = False
demo_capacity = DemoCapacity()
app.add_static_files("/ravel-brand", ROOT / "brand/svg")
app.add_static_file(url_path="/favicon.svg", local_file=ROOT / "brand/favicon/favicon.svg")
app.add_static_file(url_path="/favicon.ico", local_file=ROOT / "brand/favicon/favicon.ico")
RULES = dict(id="Sequential ID", constant="Constant text", sequence="Numeric sequence",
             integer="Random integer", decimal="Random decimal", category="Category", text_id="Formatted ID",
             normal="Normal numeric", boolean="Boolean", date="Calendar date", date_sequence="Date sequence",
             category_quota="Exact category counts", foreign_key="Parent key", child_index="Child row index")


def rule_summary(field):
    kind=field['kind']
    if kind in {'integer','decimal','date'}:
        summary=f'{field["minimum"]}–{field["maximum"]}'
    elif kind in {'id','text_id'}:
        summary=f'Start {field["start"]}'
    elif kind in {'sequence','date_sequence'}:
        summary=f'{field["start"]}, step {field["step"]}'
    elif kind=='normal':
        summary=f'Mean {field["mean"]} · SD {field["sd"]} · {field["places"]} decimals'
    elif kind=='boolean':
        summary=f'p(true) {field["probability"]}'
    elif kind=='constant':
        summary=field['value']
    elif kind in {'foreign_key','child_index'}:
        summary='Derived from the explicit relationship'
    elif kind=='category_quota':
        summary=', '.join(f'{v}: {c}' for v,c in zip(field['values'],field['counts']))
        return summary+f' · missing: {field["missing_count"]} · {field["scope"]}'
    else:
        summary=', '.join(field['values'])
    return summary+f' · p(missing) {field["missing_probability"]}'+(' · unique' if field.get('unique') else '')


def help_note(title, text):
    with ui.element("div").classes("context-help") as root:
        button = ui.button(icon="help_outline", color=None).props(f'flat dense aria-label="{title} help" aria-expanded=false')
        note = ui.label(text).classes("help-content").props("role=note")
        button.props(f"aria-describedby={note.html_id} aria-controls={note.html_id}")
        button.on("click", js_handler='''e => {
            const root = e.currentTarget.parentElement, open = root.dataset.open !== 'true';
            root.dataset.open = String(open); root.dataset.dismissed = String(!open);
            e.currentTarget.setAttribute('aria-expanded', String(open));
        }''')
        root.on("keydown.escape", js_handler='''e => {
            e.currentTarget.dataset.open = 'false'; e.currentTarget.dataset.dismissed = 'true';
            e.currentTarget.querySelector('button').setAttribute('aria-expanded', 'false');
        }''')
        for event in ("mouseenter", "focusin"):
            root.on(event, js_handler="e => { e.currentTarget.dataset.dismissed = 'false'; }")


def action(label, icon, handler, tip, primary=False, compact=False):
    button = ui.button("" if compact else label, icon=icon, color=None, on_click=handler).props(
        f'flat no-caps aria-label="{label}" title="{tip}"')
    if compact:
        button.classes("icon-action")
        button.tooltip(label + " · " + tip)
    if primary:
        button.classes("primary-action")
    return button


def chrome(theme, *, workbench=False):
    theme = "light" if theme == "light" else "dark"
    ui.add_css((ROOT / "experiments/workbook/workbook.css").read_text(encoding="utf-8"))
    ui.add_css((STATIC / "generator.css").read_text(encoding="utf-8"))
    ui.add_head_html('<link rel="icon" type="image/svg+xml" href="/favicon.svg" sizes="any">')
    dark = ui.dark_mode(theme != "light")
    with ui.dialog() as session_dialog, ui.card().classes("session-dialog"):
        ui.label("Session help").classes("section-title")
        ui.label("State is local to this page. Apply or discard pending edits before generating or saving. Exact quotas and linked tables are available. Save your recipe and CSV or dataset ZIP before closing. Run records include the generating environment and checksums.").classes("help")
        action("Close help", "close", session_dialog.close, "Return to the workbench")
    with ui.element("header").classes("toolbar"):
        mark = ui.element("img").classes("mark").props(
            f'src=/ravel-brand/ravel-mark-32-{theme}.svg width=32 height=32 alt="" aria-hidden=true')
        ui.label("Ravel").classes("brand-name")
        ui.label("Workbench").classes("muted edition")

        def change_theme(event):
            dark.set_value(event.value == "Dark")
            mark.props(f"src=/ravel-brand/ravel-mark-32-{event.value.lower()}.svg")
            options.close()

        with action("More options", "more_horiz", None, "Theme, layout and session help", compact=True).classes("options-button").props("aria-haspopup=menu") as options_button:
            with ui.menu().props('anchor="bottom right" self="top right"').classes("workbench-options") as options:
                ui.label("Appearance").classes("options-label")
                choice = ui.radio(["Light", "Dark"], value=theme.title(), on_change=change_theme).props(
                    'inline dense aria-label="Theme"').classes("theme-choice")
                ui.separator()
                if workbench:
                    action("Reset layout", "restart_alt", options.close, "Restore the default Properties width").on(
                        "click", js_handler="() => window.ravelWorkspaceLayout.reset()")
                action("Session help", "info_outline", lambda: (options.close(), session_dialog.open()), "How to keep your work")
        options.on_value_change(lambda e: options_button.props(f'aria-expanded={str(e.value).lower()}'))
        options_button.props("aria-expanded=false")
    if PUBLIC_DEMO:
        ui.label("Public demo · Up to 1,000 rows per run · Invented data only").classes("demo-note")
    return choice


@ui.page("/")
def home(theme: str = "dark"):
    choice = chrome(theme)
    with ui.element("main").classes("welcome generator-welcome"):
        ui.label("Compose a table.").classes("hero")
        ui.label("Choose columns, set rules, generate data.").classes("intro")
        with ui.row().classes("start-actions"):
            action("Create table", "add", lambda: ui.navigate.to(f"/table?theme={choice.value.lower()}"),
                   "Build a table from explicit rules", True)
            action("Open recipe", "folder_open", lambda: ui.navigate.to(f"/table?theme={choice.value.lower()}&open_recipe=true"),
                   "Open a saved single-table recipe")
            action("Start from sample", "upload_file", lambda: ui.navigate.to(f"/table?theme={choice.value.lower()}&open_sample=true"),
                   "Review editable assumptions from a local CSV")
            action("Use template", "account_tree", lambda: ui.navigate.to(f"/table?theme={choice.value.lower()}&template=devices"),
                   "Devices and measurements · runnable invented linked example")


@ui.page("/table")
def table(theme: str = "dark", open_recipe: bool = False, open_sample: bool = False, template: str = ""):
    if template not in {'','devices'}:
        chrome(theme)
        ui.label('This template is not available. Choose a runnable template from Home.')
        ui.link('Home','/')
        return
    state = Workspace(devices_template() if template else None)
    client = ui.context.client
    choice = chrome(theme, workbench=True)
    ui.add_head_html("<script>" + (STATIC / "layout.js").read_text(encoding="utf-8") + "</script>")
    ui.add_head_html("<script>" + (STATIC / "edit_focus.js").read_text(encoding="utf-8") + "</script>")
    ui.add_head_html('''<script>
        window.addEventListener('beforeunload', e => {
            if (window.ravelUnsaved) { e.preventDefault(); e.returnValue = ''; }
        });
    </script>''')
    controls, table_controls, errors, marks = {}, {}, {}, {}
    view_buttons = {}
    active_view = "Fields"
    busy = False
    pending_sample = None
    last_pending = False
    reported_error = False
    reported_error_key = None
    validation_errors = {}
    last_edited = None

    def report(message, error=False):
        nonlocal reported_error, reported_error_key
        reported_error = error
        reported_error_key = None
        status.set_text(message)
        status.classes(add="error" if error else "", remove="" if error else "error")

    def update_state():
        nonlocal last_pending
        if state.result is None:
            text = "No result yet"
        elif state.current:
            text = f"Current · {len(state.table_result.rows):,} rows"+ (f' · {len(state.recipe["tables"])} tables' if state.is_dataset else '')
        else:
            text = "Out of date · Apply or discard edits first" if state.has_drafts else "Out of date · Generate to update"
        result_state.set_text("Generating…" if busy else text)
        result_state.classes(add="stale" if state.result and not state.current else "",
                             remove="" if state.result and not state.current else "stale")
        draft_summary.set_text("Unapplied edits" if state.has_drafts else "All changes applied")
        pending = state.has_drafts
        edit_actions.props(f'data-pending={str(pending).lower()}')
        edit_actions.classes(add='has-pending' if pending else '', remove='' if pending else 'has-pending')
        pending_note.set_text('Unapplied changes' if pending else 'All changes applied')
        properties_name.set_text(state.field['name'])
        apply_button.set_enabled(pending and not busy)
        discard_button.set_enabled(pending and not busy)
        if pending != last_pending:
            if not pending:
                clear_errors()
                if reported_error:
                    report('')
            pending_announcement.set_text('Unapplied changes. Apply or discard your edits.' if pending else 'All changes applied. No unapplied changes.')
            last_pending = pending
        export_button.set_enabled(state.current and state.table_result is not None and not busy)
        record_button.set_enabled(state.current and not busy)
        dataset_button.set_visibility(state.is_dataset)
        dataset_button.set_enabled(state.current and state.is_dataset and not busy)
        if controls:
            applied = field_form(state.field)
            for key, mark in marks.items():
                mark.set_visibility(state.field_draft.get(key) != applied.get(key))
        if table_name_label is not None:
            table_name_label.set_text(state.table["name"])
        if sample_summary is not None:
            if "sample" in state.recipe:
                _, rows, retained, generated = sample_context(state.recipe)
                sample_summary.set_text(f'{len(rows):,} source rows · {retained:,} retained + {generated:,} new = {retained+generated:,} output')
            else:
                sample_summary.set_text(f'{len(state.recipe["tables"])} tables · {sum(table["row_count"] for table in state.recipe["tables"]):,} configured rows · Generate updates all tables' if state.is_dataset else '')
        if state.is_dataset and 'table_primary_key' in table_controls:
            options={'':'No primary key',**{field['id']:field['name'] for field in state.table['fields'] if field['kind'] in {'id','text_id'} or field.get('unique') or (field['kind']=='constant' and state.table['row_count']==1)}}
            if table_controls['table_primary_key'].options!=options:
                table_controls['table_primary_key'].set_options(options)
        client.run_javascript(f"window.ravelUnsaved = {json.dumps(bool(state.has_unsaved))};")

    def wire_error(key, control):
        control.without_auto_validation()
        with control.add_slot("error"):
            errors[key] = ui.label("").props("role=alert")

    def set_error(key, control, message=None):
        control.error = message
        control.props(remove="error-message")
        errors[key].set_text(message or "")
        control.props(f"aria-invalid={str(bool(message)).lower()}")
        if message:
            control.props(f"aria-describedby={errors[key].html_id}")
        else:
            control.props(remove="aria-describedby")

    def clear_errors():
        for key, control in {**controls, **table_controls}.items():
            set_error(key, control)
        validation_errors.clear()

    def editor_identity(key, column=False, field_id=None):
        return f'column:{state.table_id}:{field_id or state.selected}:{key}' if column else f'table:{state.table_id}:{key}'

    def wire_editor(key, control, column=False):
        control.props(f'data-editor={editor_identity(key, column)}')

    def clear_edited_errors(identity):
        for key, dependencies in list(validation_errors.items()):
            if identity in dependencies:
                control = {**controls, **table_controls}.get(key)
                if control is not None:
                    set_error(key, control)
                del validation_errors[key]
                if reported_error_key == key:
                    report('')

    async def restore_editor_focus(ticket):
        await client.run_javascript('window.ravelEditFocus.restore(' + json.dumps(dict(
            ticket=ticket, identity=last_edited,
            fallbacks=[editor_identity('name', True), editor_identity('row_count')])) + ')')

    async def focus_control(control):
        for selector in (controls.get("kind"),):
            if selector is not None and selector is not control:
                await selector.run_method("blur")
        await client.run_javascript(f'''
            await Vue.nextTick();
            const root = getHtmlElement({json.dumps(control.html_id)});
            const input = root?.querySelector('input, textarea, [role=combobox]') || root;
            if (input) {{ input.focus({{preventScroll: true}});
                (input.closest('.q-field') || input).scrollIntoView({{block:'center', behavior:'instant'}}); }}
        ''')

    async def show_error(exc):
        nonlocal reported_error_key
        if exc.path.startswith('tables.') and state.is_dataset:
            parts=exc.path.split('.')
            table=state.recipe['tables'][int(parts[1])]
            if table['id']!=state.table_id:
                report(f'{table["name"]}: {exc.message}',True)
                update_state()
                return
            exc=ValidationError('table.'+'.'.join(parts[2:]),exc.message)
        report(exc.message, True)
        field = None
        if exc.path == "seed":
            key = "seed"
        elif exc.path.startswith("table.fields."):
            key = exc.path.rsplit(".", 1)[-1]
            if key in {"values", "probabilities"}:
                key = "categories"
            elif key in {"counts", "unique"}:
                key = "quotas" if key=="counts" else "maximum" if "maximum" in controls else "table_row_count"
            index = int(exc.path.split(".")[2])
            field = state.table["fields"][index]
            if field["id"] != state.selected:
                report(f'Column “{field["name"]}”: {exc.message}', True)
                key = "table_row_count"
        else:
            key = "table_" + exc.path.rsplit(".", 1)[-1]
        control = {**controls, **table_controls}.get(key)
        if control is not None:
            set_error(key, control, exc.message)
            if field is not None:
                parameter = exc.path.rsplit('.', 1)[-1]
                parameter = {'values':'categories', 'probabilities':'categories', 'counts':'quotas'}.get(parameter, parameter)
                dependencies = {editor_identity(parameter, True, field['id']), editor_identity('kind', True, field['id'])}
                if exc.message in {'Minimum must not exceed maximum.', 'Minimum date must not exceed maximum date.'}:
                    dependencies.update(editor_identity(k, True, field['id']) for k in ['minimum', 'maximum'])
                elif parameter == 'unique' and exc.message.startswith('Unique domain has '):
                    dependencies.update(editor_identity(k, True, field['id']) for k in ['minimum', 'maximum', 'places'])
                    dependencies.update([editor_identity('row_count'), editor_identity('mode')])
                elif parameter == 'unique' and exc.message == 'Unique generation requires zero missing probability.':
                    dependencies.add(editor_identity('missing_probability', True, field['id']))
                elif parameter == 'quotas' and exc.message.startswith('Exact counts including missing must total '):
                    dependencies.update(editor_identity(k, True, field['id']) for k in ['missing_count', 'scope'])
                    dependencies.update([editor_identity('row_count'), editor_identity('mode')])
            else:
                dependencies = {editor_identity({'table_name':'name', 'table_row_count':'row_count', 'table_primary_key':'primary_key'}.get(key, key))}
            validation_errors[key] = dependencies
            reported_error_key = key
            await focus_control(control)
        update_state()

    def edit_field(key, value):
        nonlocal last_edited
        value = value if value is not None else ""
        if state.field_draft.get(key) != value:
            last_edited = editor_identity(key, True)
            clear_edited_errors(last_edited)
        state.field_draft[key] = value
        update_state()

    def edit_table(key, value):
        nonlocal last_edited
        value = value if value is not None else ""
        if state.table_draft.get(key) != value:
            last_edited = editor_identity(key)
            clear_edited_errors(last_edited)
        state.table_draft[key] = value
        update_state()

    async def change_kind(event):
        nonlocal last_edited
        last_edited = editor_identity('kind', True)
        clear_edited_errors(last_edited)
        state.change_kind(event.value)
        await properties.refresh()
        update_state()
        await focus_control(controls["kind"])

    async def apply():
        if not state.has_drafts or busy:
            return
        ticket = await client.run_javascript(f'window.ravelEditFocus.capture({json.dumps(apply_button.html_id)})')
        clear_errors()
        try:
            state.apply()
        except ValidationError as exc:
            await show_error(exc)
            return
        await definitions.refresh()
        if state.is_dataset:
            await navigation.refresh()
            await relationships.refresh()
        if "sample" in state.recipe or state.is_dataset:
            await properties.refresh()
        update_state()
        report("Changes applied. Generate to update the result.")
        await restore_editor_focus(ticket)

    async def discard():
        if not state.has_drafts or busy:
            return
        ticket = await client.run_javascript(f'window.ravelEditFocus.capture({json.dumps(discard_button.html_id)})')
        state.discard()
        for key, control in table_controls.items():
            control.set_value(state.table_draft[{'table_name':'name','table_row_count':'row_count','table_primary_key':'primary_key'}.get(key,key)])
        await properties.refresh()
        clear_errors()
        update_state()
        report("Unapplied edits discarded.")
        await restore_editor_focus(ticket)

    async def column_action(operation, identity=None):
        try:
            if identity is None:
                getattr(state, operation)()
            else:
                state.select(identity)
        except ValidationError as exc:
            await show_error(exc)
            return
        await definitions.refresh()
        await properties.refresh()
        update_state()
        report("Column selected." if identity else {
            "add": "Column added.", "duplicate": "Column duplicated.", "remove": "Column removed."
        }[operation])
        await focus_control(controls["name"])

    async def confirm_remove():
        try:
            state.require_applied()
            if len(state.table["fields"]) == 1:
                raise ValidationError("column", "Keep at least one column.")
        except ValidationError as exc:
            await show_error(exc)
            return
        remove_note.set_text(f'Remove “{state.field["name"]}”? The current result will become out of date.')
        remove_dialog.open()

    async def remove():
        remove_dialog.close()
        await column_action("remove")

    async def run_generation():
        nonlocal busy
        try:
            snapshot = state.recipe_for_run()
        except ValidationError as exc:
            await show_error(exc)
            return
        if busy:
            return
        busy = True
        generate_button.disable()
        update_state()
        total=sum(table['row_count'] for table in snapshot['tables']) if 'tables' in snapshot else snapshot['table']['row_count']
        report(f'Generating {total:,} rows'+(' across all tables…' if 'tables' in snapshot else '…'))
        try:
            with demo_capacity.reserve(snapshot) if PUBLIC_DEMO else nullcontext():
                state.result = await run.io_bound(generate, snapshot)
            await preview.refresh()
            switch_view("Preview")
            report(f"Generated {total:,} rows." if state.current else "Generation finished; edits made during the run need Apply and Generate.")
        except (ValidationError, MemoryError) as exc:
            report("Generation failed: " + str(exc), True)
        finally:
            busy = False
            generate_button.enable()
            update_state()

    async def save():
        try:
            payload = state.save_recipe()
        except ValidationError as exc:
            await show_error(exc)
            return
        ui.download.content(payload, filename="dataset.recipe.json" if state.is_dataset else "table.recipe.json", media_type="application/json")
        state.mark_saved()
        update_state()
        report("Recipe saved.")

    async def export():
        try:
            payload = state.export_csv()
        except ValidationError as exc:
            await show_error(exc)
            return
        ui.download.content(payload.encode("utf-8"), filename=state.table_id+'.csv' if state.is_dataset else "table.csv", media_type="text/csv")
        state.mark_exported()
        update_state()
        report(f"Exported {len(state.table_result.rows):,} rows.")

    async def export_dataset():
        try:
            payload=state.export_dataset()
        except ValidationError as exc:
            await show_error(exc)
            return
        ui.download.content(payload,filename='dataset.zip',media_type='application/zip')
        state.mark_exported(all_tables=True)
        update_state()
        report('Exported all tables, recipe, dictionary and validation/run record.')

    async def save_record():
        if not state.current:
            await show_error(ValidationError("result", "Generate a current result before saving its run record."))
            return
        payload = dict(run_metadata(state.result), recipe=json.loads(state.result.recipe_json))
        ui.download.content(json.dumps(payload, indent=2), filename="dataset.run.json" if state.is_dataset else "table.run.json", media_type="application/json")
        report("Run record saved with the exact recipe and CSV checksum.")

    async def load_file(event):
        nonlocal active_view
        try:
            payload = await event.file.read()
            candidate = loads(payload)
        except (ValidationError, ValueError) as exc:
            load_error.set_text(str(exc) + " Current table preserved.")
            uploader.reset()
            return
        state.replace(candidate)
        active_view = "Fields"
        load_dialog.close()
        uploader.reset()
        await shell.refresh()
        report("Recipe loaded. Generate to preview data.")
        update_state()
        await focus_control(controls["name"])

    def open_load():
        load_error.set_text("")
        load_dialog.open()

    async def sample_file(event):
        nonlocal pending_sample
        try:
            payload = await event.file.read()
            if PUBLIC_DEMO and len(parse_csv(payload, sample_delimiter.value)[2]) > DEMO_ROWS:
                raise ValidationError('sample', 'Public demo: import at most 1,000 invented source rows.')
            pending_sample = profile(payload, sample_delimiter.value)
        except (ValidationError, ValueError) as exc:
            pending_sample = None
            use_sample.disable()
            sample_error.set_text(str(exc) + " Current table preserved.")
            sample_uploader.reset()
            await sample_review.refresh()
            return
        sample_error.set_text("")
        confirm_ids.set_value(False)
        await sample_review.refresh()
        use_sample.enable()

    async def use_import():
        nonlocal active_view
        if pending_sample is None:
            return
        from copy import deepcopy
        candidate = deepcopy(pending_sample)
        if confirm_ids.value:
            candidate["sample"]["confirmed"] = candidate["sample"]["identifiers"][:]
        try:
            state.replace(candidate, saved=False)
        except ValidationError as exc:
            sample_error.set_text(str(exc))
            return
        active_view = "Fields"
        sample_dialog.close()
        await shell.refresh()
        report("Sample imported. Review assumptions and confirm identifier rules before generating.")
        await focus_control(controls["name"])

    async def delimiter_changed():
        nonlocal pending_sample
        pending_sample = None
        use_sample.disable()
        sample_uploader.reset()
        await sample_review.refresh()

    def open_sample_dialog():
        sample_error.set_text("")
        sample_dialog.open()

    async def confirm_id():
        try:
            state.confirm_identifier()
        except ValidationError as exc:
            await show_error(exc)
            return
        await properties.refresh()
        update_state()
        report("Identifier rule confirmed. Generate when ready.")

    @ui.refreshable
    def sample_review():
        if pending_sample is None:
            ui.label("Choose a CSV to review its source and suggested assumptions.").classes("muted")
            return
        _, headers, rows = parse_csv(pending_sample["sample"]["csv_utf8"], pending_sample["sample"]["delimiter"])
        ui.label(f'{len(rows):,} rows · {len(headers)} columns · only empty cells count as missing').classes("source-count")
        with ui.element("div").classes("source-scroll").props('tabindex=0 role=region aria-label="Sample source; scroll to review rows"'):
            with ui.element("table").classes("preview-table sample-source"):
                with ui.element("thead"), ui.element("tr"):
                    for header in headers:
                        with ui.element("th"):
                            ui.label(header)
                with ui.element("tbody"):
                    for row in rows[:10]:
                        with ui.element("tr"):
                            for cell in row:
                                with ui.element("td"):
                                    ui.label(cell)
        for field in pending_sample["table"]["fields"]:
            if field['id'] in pending_sample['sample']['identifiers']:
                suggestion = f"{RULES[field['kind']]} from {field.get('start', 'explicit rule needed')} · excluded from fitting"
            elif field['kind'] in {'integer','decimal'}:
                suggestion = f"uniform {field['minimum']}–{field['maximum']} · missing {field['missing_probability']}"
            elif field['kind'] == 'category':
                suggestion = ', '.join(f'{v}: {Decimal(p).normalize():f}' for v,p in zip(field['values'],field['probabilities']))
            else:
                suggestion = f"{RULES[field['kind']]} · missing {field['missing_probability']}"
            ui.label(f"{field['name']} · {suggestion}").classes("sample-assumption")

    with ui.dialog() as sample_dialog, ui.card().classes("sample-dialog"):
        ui.label("Start from sample").classes("section-title")
        with ui.element('div').classes('sample-body'):
            ui.label("Review suggestions before replacing this table and its unsaved edits. Original cells are retained exactly in Extend mode.").classes("help")
            if PUBLIC_DEMO:
                ui.label("Files are processed on this shared server. Use invented data only; at most 1,000 source rows and 1 MiB.").classes("help")
            sample_delimiter = ui.select({',':'Comma', ';':'Semicolon', '\t':'Tab'}, value=',', label="CSV delimiter", on_change=delimiter_changed).props("outlined dense options-dense")
            sample_error = ui.label("").props("role=alert").classes("error")
            sample_uploader = ui.upload(label="Choose sample CSV", auto_upload=True, max_files=1, max_file_size=MAX_BYTES,
                on_upload=sample_file, on_rejected=lambda: sample_error.set_text("Choose a UTF-8 CSV no larger than 1 MiB.")).props("accept=.csv,.tsv")
            sample_review()
            ui.label("Suggestions describe this sample. Review ranges and frequencies; generation treats columns independently.").classes("help")
        with ui.element('div').classes('sample-actions').props('role=group aria-label="Import confirmation"'):
            confirm_ids = ui.checkbox("Use the displayed sequential identifier rules", value=False)
            with ui.row():
                use_sample = action("Use sample", "check", use_import, "Replace current table with the reviewed sample and assumptions", True)
                use_sample.disable()
                action("Cancel import", "close", sample_dialog.close, "Keep the current table and edits")

    with ui.dialog() as load_dialog, ui.card().classes("load-dialog"):
        ui.label("Open recipe").classes("section-title")
        ui.label("Loading replaces this table, edits and previous result.").classes("help")
        if PUBLIC_DEMO:
            ui.label("Recipes and embedded samples are processed on this shared server. Use invented data only.").classes("help")
        load_error = ui.label("").props("role=alert").classes("error")
        uploader = ui.upload(label="Choose recipe JSON", auto_upload=True, max_files=1, max_file_size=MAX_BYTES,
                             on_upload=load_file,
                             on_rejected=lambda: load_error.set_text("Choose a JSON recipe no larger than 1 MiB.")).props("accept=.json")
        action("Cancel", "close", load_dialog.close, "Keep the current table")
    with ui.dialog() as remove_dialog, ui.card().classes("remove-dialog"):
        ui.label("Remove column?").classes("section-title")
        remove_note = ui.label("").classes("help")
        with ui.row():
            action("Cancel removal", "close", remove_dialog.close, "Keep the column")
            action("Remove column", "delete_outline", remove, "Confirm removal")

    async def leave_table():
        await client.run_javascript("window.ravelUnsaved = false;")
        ui.navigate.to(f"/?theme={choice.value.lower()}")

    async def request_home():
        if state.has_unsaved:
            leave_dialog.open()
        else:
            await leave_table()

    with ui.dialog() as leave_dialog, ui.card().classes("leave-dialog"):
        ui.label("Leave this table?").classes("section-title")
        ui.label("Unsaved settings, edits or output will be lost. Save your recipe and export current data to keep them.").classes("help")
        with ui.row():
            action("Keep editing", "edit", leave_dialog.close, "Stay with this table")
            action("Leave table", "home", leave_table, "Discard unsaved work and return Home")

    async def refresh_workspace():
        preference=await client.run_javascript('window.ravelWorkspaceLayout.preference(window.ravelWorkspaceLayout.grid())')
        await shell.refresh()
        await client.run_javascript(f'await Vue.nextTick(); window.ravelWorkspaceLayout.prefer(window.ravelWorkspaceLayout.grid(), {json.dumps(preference)});')
        update_state()

    async def select_table(identity):
        try:
            state.select_table(identity)
        except ValidationError as exc:
            await show_error(exc)
            return
        await refresh_workspace()
        report(f'Selected {state.table["name"]}.')
        await focus_control(controls['name'])

    async def add_table():
        try:
            state.add_table()
        except ValidationError as exc:
            await show_error(exc)
            return
        await refresh_workspace()
        report('Table added. Configure its fields or choose a parent relationship.')
        await focus_control(controls['name'])

    async def preview_relationship():
        try:
            candidate=state.relationship_candidate(rel_parent.value,whole(rel_per.value,'relationships.children_per_parent'))
        except ValidationError as exc:
            rel_error.set_text(exc.message)
            rel_counts.set_text('')
            rel_apply.disable()
            return
        rel_error.set_text('')
        rel_counts.set_text(' · '.join(f'{table["name"]}: {table["row_count"]:,} rows' for table in candidate['tables']))
        rel_apply.enable()

    async def open_relationship():
        try:
            state.require_applied()
        except ValidationError as exc:
            await show_error(exc)
            return
        options={table['id']:table['name'] for table in state.recipe['tables'] if table['id']!=state.table_id and table['primary_key'] is not None}
        existing=next((link for link in state.recipe['relationships'] if link['child']==state.table_id),None)
        rel_title.set_text('Relationship for '+state.table['name'])
        rel_parent.set_options(options,value=existing['parent'] if existing else next(iter(options),None))
        rel_per.set_value(str(existing['children_per_parent'] if existing else 2))
        rel_remove.set_enabled(existing is not None)
        await preview_relationship()
        relationship_dialog.open()

    async def apply_relationship():
        try:
            state.set_relationship(rel_parent.value,whole(rel_per.value,'relationships.children_per_parent'))
        except ValidationError as exc:
            rel_error.set_text(exc.message)
            return
        relationship_dialog.close()
        await refresh_workspace()
        report('Relationship and displayed table counts applied. Generate all tables to update the result.')
        await focus_control(controls['name'])

    async def remove_relationship():
        try:
            state.remove_relationship()
        except ValidationError as exc:
            rel_error.set_text(exc.message)
            return
        relationship_dialog.close()
        await refresh_workspace()
        report('Relationship and its derived columns removed. Other columns and row counts were retained.')
        await focus_control(controls['name'])

    with ui.dialog() as relationship_dialog,ui.card().classes('relationship-dialog'):
        rel_title=ui.label('Relationship').classes('section-title')
        ui.label('Choose one parent and an exact child count per parent. Review every resulting count below; Apply also updates dependent child-table counts.').classes('help')
        rel_parent=ui.select({},label='Parent table',value=None,on_change=preview_relationship).props('outlined dense options-dense')
        rel_per=ui.input('Rows per parent',value='2',on_change=preview_relationship).props('outlined dense')
        rel_counts=ui.label('').classes('relationship-counts').props('role=status')
        rel_error=ui.label('').classes('error').props('role=alert')
        with ui.row():
            rel_apply=action('Apply relationship and counts','check',apply_relationship,'Apply the parent link and every displayed row count',True)
            action('Cancel relationship','close',relationship_dialog.close,'Keep the current recipe and counts')
        ui.label('Remove also removes this table’s Parent key and Child row index columns. Save the current recipe first to keep the relationship.').classes('help')
        rel_remove=action('Remove relationship','link_off',remove_relationship,'Remove the link and its derived columns after reviewing this notice')

    with ui.element("nav").classes("action-toolbar").props('aria-label="Table actions"'):
        with ui.link(target=f"/?theme={choice.value.lower()}").classes("home-link") as home_link:
            ui.icon("home").props("aria-hidden=true")
            ui.label("Home")
        home_link.on("click", request_home, js_handler="e => { e.preventDefault(); emit(); }")
        choice.on_value_change(lambda e: home_link.props(f"href=/?theme={e.value.lower()}"))
        generate_button = action("Generate table", "play_arrow", run_generation, "Generate using applied rules", True)
        export_button = action("Export CSV", "download", export, "Export the current generated result")
        dataset_button = action("Export dataset ZIP", "folder_zip", export_dataset, "Export all tables and matching recipe, dictionary and validation/run record")
        action("Save recipe", "save", save, "Save applied rules as a versioned recipe")
        action("Open recipe", "folder_open", open_load, "Open recipe · replaces the current table", compact=True)
        action("Import CSV", "upload_file", open_sample_dialog, "Import CSV · review source and assumptions", compact=True)
        record_button = action("Save run record", "description", save_record, "Save run record · recipe, environment and CSV checksum", compact=True)
    status = ui.label("Ready. Configure columns, Apply changes, then Generate.").classes("status-line").props("role=status aria-live=polite")
    pending_announcement = ui.label('').classes('pending-announcement').props('role=status aria-live=polite aria-atomic=true')

    def switch_view(view):
        nonlocal active_view
        active_view = view
        fields_region.set_visibility(view == "Fields")
        preview_region.set_visibility(view == "Preview")
        source_region.set_visibility(view == "Source")
        relationships_region.set_visibility(view=='Relationships')
        for name, button in view_buttons.items():
            button.props(f"aria-pressed={str(name == view).lower()}")
            button.classes(add="active-view" if name == view else "", remove="" if name == view else "active-view")

    @ui.refreshable
    def navigation():
        nonlocal table_name_label
        ui.label('Workbook').classes('pane-title')
        if state.is_dataset:
            ui.label(f'{len(state.recipe["tables"])} tables').classes('muted')
            for table in state.recipe['tables']:
                button=ui.button(table['name'],color=None,on_click=lambda identity=table['id']:select_table(identity)).props('flat no-caps').classes('table-button dataset-table-button'+(' selected-table' if table['id']==state.table_id else ''))
                button._props['aria-label']='Select table '+table['name']
                button.props(f'aria-pressed={str(table["id"]==state.table_id).lower()}')
                if table['id']==state.table_id:
                    table_name_label=button
                ui.label(f'{table["row_count"]:,} rows').classes('table-count muted')
        else:
            ui.label('1 table').classes('muted')
            table_name_label=ui.label(state.table['name']).classes('table-button table-name-label')
        ui.label('Sample assumptions' if 'sample' in state.recipe else 'Explicit rules').classes('muted')
        if 'sample' not in state.recipe:
            button=action('Add table','add',add_table,'Add an independent table; configure its relationship explicitly')
            button.set_enabled(not state.is_dataset or len(state.recipe['tables'])<8)

    @ui.refreshable
    def relationships():
        if not state.is_dataset:
            return
        if not state.recipe['relationships']:
            ui.label('No relationships yet. Select a child table and choose Relationship.').classes('muted')
        tables={table['id']:table for table in state.recipe['tables']}
        for link in state.recipe['relationships']:
            ui.label(f'{tables[link["parent"]]["name"]} → {tables[link["child"]]["name"]} · {link["children_per_parent"]:,} rows per parent · {tables[link["child"]]["row_count"]:,} child rows')

    @ui.refreshable
    def definitions():
        with ui.element("table").classes("definition-table generator-definitions"):
            with ui.element("thead"), ui.element("tr"):
                for title in ["Column", "Rule", "Applied settings"]:
                    with ui.element("th").props("scope=col"):
                        ui.label(title)
            with ui.element("tbody"):
                for field in state.table["fields"]:
                    with ui.element("tr").classes("selected-row" if field["id"] == state.selected else "").props(f'data-field-id={field["id"]}'):
                        with ui.element("td"):
                            button = ui.button(field["name"], color=None, on_click=lambda f=field: column_action("select", f["id"])).props(
                                'flat no-caps').classes("field-button")
                            button._props["aria-label"] = "Select column " + field["name"]
                        with ui.element("td"):
                            ui.label(RULES[field["kind"]])
                        with ui.element("td").classes("applied-settings"):
                            ui.label(rule_summary(field))

    @ui.refreshable
    def preview():
        if state.table_result is None:
            with ui.element("div").classes("empty-preview"):
                ui.icon("table_chart").props("aria-hidden=true")
                ui.label("Generate to preview your data.")
            return
        result = state.table_result
        with ui.element("div").classes("preview-scroll").props('tabindex=0 role=region aria-label="Generated table; use arrow keys to scroll"'):
            with ui.element("table").classes("preview-table"):
                with ui.element("caption"):
                    ui.label(f"First {min(100, len(result.rows)):,} of {len(result.rows):,} output rows")
                with ui.element("thead"), ui.element("tr"):
                    for header in result.headers:
                        with ui.element("th").props("scope=col"):
                            ui.label(header)
                with ui.element("tbody"):
                    for row in preview_rows(result):
                        with ui.element("tr"):
                            for value in row:
                                with ui.element("td"):
                                    ui.label(value)

    @ui.refreshable
    def properties():
        controls.clear()
        marks.clear()
        with ui.element("div").classes("property-fields"):
            labels = dict(name="Column name", kind="Rule", start="Start", step="Step", minimum="Minimum",
                          maximum="Maximum", places="Decimal places", value="Constant value",
                          prefix="ID prefix", width="Minimum digits",
                          mean="Mean", sd="Standard deviation", probability="True probability",
                          quotas="Categories and exact counts", scope="Quota scope", missing_count="Exact missing count",
                          categories="Categories and probabilities", missing_probability="Missing probability")
            form = state.field_draft
            order = ["name", "kind"] + [k for k in ["prefix", "width", "start", "step", "minimum", "maximum", "mean", "sd", "places", "probability", "value", "categories", "quotas", "scope", "missing_count"] if k in form] + ["missing_probability"]
            for key in order:
                with ui.element("div").classes("setting-row").props(f"data-setting={key}"):
                    if key == "kind":
                        options={kind:label for kind,label in RULES.items() if kind not in {'foreign_key','child_index'} or kind==form[key] or (state.is_dataset and kind=='child_index' and any(link['child']==state.table_id for link in state.recipe['relationships']))}
                        control = ui.select(options, label=labels[key], value=form[key], on_change=change_kind).props("outlined dense options-dense")
                        if form[key]=='foreign_key':
                            control.disable()
                    elif key in {"categories", "quotas"}:
                        control = ui.textarea(labels[key], value=form[key], on_change=lambda e, k=key: edit_field(k, e.value)).props("outlined rows=4")
                    elif key=="scope":
                        control = ui.select({'generated':'New generated rows','final':'Final output including originals'}, label=labels[key], value=form[key], on_change=lambda e: edit_field('scope',e.value)).props('outlined dense options-dense')
                    else:
                        control = ui.input(labels[key], value=form[key], on_change=lambda e, k=key: edit_field(k, e.value)).props("outlined dense")
                    controls[key] = control
                    wire_editor(key, control, True)
                    wire_error(key, control)
                    with ui.row().classes("setting-state"):
                        ui.label(assumption_origin(state.recipe, state.selected, key)).classes("setting-origin")
                        marks[key] = ui.label("Draft").classes("draft-mark")
            if form['kind'] in {'integer','decimal','date','id','text_id'}:
                with ui.element('div').classes('setting-row').props('data-setting=unique'):
                    unique = ui.checkbox('Require unique values',value=form.get('unique')=='True',on_change=lambda e: edit_field('unique',str(e.value)))
                    wire_editor('unique', unique, True)
                    marks['unique']=ui.label('Draft').classes('draft-mark')
        if state.selected in state.recipe.get("sample", {}).get("identifiers", []):
            ui.label("Identifier · excluded from fitting").classes("muted")
            if state.selected in state.recipe["sample"]["confirmed"]:
                ui.label("Identifier rule confirmed").classes("setting-origin")
            else:
                action("Confirm identifier rule", "verified", confirm_id, "Confirm the applied sequential identifier policy")
        with ui.row().classes("label-help"):
            help_note("Rule", "Ranges include both endpoints. Category probabilities use A,0.25 and B,0.75; they sum to1. Exact counts use A,600 and B,400 plus an exact missing count; choose new rows or final output scope. Normal uses a positive SD and half-even output rounding; unsupported draws fail without clipping. Dates use ISO YYYY-MM-DD and whole-day steps. Unique finite ranges must have enough unused values and zero missing probability. IDs cannot be missing.")
            ui.label("Rule help").classes("muted rule-help-label")

    @ui.refreshable
    def shell():
        nonlocal fields_region, preview_region, source_region, relationships_region, result_state, draft_summary, table_name_label, sample_summary
        nonlocal edit_actions, pending_note, apply_button, discard_button, properties_name
        table_controls.clear()
        view_buttons.clear()
        with ui.element("main").classes("workbook-grid generator-grid"):
            with ui.element("nav").classes("navigator").props('aria-label="Workbook"'):
                navigation()
            with ui.element("section").classes("sheet"):
                with ui.row().classes("sheet-heading"):
                    ui.label("Columns & data").classes("sheet-title")
                    draft_summary = ui.label("").classes("draft-summary muted")
                with ui.row().classes("view-bar"):
                    for name in ["Fields", "Preview"] + (["Source"] if "sample" in state.recipe else []) + (['Relationships'] if state.is_dataset else []):
                        view_buttons[name] = ui.button(name, color=None, on_click=lambda v=name: switch_view(v)).props(
                            "flat no-caps").classes("view-button")
                    help_note("Preview", "The first 100 rows of the actual generated table, formatted exactly as CSV. Previous data remains visible but export is blocked when edits make it out of date.")
                with ui.row().classes("column-actions"):
                    action("Add column", "add", lambda: column_action("add"), "Add a new random integer column", compact=True)
                    action("Duplicate column", "content_copy", lambda: column_action("duplicate"), "Copy settings with a new identity and random stream", compact=True)
                    action("Remove selected column", "delete_outline", confirm_remove, "Remove this column after confirmation", compact=True)
                    if state.is_dataset:
                        action('Relationship','account_tree',open_relationship,'Review the selected table’s parent and explicit row counts')
                result_state = ui.label("").classes("result-state").props("role=status aria-live=polite")
                sample_summary = ui.label("").classes("sample-summary muted").props("role=status")
                with ui.element("div").classes("fields-view").props('tabindex=0 role=region aria-label="Column definitions; scroll horizontally if needed"') as fields_region:
                    definitions()
                with ui.element("div").classes("preview-view") as preview_region:
                    preview()
                with ui.element("div").classes("source-view") as source_region:
                    if "sample" in state.recipe:
                        _, headers, rows = parse_csv(state.recipe['sample']['csv_utf8'], state.recipe['sample']['delimiter'])
                        ui.label(f'Original sample · first {min(10,len(rows))} of {len(rows):,} rows').classes("muted")
                        with ui.element("div").classes("source-scroll").props('tabindex=0 role=region aria-label="Original sample rows; use arrow keys to scroll"'), ui.element("table").classes("preview-table sample-source"):
                            with ui.element("thead"), ui.element("tr"):
                                for header in headers:
                                    with ui.element("th"):
                                        ui.label(header)
                            with ui.element("tbody"):
                                for row in rows[:10]:
                                    with ui.element("tr"):
                                        for cell in row:
                                            with ui.element("td"):
                                                ui.label(cell)
                with ui.element('div').classes('relationships-view') as relationships_region:
                    relationships()
            divider = ui.element("div").classes("workspace-divider").props(
                'role=separator tabindex=0 aria-label=Properties aria-orientation=vertical '
                'aria-valuemin=300 aria-valuemax=560 aria-valuenow=312 aria-valuetext="Properties 312 pixels" '
                'title="Drag to resize. Left widens, Right narrows, Shift moves 40 pixels. Home/End set limits. Escape cancels a drag."')
            with divider:
                ui.element("span").classes("divider-grip").props("aria-hidden=true")
            for event, handler in (("pointerdown", "start(e)"), ("pointermove", "move(e)"),
                                   ("pointerup", "finish(e)"), ("pointercancel", "finish(e, true)"),
                                   ("lostpointercapture", "finish(e)"), ("keydown", "key(e)")):
                divider.on(event, js_handler=f"e => window.ravelWorkspaceLayout.{handler}")
            with ui.element("aside").classes("properties").props('aria-label="Selected column settings"') as pane:
                with ui.row().classes("pane-heading"):
                    with ui.row().classes("label-help"):
                        ui.label("Properties").classes("pane-title")
                        help_note("Properties", "Apply commits both column and table edits. Generate, Save and column actions require applied edits. A changed result is out of date until you generate again.")
                    properties_name = ui.label(state.field["name"]).classes("section-title mono")
                hint = ui.label("Resize: drag the divider or Tab to it, then ← / →.").classes("layout-hint muted")
                divider.props(f"aria-controls={pane.html_id} aria-describedby={hint.html_id}")
                with ui.element('div').classes('property-body'):
                    properties()
                with ui.element('div').classes('edit-actions').props('role=group aria-label="Apply or discard changes" data-pending=false') as edit_actions:
                    pending_note = ui.label('All changes applied').classes('pending-note')
                    apply_button = action("Apply changes", "check", apply, "Apply column, row count, seed and table name edits", True).classes("apply-button")
                    discard_button = action("Discard edits", "undo", discard, "Restore the applied settings").classes("discard-button")
            with ui.element("div").classes("output-panel"):
                with ui.row().classes("output-controls"):
                    if "sample" in state.recipe:
                        mode = ui.select({'new':'Generate new rows', 'extend':'Extend to total'}, value=state.table_draft['mode'], label='Sample mode', on_change=lambda e: edit_table('mode', e.value)).props('outlined dense options-dense')
                        table_controls['mode'] = mode
                        wire_editor('mode', mode)
                        wire_error('mode', mode)
                    for key, label, control_key in [("name", "Table name", "table_name"), ("row_count", "Rows", "table_row_count"), ("seed", "Seed", "seed")]:
                        control = ui.input(label, value=state.table_draft[key], on_change=lambda e, k=key: edit_table(k, e.value)).props("outlined dense")
                        table_controls[control_key] = control
                        wire_editor(key, control)
                        wire_error(control_key, control)
                    if state.is_dataset:
                        key_control=ui.select({'':'No primary key',**{field['id']:field['name'] for field in state.table['fields'] if field['kind'] in {'id','text_id'} or field.get('unique') or (field['kind']=='constant' and state.table['row_count']==1)}},label='Primary key',value=state.table_draft['primary_key'],on_change=lambda e:edit_table('primary_key',e.value)).props('outlined dense options-dense')
                        table_controls['table_primary_key']=key_control
                        wire_editor('primary_key', key_control)
                        wire_error('table_primary_key',key_control)
                    limits = "Public demo: at most 1,000 rows across all tables and 20,000 cells per run. Larger recipes can run locally. " if PUBLIC_DEMO else "Rows: 1–100,000; columns: 1–50; at most 2 million cells. "
                    help_note("Generation", limits + "Seed: 0–2^63−1. Apply both table and column edits before generating. The same recipe and pinned environment reproduce the same CSV.")
        ui.label("Session only · Save your recipe and CSV to keep them").classes("footer-note")
        switch_view(active_view)
        ui.run_javascript("await Vue.nextTick(); window.ravelWorkspaceLayout.init();")
        update_state()

    fields_region = preview_region = source_region = relationships_region = result_state = draft_summary = table_name_label = sample_summary = None
    edit_actions = pending_note = apply_button = discard_button = properties_name = None
    shell()
    if open_recipe:
        ui.timer(0, open_load, once=True)
    elif open_sample:
        ui.timer(0, open_sample_dialog, once=True)


def launch(port=8090, host="127.0.0.1", *, public_demo=False):
    global PUBLIC_DEMO
    PUBLIC_DEMO = public_demo
    ui.run(host=host, port=port, title="Ravel | Workbench", favicon=ROOT / "brand/favicon/favicon.ico",
           dark=True, reload=False, show=False, prod_js=True, on_air=False)
