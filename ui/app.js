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
let previewTimeout = null;
let previewIndex = 0;
let previewTotal = 0;
let currentVersion = "";
let updateDownloadPolling = null;
let updateCheckPolling = null;
let updateCheckBusy = false;

// Wait for pywebview API
window.addEventListener("pywebviewready", init);

async function init() {
  config = await pywebview.api.get_config();
  renderConfig();
  refreshFileCount();
  renderPresets();

  // Execute preview separately to avoid blocking the main UI initialization
  updatePreview().catch((e) => console.error("Initial preview error:", e));

  // Show version
  try {
    const version = await pywebview.api.get_version();
    document.getElementById("app-version").textContent = "v" + version;
    currentVersion = version;
  } catch (e) {}

  // Check for updates after UI is ready
  checkForUpdates();
}

async function checkForUpdates() {
  try {
    await pywebview.api.start_update_check();
    if (updateCheckPolling) clearInterval(updateCheckPolling);
    updateCheckPolling = setInterval(async () => {
      try {
        const result = await pywebview.api.get_update_check_result();
        if (!result.done) return;
        clearInterval(updateCheckPolling);
        updateCheckPolling = null;
        if (result.update_available) {
          showUpdateBanner(result);
        } else if (result.error) {
          toast.show("No se pudo verificar actualizaciones al iniciar: " + result.error, "error");
        }
      } catch (e) {
        clearInterval(updateCheckPolling);
        updateCheckPolling = null;
        toast.show("Error al verificar actualizaciones al inicio.", "error");
      }
    }, 300);
  } catch (e) {
    console.error("Auto update check failed:", e);
    toast.show("Error al iniciar la verificacion de actualizaciones.", "error");
  }
}

function showUpdateBanner(result) {
  const banner = document.getElementById("update-banner");
  document.getElementById("update-msg").textContent =
    `Nueva versi\u00f3n ${result.latest_version} disponible`;
  const link = document.getElementById("update-link");
  link.href = result.download_url || result.release_url;
  link.dataset.latestVersion = result.latest_version;
  link.dataset.downloadUrl = result.download_url || "";
  link.dataset.releaseNotes = result.release_notes || "";
  link.dataset.releaseUrl = result.release_url || "";
  banner.style.display = "flex";
}

async function updatePreview() {
  if (!config.input_dir || config.input_dir === "input_files") {
    document.getElementById("preview-section").style.display = "none";
    document.getElementById("preview-nav").style.display = "none";
    return;
  }

  try {
    const res = await pywebview.api.get_preview(config, null, previewIndex);
    if (res.error) {
      document.getElementById("preview-section").style.display = "none";
      document.getElementById("preview-nav").style.display = "none";
      return;
    }

    document.getElementById("preview-section").style.display = "flex";
    document.getElementById("preview-nav").style.display = "flex";
    document.getElementById("preview-orig").src = res.original;
    document.getElementById("preview-res").src = res.preview;
    const filenameEl = document.getElementById("preview-filename");
    filenameEl.textContent = res.filename;
    filenameEl.setAttribute("data-tooltip", res.filename);
    filenameEl.classList.remove("expanded");
    document.getElementById("preview-index-text").textContent =
      `Imagen ${res.index + 1} de ${res.total}`;

    previewIndex = res.index;
    previewTotal = res.total;
  } catch (e) {
    console.error("Preview error:", e);
    document.getElementById("preview-section").style.display = "none";
    document.getElementById("preview-nav").style.display = "none";
  }
}

async function renderPresets() {
  const list = document.getElementById("presets-list");
  list.innerHTML = "";

  try {
    const presets = await pywebview.api.list_presets();
    for (const name of presets) {
      const item = document.createElement("div");
      item.className = "preset-item";
      item.innerHTML = `
                <span class="preset-name">${name}</span>
                <button class="btn-del-preset" title="Eliminar preset">×</button>
            `;

      item.addEventListener("click", async (e) => {
        if (e.target.classList.contains("btn-del-preset")) {
          const result = await pywebview.api.delete_preset(name);
          if (result.success) {
            renderPresets();
            toast.show("Preset eliminado", "success");
          } else {
            toast.show(`Error: ${result.error}`, "error");
          }
        } else {
          const result = await pywebview.api.load_named_preset(name);
          if (result.error) {
            toast.show(`Error al cargar preset: ${result.error}`, "error");
          } else {
            config = result;
            renderConfig();
            debouncedPreview();
            toast.show(`Preset '${name}' aplicado`, "success");
          }
        }
      });

      list.appendChild(item);
    }
  } catch (e) {
    console.error("Presets render error:", e);
  }
}

function debouncedPreview() {
  if (previewTimeout) clearTimeout(previewTimeout);
  previewTimeout = setTimeout(updatePreview, 150);
}

