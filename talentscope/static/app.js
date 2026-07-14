/* ============================================================
   TalentScope — Base JavaScript Utilities
   ============================================================ */

/* ---------- Toast Notifications ---------- */
(function () {
  const container = document.createElement('div');
  container.id = 'toast-container';
  document.body.appendChild(container);

  window.showToast = function (message, type = 'info', duration = 3500) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'opacity 300ms ease';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 320);
    }, duration);
  };
})();

/* ---------- API Helper ---------- */
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return res.status === 204 ? null : res.json();
  } catch (e) {
    showToast(e.message || 'Request failed', 'error');
    throw e;
  }
}

/* ---------- Active Nav Highlight ---------- */
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('.nav-item').forEach((link) => {
    const href = link.getAttribute('href')?.replace(/\/$/, '') || '';
    if (href === path || (href !== '' && path.startsWith(href))) {
      link.classList.add('active');
    }
  });
});
