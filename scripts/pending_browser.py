"""Exercise the Apply/Discard contract on the actual running workbench."""
from playwright.sync_api import expect

from scripts.check_generator_browser import (
    activate, apply, assert_error, contrast, download, generate_table, keyboard_to,
    layout_regressions, set_theme, type_value,
)


def pending(page, value):
    area=page.locator('.edit-actions')
    expect(area).to_have_attribute('data-pending',str(value).lower())
    expect(area.locator('.pending-note')).to_have_text('Unapplied changes' if value else 'All changes applied')
    for name in ['Apply changes','Discard edits']:
        button=page.get_by_role('button',name=name,exact=True)
        (expect(button).to_be_enabled if value else expect(button).to_be_disabled)()
        expect(button).to_be_in_viewport(ratio=1)
    style=area.evaluate('(e)=>{const s=getComputedStyle(e);return {border:s.borderTopColor,background:s.backgroundColor}}')
    if value:
        assert style['border'] not in ['transparent','rgba(0, 0, 0, 0)']
    else:
        assert style['border'] in ['transparent','rgba(0, 0, 0, 0)']
    return style


def exercise(page,base,out,viewport,theme):
    prefix=f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-pending'
    if page.url.startswith(base) and page.evaluate('Boolean(window.ravelUnsaved)'):
        page.once('dialog',lambda dialog:dialog.accept())
    page.goto(base+'/table?theme='+theme.lower())
    expect(page.get_by_label('Column name',exact=True)).to_have_value('value')
    generate_table(page)
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)
    page.screenshot(path=out/f'{prefix}-unchanged.png')
    pending(page,False)
    download(page,'Save recipe',out/f'{prefix}-original.recipe.json')
    download(page,'Export CSV',out/f'{prefix}-original.csv')
    page.wait_for_function('window.ravelUnsaved === false')
    check=page.get_by_role('button',name='Session help',exact=True)
    keyboard_to(page,check)
    page.keyboard.press('Enter')
    expect(page.locator('.action-toolbar .help-content')).to_contain_text('Exact quotas')
    expect(page.locator('.action-toolbar .help-content')).not_to_contain_text('not supported yet')
    page.keyboard.press('Escape')
    page.evaluate('''() => {
        window.pendingAnnouncements=[];
        const e=document.querySelector('.pending-announcement');
        let last=e.textContent;
        new MutationObserver(()=>{
            if(e.textContent!==last) {last=e.textContent; window.pendingAnnouncements.push(last);}
        }).observe(e,{childList:true,characterData:true,subtree:true});
    }''')
    unchanged=page.locator('.edit-actions').bounding_box()
    type_value(page,'Column name','reading')
    pending_style=pending(page,True)
    note_contrast=contrast(page,'.pending-note')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    expect(page.locator('[data-setting=name] .draft-mark')).to_be_visible()
    assert page.locator('.edit-actions').bounding_box()==unchanged
    page.screenshot(path=out/f'{prefix}-column.png')
    type_value(page,'Column name','value')
    pending(page,False)
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()
    page.wait_for_function('window.ravelUnsaved === false')
    page.wait_for_function('window.pendingAnnouncements.length === 2')
    type_value(page,'Column name','reading')
    type_value(page,'Maximum','20')
    type_value(page,'Minimum','200')
    pending(page,True)
    layout_regressions(page,viewport,theme)
    pending(page,True)
    checkbox=page.get_by_role('checkbox',name='Require unique values',exact=True)
    keyboard_to(page,checkbox)
    expect(checkbox).to_be_in_viewport(ratio=1)
    assert checkbox.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}')
    activate(page,'Apply changes')
    assert_error(page,'Minimum','Minimum must not exceed maximum')
    pending(page,True)
    expect(page.get_by_label('Minimum',exact=True)).to_be_focused()
    expect(page.locator('.pending-announcement')).to_have_attribute('aria-live','polite')
    expect(page.locator('.pending-announcement')).to_have_attribute('aria-atomic','true')
    # Repeated edits, theme/view changes and validation do not repeat the announcement.
    assert len(page.evaluate('window.pendingAnnouncements'))==3
    page.screenshot(path=out/f'{prefix}-invalid.png')
    type_value(page,'Minimum','5')
    apply(page)
    pending(page,False)
    expect(page.locator('.result-state')).to_contain_text('Out of date · Generate to update')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    # Prior data stays visibly stale; no placeholder result replaces it.
    activate(page,'Preview')
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)
    page.screenshot(path=out/f'{prefix}-applied-stale.png')
    generate_table(page)
    pending(page,False)
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()
    type_value(page,'Rows','0')
    pending(page,True)
    expect(page.locator('[data-setting] .draft-mark:visible')).to_have_count(0)
    expect(page.get_by_label('Rows',exact=True)).to_be_focused()
    page.screenshot(path=out/f'{prefix}-table.png')
    activate(page,'Apply changes')
    assert_error(page,'Rows','from 1 to 100,000')
    pending(page,True)
    type_value(page,'Rows','1000')
    pending(page,False)
    expect(page.locator('.output-panel [aria-invalid=true]')).to_have_count(0)
    expect(page.locator('.status-line.error')).to_have_count(0)
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()
    type_value(page,'Seed','18')
    pending(page,True)
    activate(page,'Discard edits')
    pending(page,False)
    expect(page.get_by_label('Seed',exact=True)).to_have_value('17')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()
    type_value(page,'Rows','1001')
    pending(page,True)
    apply(page)
    pending(page,False)
    expect(page.locator('.result-state')).to_contain_text('Out of date')
    generate_table(page)
    expect(page.locator('.result-state')).to_contain_text('1,001')
    pending(page,False)
    page.screenshot(path=out/f'{prefix}-regenerated.png')
    return dict(workflow='pending',viewport=viewport,theme=theme,result='passed',
                pending_style=pending_style,note_contrast=note_contrast,announcements=page.evaluate('window.pendingAnnouncements'),
                assertions='unchanged disabled; column/table-only pending; exact revert; invalid Apply/recovery; Apply/Discard; theme/view/resize; keyboard focus; stable reachable actions; transition-only polite announcements; stale export; updated Session help')
