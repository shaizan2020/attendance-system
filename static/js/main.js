/**
 * AMS — Attendance Management System
 * Global JavaScript utilities
 */

// ── Auto-dismiss flash alerts ───────────────────
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert-container .alert');
  alerts.forEach((alert, i) => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(120%)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 4000 + i * 500);
  });
});

// ── Modal helpers ────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
  }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(m => m.classList.remove('open'));
  }
});

// ── Table search filter ──────────────────────────
function filterTable(input, tableId) {
  const query = input.value.toLowerCase();
  const rows = document.querySelectorAll(`#${tableId} tbody tr`);
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
  });
}

// ── Jinja2 enumerate polyfill ────────────────────
// (not needed in JS, but keeping this file clean)

// ── Button loading state ─────────────────────────
document.addEventListener('submit', (e) => {
  const btn = e.target.querySelector('button[type="submit"]');
  if (btn && !btn.dataset.noLoad) {
    btn.disabled = true;
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Processing...';
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = orig;
    }, 8000); // Re-enable after 8s as safety
  }
});

// ── Highlight active nav link ────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
  if (link.href === window.location.href) {
    link.classList.add('active');
  }
});