function renderConfig() {
  document.getElementById("input-dir").value =
    config.input_dir || "input_files";
  document.getElementById("output-dir").value =
    config.output_dir || "output_files";
  document.getElementById("output-format").value =
    config.output_format || "webp";
  document.getElementById("output-quality").value = config.output_quality || 90;
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
  document
    .querySelectorAll(
      ".transform-card input[type='checkbox'][data-enabled-key]",
    )
    .forEach((cb) => {
      cb.addEventListener("change", () => {
        config[cb.dataset.enabledKey] = cb.checked;
        const card = cb.closest(".transform-card");
        card.classList.toggle("disabled", !cb.checked);
        saveConfig();
        debouncedPreview();
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
        if (pct)
          pct.style.display = sel.value === "percentage" ? "contents" : "none";
        if (dim)
          dim.style.display = sel.value === "dimensions" ? "contents" : "none";
      }
      saveConfig();
      debouncedPreview();
    });
  });

  // Number inputs
  document
    .querySelectorAll(".card-params input[type='number'][data-key]")
    .forEach((inp) => {
      inp.addEventListener("change", () => {
        config[inp.dataset.key] = Number(inp.value);
        saveConfig();
        debouncedPreview();
      });
    });

  // Range inputs
  document
    .querySelectorAll(".card-params input[type='range'][data-key]")
    .forEach((inp) => {
      inp.addEventListener("input", () => {
        const val = Number(inp.value);
        config[inp.dataset.key] = val;
        const span = inp.nextElementSibling;
        if (span && span.classList.contains("range-val")) {
          span.textContent = val.toFixed(2);
        }
        debouncedPreview();
      });
      inp.addEventListener("change", () => {
        saveConfig();
      });
    });

  // Checkbox in params (keep aspect)
  document
    .querySelectorAll(".card-params input[type='checkbox'][data-key]")
    .forEach((cb) => {
      cb.addEventListener("change", () => {
        config[cb.dataset.key] = cb.checked;
        saveConfig();
        debouncedPreview();
      });
    });
}

function onReorder() {
  const cards = document.querySelectorAll("#transforms-list .transform-card");
  config.transform_order = Array.from(cards).map((c) => c.dataset.key);
  saveConfig();
  debouncedPreview();
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
document.getElementById("output-quality").addEventListener("change", (e) => {
  config.output_quality = Number(e.target.value);
  saveConfig();
});

// Format input
document.getElementById("output-format").addEventListener("change", (e) => {
  config.output_format = e.target.value;
  saveConfig();
});

// Browse buttons
document.getElementById("btn-input-dir").addEventListener("click", async () => {
  const dir = await pywebview.api.select_input_directory();
  if (dir) {
    document.getElementById("input-dir").value = dir;
    config.input_dir = dir;
    previewIndex = 0;
    refreshFileCount();
    updatePreview();
  }
});

document
  .getElementById("btn-output-dir")
  .addEventListener("click", async () => {
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
  toast.clearAll();

  const result = await pywebview.api.process_images();
  if (result.error) {
    toast.show(result.error, "error");
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
        toast.show(
          `Completado con ${p.errors.length} error${p.errors.length > 1 ? "es" : ""}. ${p.current - p.errors.length}/${p.total} procesadas.`,
          "error",
        );
      } else if (p.total === 0) {
        toast.show("No se encontraron imágenes para procesar.", "error");
      } else {
        toast.show(
          `${p.total} imagen${p.total !== 1 ? "es" : ""} procesada${p.total !== 1 ? "s" : ""} correctamente.`,
          "success",
        );
      }
    }
  }, 200);
}

// Open output
document.getElementById("btn-open-output").addEventListener("click", () => {
  pywebview.api.open_output_directory();
});

// Dismiss update banner
document.getElementById("update-dismiss").addEventListener("click", () => {
  document.getElementById("update-banner").style.display = "none";
});

// Update banner click: open update modal
document.getElementById("update-link").addEventListener("click", (e) => {
  e.preventDefault();
  const link = document.getElementById("update-link");
  const data = {
    latestVersion: link.dataset.latestVersion || "",
    downloadUrl: link.dataset.downloadUrl || "",
    releaseNotes: link.dataset.releaseNotes || "",
    releaseUrl: link.dataset.releaseUrl || "",
  };
  showUpdateModal(data);
});

// Modal helper
function showModal(html) {
  document.getElementById("modal-body").innerHTML = html;
  document.getElementById("modal-overlay").style.display = "flex";
}

function hideModal() {
  document.getElementById("modal-overlay").style.display = "none";
}

document.getElementById("modal-close").addEventListener("click", () => {
  hideModal();
});

document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) {
    hideModal();
  }
});

