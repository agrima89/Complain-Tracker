/**
 * Student Complaint & Solution Tracker (SCST)
 * Admin Experience & Live Status Management Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  initAdminStatusUpdaters();
});

function initAdminStatusUpdaters() {
  // Handle in-line quick status update buttons in Admin Table
  document.querySelectorAll('.admin-status-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const complaintId = form.dataset.complaintId;
      const statusSelect = form.querySelector('.status-select');
      const submitBtn = form.querySelector('button[type="submit"]');
      const newStatus = statusSelect.value;

      if (!complaintId || !newStatus) return;

      const originalBtnText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Updating...';

      try {
        const response = await fetch('/admin/api/update-status', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            complaint_id: complaintId,
            status: newStatus
          })
        });

        const data = await response.json();

        if (data.success) {
          // Update Status Badge on the row/card
          updateStatusBadge(complaintId, newStatus);

          // Update Dashboard Statistics Cards
          if (data.stats) {
            updateDashboardStats(data.stats);
          }

          // Show Toast notification
          if (window.showToast) {
            window.showToast('success', 'Status Updated', `Complaint #${String(complaintId).padStart(3, '0')} is now marked as ${newStatus}.`);
          }
        } else {
          if (window.showToast) {
            window.showToast('error', 'Update Failed', data.message || 'Could not update status.');
          }
        }
      } catch (err) {
        console.error('Error updating status:', err);
        if (window.showToast) {
          window.showToast('error', 'Network Error', 'An error occurred while updating the complaint.');
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
      }
    });
  });
}

function updateStatusBadge(complaintId, status) {
  const badge = document.querySelector(`#statusBadge-${complaintId}`);
  if (!badge) return;

  badge.className = 'badge';
  if (status === 'Pending') {
    badge.classList.add('badge-pending');
    badge.innerHTML = '<span class="badge-dot"></span> Pending';
  } else if (status === 'In Progress') {
    badge.classList.add('badge-in-progress');
    badge.innerHTML = '<span class="badge-dot"></span> In Progress';
  } else if (status === 'Resolved') {
    badge.classList.add('badge-resolved');
    badge.innerHTML = '<span class="badge-dot"></span> Resolved';
  } else {
    badge.classList.add('badge-category');
    badge.textContent = status;
  }
}

function updateDashboardStats(stats) {
  const elTotal = document.getElementById('stat-total');
  const elPending = document.getElementById('stat-pending');
  const elProgress = document.getElementById('stat-progress');
  const elResolved = document.getElementById('stat-resolved');

  if (elTotal) elTotal.textContent = stats.total;
  if (elPending) elPending.textContent = stats.pending;
  if (elProgress) elProgress.textContent = stats.in_progress;
  if (elResolved) elResolved.textContent = stats.resolved;
}
