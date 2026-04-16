# Plan 002: Toast Notification System

**Date:** 2026-04-16  
**Status:** Pending

## Problem

Currently notifications use two different mechanisms:
1. **`setStatus(msg, type)`** — renders text inline AFTER the "Procesar Imágenes"/"Abrir Carpeta Output" buttons, with only color changes (green/red). No auto-dismiss, no animation, easy to miss.
2. **`showModal(html)`** — renders a blocking modal dialog for both errors AND informational messages (about, update check, etc.). Overkill for simple success/error messages.

This creates UX issues:
- Success/error messages appear at the bottom of the page, easily overlooked
- Simple notifications like "Preset guardado" require dismissing a modal
- No consistency: some things use `setStatus`, some use `showModal`, some use the update-banner
- No auto-dismiss or animation on any notification

## Solution: Toast Notification System

Create a unified `Toast` service in pure JS/CSS that replaces ALL `setStatus()` calls and most `showModal()` error calls with floating toast notifications. The modal system stays for confirmations, about dialogs, and rich content that genuinely needs user interaction.

### Toast Types
- **success** — green accent, auto-dismiss 3s
- **error** — red accent, auto-dismiss 5s  
- **info** — blue accent, auto-dismiss 3s
- **warning** — yellow accent, auto-dismiss 4s

### Toast Behavior
- Stack from top-right corner of the viewport
- Slide-in animation (from right)
- Auto-dismiss with progress bar
- Manual dismiss via click
- Max 3 visible toasts, older ones dismissed

## Notification Mapping: Current → Toast

| # | Current Mechanism | Current Message | New Mechanism | Toast Type |
|---|---|---|---|---|
| 1 | setStatus | "Preset eliminado" | toast.show() | success |
| 2 | setStatus | "Preset 'X' aplicado" | toast.show() | success |
| 3 | setStatus | "" (clear) | toast.clearAll() → only if needed | - |
| 4 | setStatus | process error | toast.show() | error |
| 5 | setStatus | completed with errors | toast.show() | error |
| 6 | setStatus | "No se encontraron imágenes..." | toast.show() | error |
| 7 | setStatus | completed successfully | toast.show() | success |
| 8 | setStatus | "Configuración restablecida" | toast.show() | success |
| 9 | setStatus | "Receta 'X' guardada" | toast.show() | success |
| 10 | setStatus | "Preset guardado exitosamente" | toast.show() | success |
| 11 | setStatus | "Preset cargado" | toast.show() | success |
| 12 | showModal | "Error: {error}" (delete preset) | toast.show() | error |
| 13 | showModal | "Error al cargar preset: {error}" | toast.show() | error |
| 14 | showModal | "Buscando actualizaciones..." | **KEEP showModal** (loading state) | - |
| 15 | showModal | Update available (HTML rich) | **KEEP showModal** (rich content + link) | - |
| 16 | showModal | "Ya tienes la última versión" | toast.show() | info |
| 17 | showModal | "No se pudo verificar actualizaciones" | toast.show() | error |
| 18 | showModal | About dialog (HTML rich) | **KEEP showModal** (rich content) | - |
| 19 | showModal | About fallback (HTML) | **KEEP showModal** | - |
| 20 | showModal | "Error al guardar receta: {error}" | toast.show() | error |
| 21 | showModal | "Error al guardar preset: {error}" | toast.show() | error |
| 22 | showModal | "Error al cargar preset: {error}" | toast.show() | error |

**Summary:** 18 notifications migrate to toast, 4 stay as modal (loading, update available, about ×2).

The update-banner (auto-check) stays as-is — it's a persistent banner, not a toast.

## Architecture

### Files Changed

| Agent | Files Owned | Changes |
|-------|------------|---------|
| **frontend** | `ui/app.js`, `ui/toast.js` (NEW) | Create toast service, replace setStatus/showModal calls |
| **frontend-styles** | `ui/style.css`, `ui/index.html` | Toast CSS, remove status-msg HTML, remove status-msg CSS |

## Task Breakdown

### TASK-001: Create toast service (`ui/toast.js`)
**Owner:** frontend  
**Files:** `ui/toast.js` (NEW)  
**Depends:** none  
**Done when:**
- `Toast` class with `show(message, type)` method exists
- Types: `success`, `error`, `info`, `warning`
- Auto-dismiss: success=3s, error=5s, info=3s, warning=4s
- Stacking from top-right with slide-in animation
- Max 3 visible toasts, older ones auto-dismissed
- Click to dismiss
- Progress bar showing time remaining
- `clearAll()` method
- Adds `<script src="toast.js">` to index.html BEFORE app.js

### TASK-002: Add toast CSS styles (`ui/style.css`)
**Owner:** frontend-styles  
**Files:** `ui/style.css`  
**Depends:** none  
**Done when:**
- `.toast-container` styles: fixed top-right, z-index 300, flex column
- `.toast` styles: card-like, rounded, padding, shadow, slide-in keyframe
- `.toast-success`, `.toast-error`, `.toast-info`, `.toast-warning` color variants
- `.toast-progress` bar styles
- `.toast-close` button styles
- Remove `.status-msg` and its variants (they will no longer be used)
- Remove the `#status-msg` div from `ui/index.html`

### TASK-003: Remove `#status-msg` div from HTML (`ui/index.html`)
**Owner:** frontend-styles  
**Files:** `ui/index.html`  
**Depends:** none  
**Done when:**
- `<div id="status-msg" class="status-msg"></div>` removed from HTML
- `<script src="toast.js"></script>` added before `<script src="app.js"></script>`

