class Toast {
  constructor(containerId = "toast-container") {
    this.container = document.getElementById(containerId);
    this.maxVisible = 3;
    this.durations = {
      success: 3000,
      error: 5000,
      info: 3000,
      warning: 4000,
    };
  }

  show(message, type = "info") {
    const toast = this._createToast(message, type);
    this.container.appendChild(toast);
    this._enforceMax();
    requestAnimationFrame(() => toast.classList.add("toast-visible"));
    const duration = this.durations[type] || 3000;
    const timer = setTimeout(() => this._dismiss(toast), duration);
    toast._timer = timer;
    toast._startTime = Date.now();
    toast._duration = duration;
    this._startProgress(toast);
  }

  _createToast(message, type) {
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.innerHTML = `
      <div class="toast-content">${message}</div>
      <button class="toast-close">&times;</button>
      <div class="toast-progress"></div>
    `;
    el.querySelector(".toast-close").addEventListener("click", () =>
      this._dismiss(el),
    );
    return el;
  }

  _dismiss(toast) {
    if (toast._dismissed) return;
    toast._dismissed = true;
    clearTimeout(toast._timer);
    toast.classList.remove("toast-visible");
    toast.classList.add("toast-exit");
    setTimeout(() => toast.remove(), 300);
  }

  _enforceMax() {
    const toasts = this.container.querySelectorAll(".toast");
    while (toasts.length > this.maxVisible) {
      this._dismiss(toasts[0]);
    }
  }

  _startProgress(toast) {
    const bar = toast.querySelector(".toast-progress");
    if (!bar) return;
    const update = () => {
      if (toast._dismissed) return;
      const elapsed = Date.now() - toast._startTime;
      const pct = Math.max(0, 100 - (elapsed / toast._duration) * 100);
      bar.style.width = pct + "%";
      if (pct > 0) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  clearAll() {
    this.container.querySelectorAll(".toast").forEach((t) => this._dismiss(t));
  }
}

window.toast = new Toast();
