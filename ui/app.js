// Transform definitions
const TRANSFORMS = {
    flip: {
        title: "Flip",
        desc: "Voltea la imagen horizontal o verticalmente",
        enabledKey: "flip_enabled",
        params: (cfg) => `
            <label>Dirección:</label>
            <select data-key="flip_direction">
                <option value="horizontal" ${cfg.flip_direction === "horizontal" ? "selected" : ""}>Horizontal</option>
                <option value="vertical" ${cfg.flip_direction === "vertical" ? "selected" : ""}>Vertical</option>
            </select>
        `,
    },
    rotate: {
        title: "Rotate",
        desc: "Rota la imagen los grados indicados",
        enabledKey: "rotate_enabled",
        params: (cfg) => `
            <label>Grados:</label>
            <input type="number" data-key="rotate_degrees" value="${cfg.rotate_degrees}" min="-360" max="360" style="width:60px">
        `,
    },
    crop: {
        title: "Safe Square Crop",
        desc: "Recorte cuadrado que elimina esquinas transparentes",
        enabledKey: "crop_enabled",
        params: () => "",
    },
    resize: {
        title: "Resize",
        desc: "Redimensiona la imagen por porcentaje o dimensiones",
        enabledKey: "resize_enabled",
        params: (cfg) => `
            <label>Modo:</label>
            <select data-key="resize_mode" class="resize-mode-select">
                <option value="percentage" ${cfg.resize_mode === "percentage" ? "selected" : ""}>Porcentaje</option>
                <option value="dimensions" ${cfg.resize_mode === "dimensions" ? "selected" : ""}>Dimensiones</option>
            </select>
            <span class="resize-percentage-fields" style="display:${cfg.resize_mode === "percentage" ? "contents" : "none"}">
                <label>%:</label>
                <input type="number" data-key="resize_percentage" value="${cfg.resize_percentage}" min="10" max="500" style="width:60px">
            </span>
            <span class="resize-dimensions-fields" style="display:${cfg.resize_mode === "dimensions" ? "contents" : "none"}">
                <label>Ancho:</label>
                <input type="number" data-key="resize_width" value="${cfg.resize_width}" min="0" style="width:70px">
                <label>Alto:</label>
                <input type="number" data-key="resize_height" value="${cfg.resize_height}" min="0" style="width:70px">
                <label>
                    <input type="checkbox" data-key="resize_keep_aspect" ${cfg.resize_keep_aspect ? "checked" : ""}> Aspecto
                </label>
            </span>
        `,
    },
    brightness: {
        title: "Brightness",
        desc: "Ajusta el brillo de la imagen",
        enabledKey: "brightness_enabled",
        params: (cfg) => `
            <label>Factor:</label>
            <input type="range" data-key="brightness_factor" min="0.5" max="2.0" step="0.05" value="${cfg.brightness_factor}">
            <span class="range-val">${Number(cfg.brightness_factor).toFixed(2)}</span>
        `,
    },
    contrast: {
        title: "Contrast",
        desc: "Ajusta el contraste de la imagen",
        enabledKey: "contrast_enabled",
        params: (cfg) => `
            <label>Factor:</label>
            <input type="range" data-key="contrast_factor" min="0.5" max="2.0" step="0.05" value="${cfg.contrast_factor}">
            <span class="range-val">${Number(cfg.contrast_factor).toFixed(2)}</span>
        `,
    },
    sharpness: {
        title: "Sharpness",
        desc: "Ajusta la nitidez de la imagen",
        enabledKey: "sharpness_enabled",
        params: (cfg) => `
            <label>Factor:</label>
            <input type="range" data-key="sharpness_factor" min="0.0" max="3.0" step="0.05" value="${cfg.sharpness_factor}">
            <span class="range-val">${Number(cfg.sharpness_factor).toFixed(2)}</span>
        `,
    },
};

let config = {};
let polling = null;

// Wait for pywebview API
window.addEventListener("pywebviewready", init);

async function init() {
    config = await pywebview.api.get_config();
    renderConfig();
    refreshFileCount();
}

function renderConfig() {
    document.getElementById("input-dir").value = config.input_dir || "input_files";
    document.getElementById("output-dir").value = config.output_dir || "output_files";
    document.getElementById("webp-quality").value = config.webp_quality || 90;
    renderTransforms();
}

function renderTransforms() {
    const list = document.getElementById("transforms-list");
    list.innerHTML = "";

    const order = config.transform_order || Object.keys(TRANSFORMS);

    for (const key of order) {
        const t = TRANSFORMS[key];
        if (!t) continue;
        const enabled = config[t.enabledKey];

        const card = document.createElement("div");
        card.className = `transform-card ${enabled ? "" : "disabled"}`;
        card.dataset.key = key;

        card.innerHTML = `
            <div class="card-header">
                <span class="drag-handle">&#10303;</span>
                <input type="checkbox" data-enabled-key="${t.enabledKey}" ${enabled ? "checked" : ""}>
                <span class="card-title">${t.title}</span>
            </div>
            ${t.params(config) ? `<div class="card-params">${t.params(config)}</div>` : ""}
            ${t.desc ? `<div class="card-desc">${t.desc}</div>` : ""}
        `;

        list.appendChild(card);
    }

    // Init Sortable
    if (window._sortable) window._sortable.destroy();
    window._sortable = new Sortable(list, {
        handle: ".drag-handle",
        animation: 150,
        ghostClass: "sortable-ghost",
        chosenClass: "sortable-chosen",
        onEnd: onReorder,
    });

    bindCardEvents();
}