function showUpdateModal(data) {
  const notesHtml = data.releaseNotes
    ? `<div class="update-notes">${simpleMarkdown(data.releaseNotes)}</div>`
    : "";
  const html = `
    <div class="update-modal">
      <div class="update-icon">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 0117.778-7.778z"/>
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 0117.778-7.778z" transform="translate(0,0)"/>
        </svg>
      </div>
      <div class="update-title">Nueva versi\u00f3n ${data.latestVersion} disponible</div>
      <div class="update-current">Versi\u00f3n actual: ${currentVersion}</div>
      ${notesHtml}
      <div class="update-actions">
        <button id="btn-update-download" class="btn-primary">Actualizar</button>
        <button id="btn-update-skip" class="btn-cancel">Saltar esta versi\u00f3n</button>
        <a href="${data.releaseUrl}" target="_blank" class="btn-link">Ver en GitHub</a>
      </div>
    </div>
  `;
  showModal(html);

  document.getElementById("btn-update-download").addEventListener("click", () => {
    hideModal();
    if (data.downloadUrl) {
      startUpdateDownload(data.downloadUrl);
    } else {
      window.open(data.releaseUrl, "_blank");
    }
  });

  document.getElementById("btn-update-skip").addEventListener("click", async () => {
    await pywebview.api.skip_update(data.latestVersion);
    document.getElementById("update-banner").style.display = "none";
    hideModal();
    toast.show("Se omiti\u00f3 la versi\u00f3n " + data.latestVersion, "info");
  });
}

function simpleMarkdown(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, "<strong>$1</strong>")
    .replace(/^## (.+)$/gm, "<strong>$1</strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "\u2022 $1")
    .replace(/\n/g, "<br>");
}

async function startUpdateDownload(downloadUrl) {
  const overlay = document.getElementById("update-progress-overlay");
  overlay.style.display = "flex";
  document.getElementById("update-progress-bar").style.width = "0%";
  document.getElementById("update-progress-text").textContent = "Descargando...";

  try {
    await pywebview.api.start_update_download(downloadUrl);

    if (updateDownloadPolling) clearInterval(updateDownloadPolling);
    updateDownloadPolling = setInterval(async () => {
      try {
        const p = await pywebview.api.get_download_progress();
        const pct = p.total > 0 ? (p.downloaded / p.total) * 100 : 0;
        document.getElementById("update-progress-bar").style.width = pct + "%";

        if (p.done) {
          clearInterval(updateDownloadPolling);
          updateDownloadPolling = null;
          if (p.result && p.result.error) {
            overlay.style.display = "none";
            toast.show("Error al descargar: " + p.result.error, "error");
          } else {
            showUpdateInstructions();
          }
        }
      } catch (e) {
        clearInterval(updateDownloadPolling);
        updateDownloadPolling = null;
        overlay.style.display = "none";
      }
    }, 300);
  } catch (e) {
    overlay.style.display = "none";
    toast.show("Error al descargar la actualizaci\u00f3n.", "error");
  }
}

function showUpdateInstructions() {
  const overlay = document.getElementById("update-progress-overlay");
  overlay.querySelector(".update-progress-content").innerHTML = `
    <div class="update-success-icon">\u2713</div>
    <div class="update-title">Descarga completa</div>
    <div class="update-instructions">
      La nueva versi\u00f3n se ha descargado. Para completar la actualizaci\u00f3n:
    </div>
    <ol class="update-steps">
      <li>Haz clic en <strong>Abrir en Finder</strong></li>
      <li>Arrastra <strong>Image Transform Lite.app</strong> a tu carpeta Aplicaciones</li>
      <li>Cierra esta aplicaci\u00f3n y abre la nueva versi\u00f3n</li>
    </ol>
    <div class="update-actions">
      <button id="btn-reveal-update" class="btn-primary">Abrir en Finder</button>
      <button id="btn-close-update" class="btn-cancel">Cerrar</button>
    </div>
  `;

  document.getElementById("btn-reveal-update").addEventListener("click", async () => {
    await pywebview.api.reveal_update();
  });
  document.getElementById("btn-close-update").addEventListener("click", () => {
    overlay.style.display = "none";
    document.getElementById("update-banner").style.display = "none";
  });
}

