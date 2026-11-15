
window.ravelWorkspaceLayout = {
    grid: () => document.querySelector('.workbook-grid'),
    limits(grid) {
        const minimumWorkspace = parseFloat(getComputedStyle(grid).getPropertyValue('--workspace-min'));
        const available = grid.clientWidth - grid.querySelector('.navigator').getBoundingClientRect().width
            - grid.querySelector('.workspace-divider').getBoundingClientRect().width;
        return {minimum: 300, maximum: Math.max(300, Math.min(560, available - minimumWorkspace))};
    },
    width(grid) { return grid.querySelector('.properties').getBoundingClientRect().width; },
    preference(grid) { return parseFloat(grid.style.getPropertyValue('--properties-width')) || 312; },
    sync(grid) {
        const divider = grid.querySelector('.workspace-divider'), width = Math.round(this.width(grid));
        divider.setAttribute('aria-valuemax', Math.floor(this.limits(grid).maximum));
        divider.setAttribute('aria-valuenow', width);
        divider.setAttribute('aria-valuetext', 'Properties ' + width + ' pixels');
    },
    init() {
        this.observer?.disconnect();
        const grid = this.grid();
        this.observer = new ResizeObserver(() => this.sync(grid));
        this.observer.observe(grid);
        this.observer.observe(grid.querySelector('.properties'));
        this.sync(grid);
    },
    prefer(grid, width) {
        grid.style.setProperty('--properties-width', width + 'px');
        this.sync(grid);
    },
    set(grid, width) {
        const limits = this.limits(grid);
        width = Math.round(Math.max(limits.minimum, Math.min(limits.maximum, width)));
        this.prefer(grid, width);
    },
    start(event) {
        if (event.button !== 0 || !event.isPrimary) return;
        event.preventDefault();
        const divider = event.currentTarget, grid = divider.closest('.workbook-grid');
        divider.focus();
        divider._resizeStart = {x: event.clientX, width: this.width(grid),
                                preference: this.preference(grid), pointer: event.pointerId};
        grid.dataset.resizing = 'true';
        divider.setPointerCapture(event.pointerId);
    },
    move(event) {
        const divider = event.currentTarget, start = divider._resizeStart;
        if (start && event.pointerId === start.pointer)
            this.set(divider.closest('.workbook-grid'), start.width + start.x - event.clientX);
    },
    finish(event, cancel = false) {
        const divider = event.currentTarget, start = divider._resizeStart;
        if (!start) return;
        divider._resizeStart = null;
        const grid = divider.closest('.workbook-grid');
        if (cancel) this.prefer(grid, start.preference);
        grid.dataset.resizing = 'false';
        if (divider.hasPointerCapture(start.pointer)) divider.releasePointerCapture(start.pointer);
    },
    key(event) {
        if (event.altKey || event.ctrlKey || event.metaKey) return;
        const grid = event.currentTarget.closest('.workbook-grid');
        const step = event.shiftKey ? 40 : 10, limits = this.limits(grid);
        const widths = {ArrowLeft: this.width(grid) + step, ArrowRight: this.width(grid) - step,
                        Home: limits.minimum, End: limits.maximum};
        if (event.key === 'Escape' && event.currentTarget._resizeStart) {
            event.preventDefault(); this.finish(event, true);
        } else if (event.key in widths) {
            event.preventDefault(); this.set(grid, widths[event.key]);
        }
    },
    reset() { const grid = this.grid(); if (grid) this.prefer(grid, 312); }
};