function bindCardEvents() {
    // Checkboxes
    document.querySelectorAll(".transform-card input[type='checkbox'][data-enabled-key]").forEach((cb) => {
        cb.addEventListener("change", () => {
            config[cb.dataset.enabledKey] = cb.checked;
            const card = cb.closest(".transform-card");
            card.classList.toggle("disabled", !cb.checked);
            saveConfig();
        });
    });

    // Selects
    document.querySelectorAll(".card-params select[data-key]").forEach((sel) => {
        sel.addEventListener("change", () => {
            const key = sel.dataset.key;
            config[key] = sel.value;
            // Toggle resize mode fields
            if (key === "resize_mode") {
                const card = sel.closest(".transform-card");
                const pct = card.querySelector(".resize-percentage-fields");
                const dim = card.querySelector(".resize-dimensions-fields");
                if (pct) pct.style.display = sel.value === "percentage" ? "contents" : "none";
                if (dim) dim.style.display = sel.value === "dimensions" ? "contents" : "none";
            }
            saveConfig();
        });
    });

    // Number inputs
    document.querySelectorAll(".card-params input[type='number'][data-key]").forEach((inp) => {
        inp.addEventListener("change", () => {
            config[inp.dataset.key] = Number(inp.value);
            saveConfig();
        });
    });

    // Range inputs
    document.querySelectorAll(".card-params input[type='range'][data-key]").forEach((inp) => {
        inp.addEventListener("input", () => {
            const val = Number(inp.value);
            config[inp.dataset.key] = val;
            const span = inp.nextElementSibling;
            if (span && span.classList.contains("range-val")) {
                span.textContent = val.toFixed(2);
            }
        });
        inp.addEventListener("change", () => {
            saveConfig();
        });
    });

    // Checkbox in params (keep aspect)
    document.querySelectorAll(".card-params input[type='checkbox'][data-key]").forEach((cb) => {
        cb.addEventListener("change", () => {
            config[cb.dataset.key] = cb.checked;
            saveConfig();
        });
    });
}

function onReorder() {
    const cards = document.querySelectorAll("#transforms-list .transform-card");
    config.transform_order = Array.from(cards).map((c) => c.dataset.key);
    saveConfig();
}

async function saveConfig() {
    config = await pywebview.api.save_config(config);
}

async function refreshFileCount() {
    const data = await pywebview.api.get_input_files();
    const el = document.getElementById("file-count");
    if (data.count === 0) {
        el.textContent = "No se encontraron imágenes en la carpeta de input";
    } else {
        el.textContent = `${data.count} imagen${data.count !== 1 ? "es" : ""} encontrada${data.count !== 1 ? "s" : ""}`;
    }
}

// Quality input
document.getElementById("webp-quality").addEventListener("change", (e) => {
    config.webp_quality = Number(e.target.value);
    saveConfig();
});

// Browse buttons
document.getElementById("btn-input-dir").addEventListener("click", async () => {
    const dir = await pywebview.api.select_input_directory();
    if (dir) {
        document.getElementById("input-dir").value = dir;
        config.input_dir = dir;
        refreshFileCount();
    }
});

document.getElementById("btn-output-dir").addEventListener("click", async () => {
    const dir = await pywebview.api.select_output_directory();
    if (dir) {
        document.getElementById("output-dir").value = dir;
        config.output_dir = dir;
    }
});

// Process button
document.getElementById("btn-process").addEventListener("click", async () => {
    const btn = document.getElementById("btn-process");
    btn.disabled = true;
    setStatus("");

    const result = await pywebview.api.process_images();
    if (result.error) {
        setStatus(result.error, "error");
        btn.disabled = false;
        return;
    }

    document.getElementById("progress-section").style.display = "";
    pollProgress();
});

function pollProgress() {
    if (polling) clearInterval(polling);
    polling = setInterval(async () => {
        const p = await pywebview.api.get_progress();
        const pct = p.total > 0 ? (p.current / p.total) * 100 : 0;
        document.getElementById("progress-bar").style.width = pct + "%";
        document.getElementById("progress-text").textContent =
            `${p.current}/${p.total} — ${p.current_file || "..."}`;

        if (p.done) {
            clearInterval(polling);
            polling = null;
            document.getElementById("btn-process").disabled = false;
            document.getElementById("progress-bar").style.width = "100%";

            if (p.errors.length > 0) {
                setStatus(
                    `Completado con ${p.errors.length} error${p.errors.length > 1 ? "es" : ""}. ${p.current - p.errors.length}/${p.total} procesadas.`,
                    "error"
                );
            } else if (p.total === 0) {
                setStatus("No se encontraron imágenes para procesar.", "error");
            } else {
                setStatus(`${p.total} imagen${p.total !== 1 ? "es" : ""} procesada${p.total !== 1 ? "s" : ""} correctamente.`, "success");
            }
        }
    }, 200);
}

// Open output
document.getElementById("btn-open-output").addEventListener("click", () => {
    pywebview.api.open_output_directory();
});

// Reset
document.getElementById("btn-reset").addEventListener("click", async () => {
    config = await pywebview.api.reset_config();
    renderConfig();
    refreshFileCount();
    setStatus("Configuración restablecida", "success");
});

function setStatus(msg, type) {
    const el = document.getElementById("status-msg");
    el.textContent = msg;
    el.className = "status-msg" + (type ? ` ${type}` : "");
}
