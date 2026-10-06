/* ============================================================
   SpendWise - app.js
   Vanilla JS for UI interactions
   ============================================================ */

'use strict';

// ─── Toast Auto-dismiss ─────────────────────────────────────────
function initToasts() {
  const toasts = document.querySelectorAll('.sw-toast');
  toasts.forEach(function(toast) {
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(function() {
      dismissToast(toast);
    }, 5000);

    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        clearTimeout(timer);
        dismissToast(toast);
      });
    }
  });
}

function dismissToast(toast) {
  toast.classList.add('hiding');
  setTimeout(function() {
    toast.remove();
  }, 300);
}

// ─── Mobile Sidebar ─────────────────────────────────────────────
function initMobileSidebar() {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (!menuBtn || !sidebar) return;

  function openSidebar() {
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  menuBtn.addEventListener('click', function() {
    if (sidebar.classList.contains('open')) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // Close on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });
}

// ─── Password Visibility Toggle ──────────────────────────────────
function initPasswordToggles() {
  const toggleBtns = document.querySelectorAll('.password-toggle');
  toggleBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (!input) return;

      if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        btn.setAttribute('aria-label', 'Hide password');
      } else {
        input.type = 'password';
        btn.innerHTML = '<i class="bi bi-eye"></i>';
        btn.setAttribute('aria-label', 'Show password');
      }
    });
  });
}

// ─── Delete Confirmation ─────────────────────────────────────────
function initDeleteConfirmation() {
  const deleteLinks = document.querySelectorAll('[data-confirm-delete]');
  deleteLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      const message = link.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
}

// ─── Progress Bar Animation ──────────────────────────────────────
function initProgressBars() {
  const progressBars = document.querySelectorAll('[data-progress]');
  progressBars.forEach(function(bar) {
    const target = parseFloat(bar.getAttribute('data-progress')) || 0;
    const capped = Math.min(target, 100);
    // Small delay for visual effect
    setTimeout(function() {
      bar.style.width = capped + '%';
    }, 100);
  });
}

// ─── Chart.js Doughnut Chart ─────────────────────────────────────
function initSpendingChart() {
  const canvas = document.getElementById('spending-chart');
  if (!canvas) return;

  const labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
  const values = JSON.parse(canvas.getAttribute('data-values') || '[]');
  const colors = JSON.parse(canvas.getAttribute('data-colors') || '[]');

  if (labels.length === 0 || values.every(v => v === 0)) {
    const container = canvas.parentElement;
    container.innerHTML = '<div class="empty-state" style="padding:30px 10px"><div class="empty-state-icon"><i class="bi bi-pie-chart"></i></div><p class="empty-state-text">No spending data for this month</p></div>';
    return;
  }

  if (typeof Chart === 'undefined') return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 0,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 10,
            font: {
              size: 12,
              family: 'Inter, system-ui, sans-serif',
              weight: '500',
            },
            color: '#64748b',
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const value = context.parsed;
              const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return ` ₹${value.toLocaleString('en-IN', {minimumFractionDigits: 2})} (${pct}%)`;
            }
          },
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: '#334155',
          borderWidth: 1,
          cornerRadius: 8,
          padding: 10,
        }
      },
      animation: {
        animateRotate: true,
        duration: 800,
        easing: 'easeInOutQuart',
      }
    }
  });
}

// ─── Amount Input Formatting ─────────────────────────────────────
function initAmountInputs() {
  const amountInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
  amountInputs.forEach(function(input) {
    input.addEventListener('blur', function() {
      if (input.value && !isNaN(parseFloat(input.value))) {
        input.value = parseFloat(input.value).toFixed(2);
      }
    });
  });
}

// ─── Character Counter ───────────────────────────────────────────
function initCharCounters() {
  const textareas = document.querySelectorAll('[data-maxlength]');
  textareas.forEach(function(el) {
    const max = parseInt(el.getAttribute('data-maxlength'));
    const counterId = el.getAttribute('data-counter');
    const counter = document.getElementById(counterId);
    if (!counter) return;

    function update() {
      const remaining = max - el.value.length;
      counter.textContent = remaining + ' characters remaining';
      counter.style.color = remaining < 20 ? 'var(--warning)' : 'var(--text-muted)';
    }

    el.addEventListener('input', update);
    update();
  });
}

// ─── Filter Form Auto-submit ─────────────────────────────────────
function initFilterAutoSubmit() {
  const filterSelects = document.querySelectorAll('[data-auto-submit]');
  filterSelects.forEach(function(select) {
    select.addEventListener('change', function() {
      const form = select.closest('form');
      if (form) form.submit();
    });
  });
}

// ─── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initToasts();
  initMobileSidebar();
  initPasswordToggles();
  initDeleteConfirmation();
  initProgressBars();
  initSpendingChart();
  initAmountInputs();
  initCharCounters();
  initFilterAutoSubmit();
});
