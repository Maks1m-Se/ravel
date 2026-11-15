"""P1/P2 regression checks against the running app, with unassisted focus assertions."""
from playwright.sync_api import expect

from scripts.check_generator_browser import (
    ROOT, activate, apply, assert_error, choose_rule, generate_table, keyboard_to, type_value,
)
from scripts.pending_browser import pending


def no_error(page, label):
    field = page.get_by_label(label, exact=True)
    expect(field).to_have_attribute('aria-invalid', 'false')
    assert not field.get_attribute('aria-describedby')
    assert field.evaluate("e => [...e.closest('.q-field').querySelectorAll('[role=alert]')].every(e => !e.textContent)")


def scroll_positions(page):
    return page.evaluate('''() => ({x:scrollX, y:scrollY,
        properties:document.querySelector('.property-body').scrollTop})''')


def finish(page, action, label, *, pointer=False, stable_scroll=True):
    if not pointer:
        keyboard_to(page, page.get_by_role('button', name=action, exact=True))
    before = scroll_positions(page)
    was_visible = page.get_by_label(label, exact=True).evaluate('''e => {
        const c = e.closest('.property-body')?.getBoundingClientRect(), r = (e.closest('.q-field') || e).getBoundingClientRect();
        return !c || (r.top >= c.top + 4 && r.bottom <= c.bottom - 4);
    }''') if page.get_by_label(label, exact=True).count() else False
    if pointer:
        page.get_by_role('button', name=action, exact=True).click()
    else:
        page.keyboard.press('Enter')
    expect(page.locator('.status-line')).to_contain_text('Changes applied' if action == 'Apply changes' else 'Unapplied edits discarded')
    pending(page, False)
    # No Tab/focus helper here: this is the focus produced by the application.
    expect(page.get_by_label(label, exact=True)).to_be_focused()
    expect(page.get_by_label(label, exact=True)).to_be_in_viewport(ratio=1)
    after = scroll_positions(page)
    assert (after['x'], after['y']) == (before['x'], before['y'])
    if stable_scroll and was_visible:
        assert after == before


def capture(page, path):
    # A pointer left at a former menu option can hover Rule help after a re-render.
    page.mouse.move(0, 0)
    expect(page.locator('.context-help .help-content:visible')).to_have_count(0)
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)
    page.screenshot(path=path, animations='disabled')


