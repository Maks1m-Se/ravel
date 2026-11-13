/* Roving focus is confined to explicit composites; text editors keep their keys. */
(() => {
  const groups = '[data-ravel-roving]';
  const visible = e => e.getClientRects().length && !e.disabled && e.getAttribute('aria-disabled') !== 'true';
  const items = group => [...group.querySelectorAll('[data-ravel-item], :scope > button, :scope > a[href]')]
    .filter(e => e.closest(groups) === group && visible(e));
  function sync(group) {
    const all = items(group);
    const active = all.find(e => e === document.activeElement || e.contains(document.activeElement));
    const selected = all.find(e => e.getAttribute('aria-selected') === 'true');
    const previous = all.find(e => e.getAttribute('tabindex') === '0');
    const entry = active || (['fields', 'tabs'].includes(group.dataset.ravelRoving) ? selected : previous) || all[0];
    for (const e of all) e.setAttribute('tabindex', e === entry ? '0' : '-1');
  }
  const refresh = () => {
    document.querySelectorAll(groups).forEach(sync);
    for (const root of document.querySelectorAll('.q-uploader[data-file-label]')) {
      const button = root.querySelector('a[role=button]:has(input[type=file])');
      if (button) button.setAttribute('aria-label', root.dataset.fileLabel);
    }
  };
  document.addEventListener('focusin', e => {
    const group = e.target.closest(groups);
    if (group) sync(group);
  });
  document.addEventListener('focusout', e => {
    const group = e.target.closest(groups);
    if (group && !group.contains(e.relatedTarget)) queueMicrotask(() => sync(group));
  });
  document.addEventListener('keydown', e => {
    if (e.defaultPrevented || e.isComposing || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
    if (e.target.closest('input, textarea, select, [contenteditable=true], [role=combobox], [role=slider], [role=separator]')) return;
    const group = e.target.closest(groups);
    if (!group) return;
    const all = items(group), current = all.findIndex(item => item === e.target || item.contains(e.target));
    if (current < 0) return;
    if (group.dataset.ravelRoving === 'fields' && ['Enter', ' '].includes(e.key)) {
      e.preventDefault();
      if (!e.repeat) all[current].click();
      return;
    }
    const vertical = ['fields', 'vertical'].includes(group.dataset.ravelRoving);
    let next;
    if (e.key === (vertical ? 'ArrowDown' : 'ArrowRight')) next = (current + 1) % all.length;
    if (e.key === (vertical ? 'ArrowUp' : 'ArrowLeft')) next = (current - 1 + all.length) % all.length;
    if (e.key === 'Home') next = 0;
    if (e.key === 'End') next = all.length - 1;
    if (next === undefined) return;
    e.preventDefault();
    all[next].focus({preventScroll: true});
    all[next].scrollIntoView({block: 'nearest', inline: 'nearest'});
  });
  new MutationObserver(refresh).observe(document.documentElement, {
    subtree: true, childList: true, attributes: true,
    attributeFilter: ['disabled', 'aria-disabled', 'aria-selected', 'style'],
  });
  refresh();
})();
