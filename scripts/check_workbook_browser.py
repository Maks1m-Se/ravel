"""Keyboard/state assertions for the running fixture workbook; see development.md."""

import argparse
from datetime import datetime, timezone
import json
from importlib.metadata import version
from itertools import product
from pathlib import Path
import platform
import re
import sys
import traceback
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.workbook.config import new_config  # noqa: E402


def keyboard_to(page, target):
    """Navigate only; never use this helper to assert post-action focus."""
    for _ in range(65):
        if target.evaluate('(e) => e === document.activeElement || e.contains(document.activeElement)'):
            return
        page.keyboard.press('Tab')
    raise AssertionError(f'Cannot reach {target} with Tab')


def type_value(page, label, value):
    target = page.get_by_label(label, exact=True)
    keyboard_to(page, target)
    page.keyboard.press('Control+a')
    page.keyboard.type(value)
    expect(target).to_have_value(value)


def activate(page, name):
    keyboard_to(page, page.get_by_role('button', name=name, exact=True))
    page.keyboard.press('Enter')


def assert_error(page, label, message, *, focused=True):
    target = page.get_by_label(label, exact=True)
    expect(target).to_have_attribute('aria-invalid', 'true')
    if focused:
        expect(target).to_be_focused()  # no Tab helper after the failed action
    described_by = target.get_attribute('aria-describedby')
    assert described_by, f'{label} has no associated error message'
    error = page.locator(f'#{described_by.split()[0]}')
    expect(error).to_contain_text(message)
    expect(error).to_be_in_viewport(ratio=1)
    expect(target).to_be_in_viewport(ratio=1)
    # Viewport presence alone does not catch an error painted over another input.
    assert error.evaluate('''e => {
        const r = e.getBoundingClientRect();
        const field = e.closest('.q-field');
        const f = field.getBoundingClientRect();
        return r.top >= f.top && r.bottom <= f.bottom + 1 &&
            [...document.querySelectorAll('.q-field__control')].every(other => {
                const o = other.getBoundingClientRect();
                return r.right <= o.left || r.left >= o.right || r.bottom <= o.top || r.top >= o.bottom;
            });
    }'''), f'{label}: error overlaps a control or escapes its field'
    return {'label': label, 'message': error.inner_text(),
            'bounds': error.bounding_box(), 'focused': focused}


def assert_focus_style(page, target):
    expect(target).to_be_focused()
    result = target.evaluate('''e => {
        const ring = e.closest('.q-field') || e;
        const style = getComputedStyle(ring);
        const rgb = c => c.match(/[\\d.]+/g).map(Number);
        const lum = c => rgb(c).slice(0, 3).map(v => {
            v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        }).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
        let surface = ring, bg;
        do { bg = getComputedStyle(surface).backgroundColor; surface = surface.parentElement; }
        while (surface && (rgb(bg)[3] ?? 1) === 0);
        const color = parseFloat(style.outlineWidth) > 0 ? style.outlineColor :
            style.boxShadow.match(/rgba?\\([^)]+\\)/)?.[0];
        const a = color ? lum(color) : 0, b = lum(bg);
        return {tag: e.tagName, label: e.getAttribute('aria-label') || e.innerText,
            focusVisible: e.matches(':focus-visible'), outline: style.outline,
            outlineWidth: parseFloat(style.outlineWidth), outlineStyle: style.outlineStyle,
            boxShadow: style.boxShadow, color: style.color, background: style.backgroundColor,
            focusContrast: color ? (Math.max(a,b)+.05)/(Math.min(a,b)+.05) : 0};
    }''')
    assert result['focusVisible'], result
    assert ((result['outlineWidth'] >= 2 and result['outlineStyle'] not in ('none', 'hidden'))
            or result['boxShadow'] != 'none'), result
    assert result['focusContrast'] >= 3, result
    expect(target).to_be_in_viewport(ratio=1)
    return result


def save_json(page, path):
    with page.expect_download() as pending:
        activate(page, 'Save configuration')
    pending.value.save_as(path)
    return json.loads(path.read_text())


def reload_json(page, path):
    activate(page, 'Reload configuration')
    popup_ready(page, '.load-dialog')
    page.locator('input[type=file]').set_input_files(path)