def exercise(page, base, out, viewport, theme):
    prefix = f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-recovery'
    if page.url.startswith(base) and page.evaluate('Boolean(window.ravelUnsaved)'):
        page.once('dialog', lambda dialog: dialog.accept())
    page.goto(base + '/table?theme=' + theme.lower())
    expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
    generate_table(page)
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)

    # Pure table drafts must return to the edited table field, never Column name.
    for label, value in [('Rows', '1001'), ('Seed', '18')]:
        original = page.get_by_label(label, exact=True).input_value()
        type_value(page, label, value)
        finish(page, 'Discard edits', label, pointer=True)
        expect(page.get_by_label(label, exact=True)).to_have_value(original)
        expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_enabled()
        type_value(page, label, value)
        finish(page, 'Apply changes', label)
        expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
        generate_table(page)

    type_value(page, 'Column name', 'reading')
    finish(page, 'Apply changes', 'Column name', pointer=True)
    type_value(page, 'Column name', 'temporary')
    old_id = page.get_by_label('Column name', exact=True).get_attribute('id')
    finish(page, 'Discard edits', 'Column name')
    assert old_id != page.get_by_label('Column name', exact=True).get_attribute('id')
    capture(page, out / f'{prefix}-discard-focus.png')

    choose_rule(page, 'Constant text')
    type_value(page, 'Constant value', 'not applied')
    finish(page, 'Discard edits', 'Column name', stable_scroll=False)
    expect(page.get_by_label('Constant value', exact=True)).to_have_count(0)

    type_value(page, 'Minimum', '200')
    type_value(page, 'Maximum', '20')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    type_value(page, 'Seed', '19')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum', focused=False)
    expect(page.locator('.status-line.error')).to_contain_text('Minimum must not exceed maximum')
    type_value(page, 'Maximum', '150')
    no_error(page, 'Minimum')
    expect(page.locator('.status-line')).to_have_text('')
    pending(page, True)
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    capture(page, out / f'{prefix}-edited-unvalidated.png')
    # A cleared historical error is not validation: the still-inverted range fails again.
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    type_value(page, 'Minimum', '5')
    no_error(page, 'Minimum')
    pending(page, True)
    finish(page, 'Apply changes', 'Minimum')

    type_value(page, 'Minimum', '200')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    type_value(page, 'Maximum', '250')
    no_error(page, 'Minimum')
    expect(page.locator('.status-line')).to_have_text('')
    pending(page, True)
    finish(page, 'Apply changes', 'Maximum')

    type_value(page, 'Minimum', 'invalid')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Enter a whole number')
    type_value(page, 'Maximum', '151')
    # A Maximum edit does not clear a scalar parsing failure in Minimum.
    assert_error(page, 'Minimum', 'Enter a whole number', focused=False)
    activate(page, 'Save recipe')
    expect(page.locator('.status-line.error')).to_contain_text('Apply or discard')
    type_value(page, 'Minimum', 'still invalid')
    no_error(page, 'Minimum')
    expect(page.locator('.status-line.error')).to_contain_text('Apply or discard')
    pending(page, True)
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Enter a whole number')
    capture(page, out / f'{prefix}-still-invalid.png')
    type_value(page, 'Minimum', '6')
    no_error(page, 'Minimum')
    finish(page, 'Apply changes', 'Minimum')

    for label, other, invalid, another_invalid, valid in [
        ('Rows', 'Seed', '0', '-1', '1002'), ('Seed', 'Rows', '-1', '-2', '20'),
    ]:
        type_value(page, label, invalid)
        activate(page, 'Apply changes')
        assert_error(page, label, 'from ')
        type_value(page, other, '21' if other == 'Seed' else '1003')
        assert_error(page, label, 'from ', focused=False)
        type_value(page, label, another_invalid)
        no_error(page, label)
        expect(page.locator('.status-line')).to_have_text('')
        pending(page, True)
        expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
        activate(page, 'Apply changes')
        assert_error(page, label, 'from ')
        type_value(page, label, valid)
        no_error(page, label)
        finish(page, 'Apply changes', label, pointer=True)
    capture(page, out / f'{prefix}-seed-focus.png')

    # Delay only restoration to model a user moving on during a slow response.
    # The real restore implementation must honor that later keyboard interaction.
    type_value(page, 'Column name', 'temperature')
    page.evaluate('''() => {
        const original = window.ravelEditFocus.restore;
        window.ravelEditFocus.restore = async args => {
            window.focusRestoreWaiting = true;
            await new Promise(resolve => { window.releaseFocusRestore = resolve; });
            window.ravelEditFocus.restore = original;
            return original(args);
        };
    }''')
    activate(page, 'Apply changes')
    page.wait_for_function('window.focusRestoreWaiting === true')
    keyboard_to(page, page.get_by_label('Seed', exact=True))
    page.evaluate('window.releaseFocusRestore()')
    expect(page.get_by_label('Seed', exact=True)).to_be_focused()
    # Send another server event to ensure the deferred restoration has completed.
    type_value(page, 'Seed', '22')
    finish(page, 'Discard edits', 'Seed')

    choose_rule(page, 'Exact category counts')
    type_value(page, 'Categories and exact counts', 'A,bad\nB,3')
    activate(page, 'Apply changes')
    assert_error(page, 'Categories and exact counts', 'Enter a whole number')
    type_value(page, 'Rows', '1004')
    expect(page.get_by_label('Categories and exact counts', exact=True)).to_have_attribute('aria-invalid', 'true')
    expect(page.locator('.status-line.error')).to_contain_text('Enter a whole number')
    type_value(page, 'Categories and exact counts', 'A,5\nB,5')
    no_error(page, 'Categories and exact counts')
    activate(page, 'Apply changes')
    assert_error(page, 'Categories and exact counts', 'must total 1,004')
    type_value(page, 'Exact missing count', '994')
    no_error(page, 'Categories and exact counts')
    pending(page, True)
    finish(page, 'Apply changes', 'Exact missing count')

    # Apply re-renders Properties for linked and sample recipes as well as Discard.
    page.once('dialog', lambda dialog: dialog.accept())
    page.goto(base + '/table?theme=' + theme.lower() + '&template=devices')
    expect(page.get_by_label('Column name', exact=True)).to_be_visible()
    type_value(page, 'Column name', 'reviewed_measurement')
    old_id = page.get_by_label('Column name', exact=True).get_attribute('id')
    finish(page, 'Apply changes', 'Column name')
    assert old_id != page.get_by_label('Column name', exact=True).get_attribute('id')
    type_value(page, 'Rows', '1001')
    finish(page, 'Discard edits', 'Rows')

    page.once('dialog', lambda dialog: dialog.accept())
    page.goto(base + '/table?theme=' + theme.lower() + '&open_sample=true')
    dialog = page.locator('.sample-dialog')
    expect(dialog).to_be_visible()
    dialog.locator('input[type=file]').set_input_files(ROOT / 'examples/sample-assisted/ten-rows.csv')
    expect(dialog.locator('.sample-source tbody tr')).to_have_count(10)
    page.get_by_role('button', name='Use sample', exact=True).click()
    expect(dialog).to_be_hidden()
    type_value(page, 'Column name', 'reviewed_sample')
    old_id = page.get_by_label('Column name', exact=True).get_attribute('id')
    finish(page, 'Apply changes', 'Column name')
    assert old_id != page.get_by_label('Column name', exact=True).get_attribute('id')

    return dict(workflow='recovery', viewport=viewport, theme=theme, result='passed',
        assertions='unassisted Apply/Discard focus; pure Rows/Seed; stable identity across field re-render; removed-field fallback; no scroll jump or late focus steal; related and independent errors/ARIA/status; unvalidated drafts/export block; full invalid revalidation; sample/linked refresh')
