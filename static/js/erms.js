/* ERMS — Main JavaScript */

// Sidebar Toggle
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle('open');
    } else {
      sidebar.classList.toggle('collapsed');
      mainContent.classList.toggle('expanded');
    }
  });
}

// Auto-dismiss alerts after 5s
document.querySelectorAll('.erms-alert').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    if (bsAlert) bsAlert.close();
  }, 5000);
});

// Active nav link highlighting
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-link-erms').forEach(link => {
  if (link.getAttribute('href') && currentPath.startsWith(link.getAttribute('href'))) {
    link.classList.add('active');
  }
});

// Score input validation (0-100)
document.querySelectorAll('input[data-score]').forEach(input => {
  input.addEventListener('input', function() {
    const val = parseFloat(this.value);
    if (this.value && (isNaN(val) || val < 0 || val > 100)) {
      this.classList.add('is-invalid');
    } else {
      this.classList.remove('is-invalid');
    }
  });
});

// Confirm dangerous actions
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', function(e) {
    if (!confirm(this.dataset.confirm)) e.preventDefault();
  });
});

// Select all checkboxes
const selectAllBox = document.getElementById('selectAll');
if (selectAllBox) {
  selectAllBox.addEventListener('change', function() {
    document.querySelectorAll('.row-check').forEach(cb => cb.checked = this.checked);
  });
}

// AJAX mark notification read
document.querySelectorAll('.notif-item').forEach(link => {
  link.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if (href) {
      fetch(href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }).catch(() => {});
    }
  });
});

// Chart.js defaults
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = '#4A5568';
  Chart.defaults.plugins.legend.position = 'bottom';
}

// GPA Trend Chart helper
function renderGPAChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'GPA',
        data: data,
        borderColor: '#0D7377',
        backgroundColor: 'rgba(13,115,119,.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#1B2B5A',
        pointRadius: 5,
        pointHoverRadius: 7,
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 5, grid: { color: 'rgba(0,0,0,.05)' }, ticks: { stepSize: 1 } },
        x: { grid: { display: false } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

// Grade Distribution Doughnut Chart
function renderGradeChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const COLORS = ['#1A9457','#2563EB','#7C3AED','#D97706','#EA7317','#C0392B'];
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{ data: data, backgroundColor: COLORS, borderWidth: 2, borderColor: '#fff' }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: { legend: { position: 'right' } }
    }
  });
}

// Bar chart for department/course stats
function renderBarChart(canvasId, labels, data, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: label || 'Count',
        data: data,
        backgroundColor: 'rgba(13,115,119,.7)',
        borderColor: '#0D7377',
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' } }, x: { grid: { display: false } } },
      plugins: { legend: { display: false } }
    }
  });
}
