# Plan 001: Fix Sidebar & Dropdown Issues

**Date:** 2026-04-16  
**Status:** Pending

## Problems Identified

### 1. "Nueva Receta" button does nothing
- **File:** `ui/index.html:17` — `btn-add-preset` button exists in HTML
- **File:** `ui/app.js` — NO event listener attached to `btn-add-preset`
- **Backend:** `app/api.py` already has `save_named_preset(name, config_dict)` which saves a preset by name
- **Fix:** Add click handler to `btn-add-preset` that shows a custom modal with text input for preset name, then calls `pywebview.api.save_named_preset(name, config)` and refreshes the presets list.

### 2. No spacing between "Mis Recetas" and "Configuración" sections, all sections should be sticky
- **File:** `ui/style.css:44-51` — `.sidebar-section` has `position: sticky; top: 16px` on EACH section individually, but there's no gap between them.
- **Fix:**
  - Move `position: sticky; top: 16px; align-self: flex-start;` from `.sidebar-section` to `.sidebar`
  - Add `display: flex; flex-direction: column; gap: 12px; max-height: 100vh; overflow-y: auto;` to `.sidebar`
  - This makes the entire sidebar sticky as a unit with proper spacing between sections

### 3. Import/Export preset buttons in dropdown menu are broken
- **File:** `ui/index.html:48-49` — Dropdown has `menu-load-preset` and `menu-save-preset` IDs
- **File:** `ui/app.js:530-558` — Event listeners attached to `btn-save-preset` and `btn-load-preset` (IDs that DON'T EXIST in HTML)
- **Result:** Import/export buttons in dropdown are completely non-functional
- **Fix:** Change JS to use correct IDs: `menu-save-preset` and `menu-load-preset`
- **Additional fix:** The load handler uses `select_input_directory()` (folder dialog) — should use a proper file dialog for JSON files. Add `select_preset_file()` method to `api.py`.

### 4. (Bonus) Duplicate CSS rule
- **File:** `ui/style.css` lines 153-161 and 163-171 — duplicate `.header` rule block
- Remove the duplicate

## Implementation Steps

### Step 1: Add save-preset modal to `ui/index.html`
Add a modal with a text input for preset name, before the existing modal overlay:

```html
<div id="save-preset-overlay" class="modal-overlay" style="display:none;">
    <div class="modal">
        <h3 style="margin-bottom:12px;font-size:15px;">Guardar Receta</h3>
        <input type="text" id="save-preset-name" class="save-preset-input" placeholder="Nombre de la receta" autofocus>
        <div class="modal-actions">
            <button id="save-preset-cancel" class="btn-cancel">Cancelar</button>
            <button id="save-preset-confirm" class="modal-close">Guardar</button>
        </div>
    </div>
</div>
```

### Step 2: Add CSS styles for new modal and fix sidebar
**In `ui/style.css`:**

- Remove duplicate `.header` block (lines 163-171)
- Remove `position: sticky; top: 16px;` from `.sidebar-section`
- Update `.sidebar` to:
```css
.sidebar {
    width: 240px;
    flex-shrink: 0;
    position: sticky;
    top: 16px;
    align-self: flex-start;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 100vh;
    overflow-y: auto;
}
```
- Add styles for `.save-preset-input` and `.modal-actions` / `.btn-cancel`

### Step 3: Fix JS event handlers in `ui/app.js`
- Change `getElementById("btn-save-preset")` → `getElementById("menu-save-preset")`
- Change `getElementById("btn-load-preset")` → `getElementById("menu-load-preset")`
- Add `btn-add-preset` click handler that opens the save-preset modal
- Add modal confirm/cancel handlers
- Update load preset handler to close dropdown and use `select_preset_file()`

### Step 4: Add `select_preset_file()` to `app/api.py`
```python
def select_preset_file(self) -> str | None:
    if self.window is None:
        return None
    result = self.window.create_file_dialog(
        dialog_type=10,  # OPEN_DIALOG
        file_types=("JSON Files (*.json)",),
    )
    if result and len(result) > 0:
        return result[0]
    return None
```

## Files to Modify

1. `ui/index.html` — Add save preset modal with text input
2. `ui/style.css` — Fix sidebar sticky/gap, remove duplicate `.header`, add modal styles
3. `ui/app.js` — Add `btn-add-preset` handler, fix dropdown IDs, add save preset modal logic
4. `app/api.py` — Add `select_preset_file()` method
