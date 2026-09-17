// Main JavaScript for Placement Drive Management System

document.addEventListener('DOMContentLoaded', function () {
  // Mobile Sidebar Toggle
  const sidebarToggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
  }

  // Delete Modal Setup
  const deleteModalEl = document.getElementById('deleteModal');
  if (deleteModalEl) {
    deleteModalEl.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const deleteUrl = button.getAttribute('data-bs-delete-url');
      const itemName = button.getAttribute('data-bs-item-name') || 'item';
      
      const confirmBtn = deleteModalEl.querySelector('#confirmDeleteBtn');
      const itemNameSpan = deleteModalEl.querySelector('#deleteItemName');
      
      if (confirmBtn && deleteUrl) {
        confirmBtn.setAttribute('href', deleteUrl);
      }
      if (itemNameSpan) {
        itemNameSpan.textContent = itemName;
      }
    });
  }
});

// Render Chart.js Application Donut Chart
function renderApplicationChart(pending, shortlisted, selected, rejected) {
  const ctx = document.getElementById('applicationStatusChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Pending', 'Shortlisted', 'Selected', 'Rejected'],
      datasets: [{
        data: [pending, shortlisted, selected, rejected],
        backgroundColor: [
          '#f59e0b', // Pending Yellow
          '#06b6d4', // Shortlisted Cyan
          '#10b981', // Selected Green
          '#ef4444'  // Rejected Red
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      cutout: '70%'
    }
  });
}