### TASK-004: Replace `setStatus()` calls with `toast.show()` in `app.js`
**Owner:** frontend  
**Files:** `ui/app.js`  
**Depends:** TASK-001, TASK-002  
**Done when:**
- All 11 `setStatus()` calls replaced with appropriate `toast.show(msg, type)`
- `setStatus` function removed from app.js
- Line 393 (`setStatus("")`) → removed entirely (clearing is no longer needed)

### TASK-005: Replace error `showModal()` calls with `toast.show()` in `app.js`
**Owner:** frontend  
**Files:** `ui/app.js`  
**Depends:** TASK-001  
**Done when:**
- showModal calls for simple errors/confirmations replaced with toast.show():
  - Delete preset error → toast.show(msg, 'error')
  - Load preset error → toast.show(msg, 'error')
  - Save preset error → toast.show(msg, 'error')
  - Import preset error → toast.show(msg, 'error')
  - Save named preset error → toast.show(msg, 'error')
  - Update check failed → toast.show(msg, 'error')
  - "Ya tienes la última versión" → toast.show(msg, 'info')
- showModal calls KEPT for rich content:
  - "Buscando actualizaciones..." (loading state)
  - Update available dialog (has download link)
  - About dialog (has version info)

### TASK-006: Add toast container div to `ui/index.html`
**Owner:** frontend-styles  
**Files:** `ui/index.html`  
**Depends:** none  
**Done when:**
- `<div id="toast-container" class="toast-container"></div>` added at end of body, before scripts

## Execution Order

Since agents can't touch the same file simultaneously, we need:

**Phase 1 (parallel):**
- Agent frontend: Create `ui/toast.js` (TASK-001)
- Agent frontend-styles: Add toast CSS to `ui/style.css` (TASK-002)

**Phase 2 (parallel, after Phase 1):**
- Agent frontend: Update `ui/app.js` (TASK-004 + TASK-005)
- Agent frontend-styles: Update `ui/index.html` (TASK-003 + TASK-006)

**Phase 3:**
- Team Lead: Merge all, verify no conflicts, run `make test`

## Toast.js Implementation Spec

```javascript
class Toast {
  constructor(containerId = 'toast-container') {
    this.container = document.getElementById(containerId);
    this.maxVisible = 3;
    this.durations = { success: 3000, error: 5000, info: 3000, warning: 4000 };
  }

  show(message, type = 'info') {
    const toast = this._createToast(message, type);
    this.container.appendChild(toast);
    this._enforceMax();
    requestAnimationFrame(() => toast.classList.add('toast-visible'));
    const duration = this.durations[type] || 3000;
    const timer = setTimeout(() => this._dismiss(toast), duration);
    toast._timer = timer;
    toast._startTime = Date.now();
    toast._duration = duration;
    this._startProgress(toast);
  }

  _createToast(message, type) {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
      <div class="toast-content">${message}</div>
      <button class="toast-close">&times;</button>
      <div class="toast-progress"></div>
    `;
    el.querySelector('.toast-close').addEventListener('click', () => this._dismiss(el));
    return el;
  }

  _dismiss(toast) {
    if (toast._dismissed) return;
    toast._dismissed = true;
    clearTimeout(toast._timer);
    toast.classList.remove('toast-visible');
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }

  _enforceMax() {
    const toasts = this.container.querySelectorAll('.toast');
    while (toasts.length > this.maxVisible) {
      this._dismiss(toasts[0]);
      toasts[0] = null; // help GC
    }
  }

  _startProgress(toast) {
    const bar = toast.querySelector('.toast-progress');
    if (!bar) return;
    const update = () => {
      if (toast._dismissed) return;
      const elapsed = Date.now() - toast._startTime;
      const pct = Math.max(0, 100 - (elapsed / toast._duration) * 100);
      bar.style.width = pct + '%';
      if (pct > 0) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  clearAll() {
    this.container.querySelectorAll('.toast').forEach(t => this._dismiss(t));
  }
}

window.toast = new Toast();
```

## Toast CSS Spec

```css
/* Toast Notifications */
.toast-container {
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 300;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: none;
    max-width: 380px;
}

.toast {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--card);
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    font-size: 13px;
    line-height: 1.5;
    pointer-events: auto;
    transform: translateX(120%);
    opacity: 0;
    transition: transform 0.3s ease, opacity 0.3s ease;
    position: relative;
    overflow: hidden;
    border-left: 4px solid var(--accent);
}

.toast-visible {
    transform: translateX(0);
    opacity: 1;
}

.toast-exit {
    transform: translateX(120%);
    opacity: 0;
}

.toast-content { flex: 1; }

.toast-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: var(--text-secondary);
    padding: 0 2px;
    line-height: 1;
}

.toast-close:hover { color: var(--text); }

.toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: var(--accent);
    opacity: 0.4;
    transition: width 0.1s linear;
}

.toast-success { border-left-color: var(--success); }
.toast-error { border-left-color: var(--danger); }
.toast-info { border-left-color: var(--accent); }
.toast-warning { border-left-color: #ffc107; }

.toast-success .toast-progress { background: var(--success); }
.toast-error .toast-progress { background: var(--danger); }
.toast-info .toast-progress { background: var(--accent); }
.toast-warning .toast-progress { background: #ffc107; }
```
