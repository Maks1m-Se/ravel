/* Restore an edit action's focus only while that action still owns it. */
(() => {
  let intent = 0;
  for (const event of ['focusin', 'pointerdown', 'keydown', 'input']) {
    document.addEventListener(event, () => { intent += 1; }, true);
  }
  const owns = ticket => {
    if (!ticket || ticket.intent !== intent) return false;
    const action = document.getElementById(ticket.actionId);
    return document.activeElement === document.body || action?.contains(document.activeElement);
  };
  window.ravelEditFocus = {
    capture(actionId) {
      const action = document.getElementById(actionId);
      return action?.contains(document.activeElement) ? {actionId, intent} : null;
    },
    async restore({ticket, identity, fallbacks}) {
      await Vue.nextTick();
      if (!owns(ticket)) return;
      for (const id of [identity, ...fallbacks]) {
        const root = [...document.querySelectorAll('[data-editor]')].find(e => e.dataset.editor === id);
        const input = root?.matches('input, textarea, [role=checkbox], [role=combobox]') ? root : root?.querySelector('input, textarea, [role=combobox]');
        if (!input || input.disabled || input.closest('[aria-disabled=true]') || !input.getClientRects().length) continue;
        input.focus({preventScroll: true});
        const clip = input.closest('.property-body');
        const field = input.closest('.q-field') || input;
        const r = field.getBoundingClientRect(), c = clip?.getBoundingClientRect();
        if (c && (r.top < c.top + 4 || r.bottom > c.bottom - 4)) {
          field.scrollIntoView({block: 'nearest', inline: 'nearest', behavior: 'instant'});
        }
        return;
      }
    },
    async restoreTo(ticket, id) {
      await Vue.nextTick();
      if (owns(ticket)) document.getElementById(id)?.focus({preventScroll:true});
    },
  };
})();