def popup_ready(page, selector):
    expect(page.locator(selector)).to_be_visible()
    page.wait_for_function('''selector => {
        const e = document.querySelector(selector);
        return e && getComputedStyle(e).opacity === '1' &&
            e.getAnimations({subtree: true}).every(a => a.playState !== 'running');
    }''', arg=selector)


def set_theme(page, theme):
    target = page.get_by_label('Theme', exact=True)
    keyboard_to(page, target)
    page.keyboard.press('Enter')
    popup_ready(page, '.q-menu')
    page.keyboard.press('Home' if theme == 'Light' else 'End')
    page.keyboard.press('Enter')
    expect(page.locator('body')).to_have_class(re.compile('body--' + theme.lower()))
    expect(target).to_have_attribute('aria-expanded', 'false')
    expect(page.locator('.q-menu')).to_have_count(0)
    expect(target).to_be_focused()


def applied_origins(page):
    return page.locator('.setting-origin').evaluate_all('(nodes) => nodes.map(e => e.dataset.origin)')


def select_view(page, name):
    activate(page, name)
    expect(page.get_by_role('button', name=name, exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('.preview-table' if name == 'Preview' else '.definition-table')).to_be_visible()


def theme_state(page):
    return page.evaluate('''() => ({
        inputs: [...document.querySelectorAll('.properties input, .output-panel input')]
            .map(e => [e.id, e.value, e.disabled, e.getAttribute('aria-invalid'), e.getAttribute('aria-describedby')]),
        origins: [...document.querySelectorAll('.setting-origin')].map(e => e.dataset.origin),
        selected: document.querySelector('.properties .section-title').textContent,
        activeView: document.querySelector('.view-button[aria-pressed=true]').textContent,
        preview: document.querySelector('.preview-table')?.textContent,
        properties: [...document.querySelectorAll('.setting-row, .field-state, .properties .help[role=alert]')].map(e => e.innerText),
        output: [...document.querySelectorAll('.output-controls .q-field, .count-strip')].map(e => e.innerText),
        status: document.querySelector('.status-line').textContent
    })''')


def assert_theme_round_trip(page, theme):
    before = theme_state(page)
    set_theme(page, 'Dark' if theme == 'Light' else 'Light')
    after = theme_state(page)
    assert after == before, {key: [before[key], after[key]] for key in before if before[key] != after[key]}
    set_theme(page, theme)
    assert theme_state(page) == before


def contrast(page, selector):
    readings = page.locator(selector).evaluate_all('''nodes => {
        const rgb = c => c.match(/[\\d.]+/g).map(Number);
        const luminance = c => c.slice(0, 3).map(v => {
            v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        return nodes.filter(e => e.getBoundingClientRect().height && getComputedStyle(e).visibility !== 'hidden')
            .map(e => {
                const fg = getComputedStyle(e).color;
                let parent = e, bg;
                while (parent) {
                    bg = getComputedStyle(parent).backgroundColor;
                    const c = rgb(bg);
                    if (c.length === 3 || c[3] === 1) break;
                    parent = parent.parentElement;
                }
                const a = luminance(rgb(fg)), b = luminance(rgb(bg));
                return {text: e.innerText || e.value || e.getAttribute('aria-label'), fg, bg,
                    ratio: (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
            });
    }''')
    assert readings, selector
    assert all(r['ratio'] >= 4.5 for r in readings), readings
    return readings


def unfocused_borders(page):
    keyboard_to(page, page.get_by_role('button', name='Save configuration', exact=True))
    page.mouse.move(0, 0)
    page.wait_for_function("() => !document.querySelector('.q-field:focus-within, .q-field--focused')")
    page.wait_for_function("() => [...document.querySelectorAll('.q-field')].every(e => e.getAnimations({subtree: true}).every(a => a.playState !== 'running'))")
    readings = page.locator('.q-field--outlined:not(.q-field--disabled):not(.q-field--error) .q-field__control, .primary-action, .context-help > button').evaluate_all('''nodes => {
        const rgb = c => c.match(/[\d.]+/g).map(Number);
        const mix = (fg, bg, alpha) => fg.slice(0, 3).map((v, i) => v * alpha + bg[i] * (1 - alpha));
        const background = e => {
            const chain = [];
            for (let p = e; p; p = p.parentElement) chain.unshift(p);
            return chain.reduce((bg, p) => {
                const c = rgb(getComputedStyle(p).backgroundColor);
                return mix(c, bg, c[3] ?? 1);
            }, [255, 255, 255]);
        };
        const lum = c => c.map(v => {
            v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        }).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
        const contrast = (a, b) => (Math.max(lum(a), lum(b)) + .05) / (Math.min(lum(a), lum(b)) + .05);
        return nodes.filter(e => e.getBoundingClientRect().height).map(e => {
            const field = e.closest('.q-field') || e;
            const direct = e.matches('.context-help > button');
            const pseudo = direct ? getComputedStyle(e) : getComputedStyle(e, '::before');
            const inside = background(e), outside = background(e.parentElement);
            let opacity = Number(pseudo.opacity);
            for (let p = e; p; p = p.parentElement) opacity *= Number(getComputedStyle(p).opacity);
            const edges = ['Top', 'Right', 'Bottom', 'Left'].map(side => {
                const color = rgb(pseudo['border' + side + 'Color']);
                const alpha = (color[3] ?? 1) * opacity;
                return {side, color: pseudo['border' + side + 'Color'], alpha,
                    width: parseFloat(pseudo['border' + side + 'Width']),
                    style: pseudo['border' + side + 'Style'],
                    insideContrast: contrast(mix(color, inside, alpha), inside),
                    outsideContrast: contrast(mix(color, outside, alpha), outside)};
            });
            return {label: field.getAttribute('aria-label') || field.querySelector('[aria-label]')?.getAttribute('aria-label'),
                unfocused: !field.matches(':focus-within, .q-field--focused'),
                pseudoContent: direct ? 'element' : pseudo.content, inside, outside, edges};
        });
    }''')
    assert readings, 'No enabled unfocused control borders measured'
    for reading in readings:
        assert reading['unfocused'] and reading['pseudoContent'] not in ('none', 'normal'), reading
        for edge in reading['edges']:
            assert edge['width'] >= 1 and edge['style'] == 'solid', reading
            assert edge['insideContrast'] >= 3 and edge['outsideContrast'] >= 3, reading
    return readings


def check_help(page, title):
    button = page.get_by_role('button', name=title + ' help', exact=True)
    note = page.locator('#' + button.get_attribute('aria-describedby'))
    assert button.evaluate('''e => {
        const b = e.getBoundingClientRect();
        const c = e.querySelector('.q-btn__content').getBoundingClientRect();
        return Math.abs(b.x + b.width / 2 - c.x - c.width / 2) < 1 &&
            Math.abs(b.y + b.height / 2 - c.y - c.height / 2) < 1;
    }'''), title + ' help content is not centered'
    button.hover()
    expect(note).to_be_visible()
    expect(note).to_be_in_viewport(ratio=1)
    page.mouse.move(0, 0)
    keyboard_to(page, button)
    expect(note).to_be_visible()
    page.keyboard.press('Enter')
    expect(button).to_have_attribute('aria-expanded', 'true')
    page.keyboard.press('Tab')
    expect(note).to_be_visible()  # pinned after leaving keyboard focus
    button.click()
    expect(note).to_be_hidden()
    button.tap()
    expect(note).to_be_visible()
    page.keyboard.press('Escape')
    expect(note).to_be_hidden()
    page.mouse.move(0, 0)


def exercise(page, out, width, height, entry, theme, results):
    prefix = f'{width}x{height}-{entry}-{theme.lower()}'
    observations = {'viewport': [width, height], 'entry': entry, 'theme': theme, 'errors': [], 'focus': []}
    results['cases'].append(observations)
    page.goto(results['base_url'] + '/')
    set_theme(page, theme)
    activate(page, 'Create from scratch' if entry == 'scratch' else 'Start from a sample')
    name = 'value' if entry == 'scratch' else 'length_mm'
    expect(page.get_by_label('Field name', exact=True)).to_have_value(name)
    expect(page.locator('body')).to_have_class(re.compile('body--' + theme.lower()))
    for title in ['Configuration', 'Fields', 'Properties', 'Counts']:
        check_help(page, title)
    expect(page.locator('.action-icon')).to_have_count(3)
    assert page.locator('.action-icon').evaluate_all('''nodes => nodes.every(e =>
        e.complete && e.naturalWidth > 0 && new URL(e.src).origin === location.origin)''')
    summary = page.locator('.assumptions summary')
    keyboard_to(page, summary)
    observations['focus'].append(assert_focus_style(page, summary))
    page.keyboard.press('Enter')
    expect(page.locator('.assumptions')).to_have_attribute('open', '')
    expect(page.locator('.assumptions')).to_contain_text('Relationships between fields are not inferred')
    observations['contrast'] = contrast(page, '.assumptions, .assumptions summary')
    page.keyboard.press('Enter')
    expect(page.locator('.assumptions')).not_to_have_attribute('open', '')
    settings = page.locator('.selected-row .applied-settings')
    original_summary = '0–100 · 0% missing' if entry == 'scratch' else '9.8–12.2 · 0% missing'
    expect(settings).to_have_text(original_summary)
    observations['contrast'] += contrast(page, '.q-field__label, .properties input, .setting-origin, .count-note, .counts-only, .primary-action, .action-toolbar button, .context-help button, .applied-settings, .definition-table th, .pane-title, .session-note')
    observations['unfocused_borders'] = unfocused_borders(page)
    activate(page, 'New table' if entry == 'scratch' else 'Sample table')
    activate(page, name)
    # These assertions must precede any keyboard_to/type_value call.
    expect(page.get_by_label('Field name', exact=True)).to_be_focused()
    observations['field_activation_focus'] = 'Field name'
    observations['focus'].append(assert_focus_style(page, page.get_by_label('Field name', exact=True)))
    page.screenshot(path=out / f'{prefix}-focus-input.png')

    # Link, ordinary button, field button, selector and input keyboard indicators.
    for target, suffix in [
        (page.get_by_role('link', name='Home'), 'link'),
        (page.get_by_role('button', name='Save configuration', exact=True), 'button'),
        (page.get_by_role('button', name=name, exact=True), 'field-button'),
        (page.get_by_label('Type', exact=True), 'selector'),
    ]:
        keyboard_to(page, target)
        observations['focus'].append(assert_focus_style(page, target))
        page.screenshot(path=out / f'{prefix}-focus-{suffix}.png')

    page.keyboard.press('Enter')  # the field-type selector is focused
    popup_ready(page, '.q-menu')
    observations['contrast'] += contrast(page, '.q-menu .q-item')
    page.screenshot(path=out / f'{prefix}-menu.png')
    page.keyboard.press('Escape')
    expect(page.locator('.q-menu')).to_be_hidden()

    type_value(page, 'Minimum', '200')
    expect(settings).to_have_text(original_summary)
    activate(page, 'Apply field')
    observations['errors'].append(assert_error(page, 'Minimum', 'Minimum must not exceed maximum'))
    expect(page.get_by_label('Maximum', exact=True)).to_have_attribute('aria-invalid', 'true')
    assert_error(page, 'Maximum', 'Minimum must not exceed maximum', focused=False)
    minimum_box = page.get_by_label('Minimum', exact=True).bounding_box()
    maximum_box = page.get_by_label('Maximum', exact=True).bounding_box()
    assert abs(minimum_box['y'] - maximum_box['y']) < 1 and maximum_box['x'] > minimum_box['x']
    expect(settings).to_have_text(original_summary)
    expect(page.get_by_label('Minimum', exact=True)).to_have_value('200')
    page.screenshot(path=out / f'{prefix}-range-error.png')
    observations['contrast'] += contrast(page, '.q-field--error [role=alert]')
    assert_theme_round_trip(page, theme)
    type_value(page, 'Minimum', '5')
    activate(page, 'Apply field')
    expect(page.locator('.status-line')).to_contain_text('Field applied')
    expect(page.locator('.properties [aria-invalid=true]')).to_have_count(0)
    expect(page.locator('[data-setting=minimum] .setting-origin')).to_have_text('Edited')
    expect(settings).to_have_text('5–100 · 0% missing' if entry == 'scratch' else '5–12.2 · 0% missing')

    type_value(page, 'Missing %', '150')
    activate(page, 'material' if entry == 'sample' else 'Apply field')
    observations['errors'].append(assert_error(page, 'Missing %', 'between 0 and 100'))
    expect(page.get_by_label('Missing %', exact=True)).to_have_value('150')
    if entry == 'sample':
        expect(page.locator('.properties .section-title')).to_have_text('length_mm')
        expect(page.locator('.properties .help[role=alert]')).to_contain_text('Field switch refused')
    page.screenshot(path=out / f'{prefix}-missing-error.png')
    type_value(page, 'Missing %', '15')
    activate(page, 'material' if entry == 'sample' else 'Apply field')
    if entry == 'sample':
        expect(page.get_by_label('Field name', exact=True)).to_be_focused()
        expect(page.get_by_label('Field name', exact=True)).to_have_value('material')
        expect(page.get_by_label('Minimum', exact=True)).to_be_disabled()
        observations['contrast'] += contrast(page, '.q-field--disabled .q-field__label')
        assert_theme_round_trip(page, theme)
        observations['unfocused_borders'] += unfocused_borders(page)
        activate(page, 'length_mm')
        expect(page.get_by_label('Field name', exact=True)).to_be_focused()
        expect(page.get_by_label('Missing %', exact=True)).to_have_value(re.compile(r'15(?:\.0)?'))
    expect(page.locator('.properties [aria-invalid=true]')).to_have_count(0)
    applied_summary = '5–100 · 15% missing' if entry == 'scratch' else '5–12.2 · 15% missing'
    expect(settings).to_have_text(applied_summary)

    # The preview and its headers stay fixed even when the field draft changes.
    select_view(page, 'Preview')
    check_help(page, 'Preview')
    expect(page.locator('.preview-table tbody tr')).to_have_count(10 if entry == 'sample' else 3)
    expect(page.locator('.preview-warning')).to_contain_text('not generated')
    preview_region = page.get_by_role('region', name='Fixed illustration table; use arrow keys to scroll')
    keyboard_to(page, preview_region)
    observations['focus'].append(assert_focus_style(page, preview_region))
    page.keyboard.press('ArrowDown')
    page.screenshot(path=out / f'{prefix}-preview.png')
    preview = page.locator('.preview-table').inner_text()
    type_value(page, 'Maximum', '20')
    select_view(page, 'Fields')
    expect(settings).to_have_text(applied_summary)
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    select_view(page, 'Preview')
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    assert page.locator('.preview-table').inner_text() == preview
    expect(page.locator('[data-setting=maximum] .draft-mark')).to_be_visible()
    assert_theme_round_trip(page, theme)
    select_view(page, 'Fields')
    if entry == 'sample':
        expect(page.locator('.count-note')).to_contain_text('Retained 0 + New 1,000 = Total 1,000')
        keyboard_to(page, page.get_by_label('Output mode', exact=True))
        page.keyboard.press('Enter')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        expect(page.locator('.count-note')).to_contain_text('Retained 10 + New 990 = Total 1,000')

    count_label = 'Total rows' if entry == 'sample' else 'New rows'
    # Failed Save must neither apply the valid field draft nor download anything.
    applied_before = applied_origins(page)
    definitions_before = page.locator('.definition-table').inner_text()
    downloads = []
    record_download = lambda download: downloads.append(download)
    page.on('download', record_download)
    type_value(page, count_label, '9' if entry == 'sample' else '0')
    activate(page, 'Save configuration')
    observations['errors'].append(assert_error(page, count_label,
                                              'at least 10' if entry == 'sample' else 'whole number'))
    expect(page.locator('.status-line')).to_contain_text('at least 10' if entry == 'sample' else 'whole number')
    assert applied_origins(page) == applied_before
    assert page.locator('.definition-table').inner_text() == definitions_before
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    expect(page.get_by_label(count_label, exact=True)).to_have_value('9' if entry == 'sample' else '0')
    assert downloads == [], 'Failed Save produced a download'
    page.screenshot(path=out / f'{prefix}-save-error.png')
    assert_theme_round_trip(page, theme)
    assert downloads == [], 'Theme change with invalid drafts produced a download'
    page.remove_listener('download', record_download)
    type_value(page, count_label, '1000')
    saved_path = out / f'{prefix}-saved.json'
    saved = save_json(page, saved_path)
    field = saved['table']['fields'][-1]
    assert field['settings']['maximum'] == 20 and field['settings']['missing_percent'] == 15
    assert field['origins']['maximum'] == 'user override'
    assert saved['output'] == {'mode': 'extend' if entry == 'sample' else 'new', 'count': 1000}
    expect(page.locator('[aria-invalid=true]')).to_have_count(0)
    expect(page.locator('.count-note')).to_contain_text('New 990' if entry == 'sample' else 'New 1,000')
    expect(settings).to_have_text('5–20 · 15% missing')
    observations['atomic_save_retry'] = 'passed'
    assert_theme_round_trip(page, theme)
    assert save_json(page, out / f'{prefix}-theme-saved.json') == saved
    observations['unfocused_borders'] += unfocused_borders(page)

    # Import errors must preserve both drafts and the applied provenance.
    type_value(page, 'Maximum', '30')
    type_value(page, 'Field name', 'unfinished_name')
    applied_before = applied_origins(page)
    oversized = new_config(entry)
    oversized['table']['fields'][-1]['settings']['maximum'] = 10**400
    oversized['table']['fields'][-1]['origins']['maximum'] = 'user override'
    oversized_path = out / f'{prefix}-oversized.json'
    oversized_path.write_text(json.dumps(oversized))
    reload_json(page, oversized_path)
    expect(page.locator('.load-dialog [role=alert]')).to_contain_text('Maximum must be a finite number supported')
    expect(page.locator('.load-dialog [role=alert]')).to_be_in_viewport(ratio=1)
    observations['contrast'] += contrast(page, '.load-dialog .section-title, .load-dialog [role=alert], .q-uploader__title')
    page.screenshot(path=out / f'{prefix}-import-error.png')
    activate(page, 'Cancel')
    expect(page.locator('.load-dialog')).to_be_hidden()
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('30')
    expect(page.get_by_label('Field name', exact=True)).to_have_value('unfinished_name')
    assert applied_origins(page) == applied_before
    expect(settings).to_have_text('5–20 · 15% missing')
    observations['oversized_import_preservation'] = 'passed'

    reload_json(page, saved_path)
    expect(page.locator('.status-line')).to_contain_text('Configuration reloaded')
    expect(page.locator('.load-dialog')).to_be_hidden()
    expect(page.get_by_label('Maximum', exact=True)).to_have_value(re.compile(r'20(?:\.0)?'))
    expect(page.get_by_label('Field name', exact=True)).to_have_value(name)
    again = save_json(page, out / f'{prefix}-reloaded.json')
    assert again == saved
    assert (out / f'{prefix}-reloaded.json').read_bytes() == saved_path.read_bytes()
    expect(settings).to_have_text('5–20 · 15% missing')
    observations['applied_settings_summary'] = 'passed: drafts, invalid apply/save/import, apply, save and reload'
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=out / f'{prefix}-recovered.png')
    observations['round_trip'] = 'passed'
    observations['result'] = 'passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/workbook-repair/browser')
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = dict(started_utc=datetime.now(timezone.utc).isoformat(), base_url=args.base_url,
                   python=platform.python_version(), platform=platform.platform(),
                   playwright=version('playwright'),
                   cases=[], external_requests=[], external_websockets=[], page_errors=[])
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel, headless=True)
            results['browser'] = browser.version
            for (width, height), entry, theme in product([(1366, 657), (1280, 800)], ['scratch', 'sample'], ['Light', 'Dark']):
                context = browser.new_context(viewport={'width': width, 'height': height}, accept_downloads=True, has_touch=True)

                def route(request):
                    if urlparse(request.request.url).hostname not in {'127.0.0.1', 'localhost'}:
                        results['external_requests'].append(request.request.url)
                        request.abort()
                    else:
                        request.continue_()

                def websocket(ws):
                    if urlparse(ws.url).hostname not in {'127.0.0.1', 'localhost'}:
                        results['external_websockets'].append(ws.url)
                        ws.close()
                    else:
                        ws.connect_to_server()

                context.route('**/*', route)
                context.route_web_socket('**/*', websocket)
                page = context.new_page()
                page.on('pageerror', lambda e: results['page_errors'].append(str(e)))
                try:
                    exercise(page, out, width, height, entry, theme, results)
                except Exception:
                    page.screenshot(path=out / 'failure.png')
                    raise
                finally:
                    context.close()
                print(f'PASS {width}x{height} {entry} {theme}', flush=True)
            browser.close()
        assert not results['external_requests'], results['external_requests']
        assert not results['external_websockets'], results['external_websockets']
        assert not results['page_errors'], results['page_errors']
        results['result'] = 'passed'
    except Exception:
        results['result'] = 'failed'
        results['failure'] = traceback.format_exc()
        raise
    finally:
        results['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