// Manual check for updates (clears skip so it always checks)
document
  .getElementById("menu-check-updates")
  .addEventListener("click", async () => {
    if (updateCheckBusy) return;
    updateCheckBusy = true;
    const btn = document.getElementById("menu-check-updates");
    btn.disabled = true;
    btn.style.opacity = "0.5";

    try {
      await pywebview.api.clear_skip_version();
      showModal("Buscando actualizaciones...");
      await pywebview.api.start_update_check();

      // Poll for result
      const pollCheck = setInterval(async () => {
        try {
          const result = await pywebview.api.get_update_check_result();
          if (!result.done) return;
          clearInterval(pollCheck);

          if (result.update_available) {
            hideModal();
            showUpdateBanner(result);
            showUpdateModal({
              latestVersion: result.latest_version,
              downloadUrl: result.download_url || "",
              releaseNotes: result.release_notes || "",
              releaseUrl: result.release_url || "",
            });
          } else {
            hideModal();
            if (result.error) {
              toast.show("No se pudo verificar: " + result.error, "error");
            } else {
              toast.show("Ya tienes la \u00faltima versi\u00f3n.", "info");
            }
          }
          updateCheckBusy = false;
          btn.disabled = false;
          btn.style.opacity = "";
        } catch (e) {
          clearInterval(pollCheck);
          hideModal();
          toast.show("No se pudo verificar actualizaciones.", "error");
          updateCheckBusy = false;
          btn.disabled = false;
          btn.style.opacity = "";
        }
      }, 300);
    } catch (e) {
      hideModal();
      toast.show("No se pudo verificar actualizaciones.", "error");
      updateCheckBusy = false;
      btn.disabled = false;
      btn.style.opacity = "";
    }
  });

// About
document.getElementById("menu-about").addEventListener("click", async () => {
  try {
    const version = await pywebview.api.get_version();
    showModal(
      `<strong>Image Transform Lite</strong><br>Version ${version}<br><br>` +
      `<span style="font-size:12px;color:var(--text-secondary)">macOS Apple Silicon</span><br><br>` +
      `<span style="font-size:13px;">Hecho por <a href="https://maecly.com/" target="_blank" style="color:var(--accent);text-decoration:none;">MigelAngelEC</a></span>`,
    );
  } catch (e) {
    showModal("<strong>Image Transform Lite</strong>");
  }
});

// Reset
document.getElementById("btn-reset").addEventListener("click", async () => {
  config = await pywebview.api.reset_config();
  renderConfig();
  refreshFileCount();
  previewIndex = 0;
  updatePreview();
  toast.show("Configuración restablecida", "success");
});

// Nueva Receta button - opens save preset modal
document.getElementById("btn-add-preset").addEventListener("click", () => {
  const overlay = document.getElementById("save-preset-overlay");
  const input = document.getElementById("save-preset-name");
  input.value = "";
  overlay.style.display = "flex";
  input.focus();
});

document.getElementById("save-preset-cancel").addEventListener("click", () => {
  document.getElementById("save-preset-overlay").style.display = "none";
});

document
  .getElementById("save-preset-overlay")
  .addEventListener("click", (e) => {
    if (e.target === e.currentTarget) {
      document.getElementById("save-preset-overlay").style.display = "none";
    }
  });

document
  .getElementById("save-preset-confirm")
  .addEventListener("click", async () => {
    const name = document.getElementById("save-preset-name").value.trim();
    if (!name) return;
    document.getElementById("save-preset-overlay").style.display = "none";
    const result = await pywebview.api.save_named_preset(name, config);
    if (result.error) {
      toast.show(`Error al guardar receta: ${result.error}`, "error");
    } else {
      renderPresets();
      toast.show(`Receta '${name}' guardada`, "success");
    }
  });

document.getElementById("save-preset-name").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    document.getElementById("save-preset-confirm").click();
  }
});

// Presets - Export (save to file)
document
  .getElementById("menu-save-preset")
  .addEventListener("click", async () => {
    const result = await pywebview.api.save_preset(config);
    if (result.error) {
      toast.show(`Error al guardar preset: ${result.error}`, "error");
    } else if (result.canceled) {
      // User canceled
    } else {
      toast.show("Preset guardado exitosamente", "success");
    }
  });

// Presets - Import (load from file)
document
  .getElementById("menu-load-preset")
  .addEventListener("click", async () => {
    const path = await pywebview.api.select_preset_file();
    if (path) {
      const result = await pywebview.api.load_preset(path);
      if (result.error) {
        toast.show(`Error al cargar preset: ${result.error}`, "error");
      } else {
        config = result;
        renderConfig();
        debouncedPreview();
        toast.show("Preset cargado", "success");
      }
    }
  });

document.getElementById("btn-prev-img").addEventListener("click", async () => {
  if (previewTotal === 0) return;
  previewIndex = (previewIndex - 1 + previewTotal) % previewTotal;
  await updatePreview();
});

document.getElementById("btn-next-img").addEventListener("click", async () => {
  if (previewTotal === 0) return;
  previewIndex = (previewIndex + 1) % previewTotal;
  await updatePreview();
});

document.getElementById("preview-filename").addEventListener("click", () => {
  const el = document.getElementById("preview-filename");
  el.classList.toggle("expanded");
});
