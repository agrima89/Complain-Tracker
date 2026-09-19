/**
 * Student Complaint & Solution Tracker (SCST)
 * Admin Experience, Live Status Management & Real-Time Analytics
 */

document.addEventListener('DOMContentLoaded', () => {
  initAdminStatusUpdaters();
  initAnalyticsCharts();
  initCampusPulseCounters();
  initCampusHeatmap();
});

/**
 * Get CSRF Token from meta tag
 */
function getCsrfToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  return '';
}

/**
 * Handle quick status updates from Admin tables and details
 */
function initAdminStatusUpdaters() {
  document.querySelectorAll('.admin-status-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const complaintId = form.dataset.complaintId;
      const statusSelect = form.querySelector('.status-select');
      const submitBtn = form.querySelector('button[type="submit"]');
      const newStatus = statusSelect ? statusSelect.value : null;

      if (!complaintId || !newStatus) return;

      const originalBtnText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Updating...';

      try {
        const csrfToken = getCsrfToken();
        const response = await fetch('/admin/api/update-status', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            complaint_id: complaintId,
            status: newStatus,
            remarks: 'Quick status update via dashboard'
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
          window.showToast('error', 'Network Error', 'An error occurred while updating the complaint status.');
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
    badge.classList.add('badge-progress');
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
  const elEscalated = document.getElementById('stat-escalated');

  if (elTotal && stats.total !== undefined) elTotal.textContent = stats.total;
  if (elPending && stats.pending !== undefined) elPending.textContent = stats.pending;
  if (elProgress && stats.in_progress !== undefined) elProgress.textContent = stats.in_progress;
  if (elResolved && stats.resolved !== undefined) elResolved.textContent = stats.resolved;
  if (elEscalated && stats.escalated !== undefined) elEscalated.textContent = stats.escalated;
}

/**
 * Initialize Chart.js interactive charts from embedded JSON data
 */
function initAnalyticsCharts() {
  const analyticsScript = document.getElementById('analyticsData');
  if (!analyticsScript || typeof Chart === 'undefined') {
    return;
  }

  let analyticsData;
  try {
    analyticsData = JSON.parse(analyticsScript.textContent);
  } catch (err) {
    console.warn('Unable to parse analytics telemetry JSON:', err);
    return;
  }

  // Global Chart.js typography & styling defaults
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  Chart.defaults.font.size = 11;

  // 1. Categories Breakdown (Doughnut Chart)
  const categoryCanvas = document.getElementById('categoryChart');
  if (categoryCanvas && analyticsData.categories) {
    const labels = analyticsData.categories.map(c => c.category || 'Other');
    const counts = analyticsData.categories.map(c => c.count);

    const colors = [
      '#38bdf8', '#818cf8', '#c084fc', '#f472b6', 
      '#fb923c', '#4ade80', '#fbbf24', '#a78bfa'
    ];

    new Chart(categoryCanvas, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          data: counts.length ? counts : [1],
          backgroundColor: counts.length ? colors.slice(0, labels.length) : ['rgba(255, 255, 255, 0.1)'],
          borderWidth: 2,
          borderColor: 'rgba(3, 7, 18, 0.8)',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 12,
              color: '#cbd5e1'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            titleColor: '#ffffff',
            bodyColor: '#38bdf8',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
          }
        },
        cutout: '68%'
      }
    });
  }

  // 2. Priority Breakdown (Bar Chart)
  const priorityCanvas = document.getElementById('priorityChart');
  if (priorityCanvas && analyticsData.priorities) {
    const priorityOrder = ['High', 'Medium', 'Low'];
    const pMap = { High: 0, Medium: 0, Low: 0 };
    (analyticsData.priorities || []).forEach(p => {
      if (pMap.hasOwnProperty(p.priority)) {
        pMap[p.priority] = p.count;
      }
    });

    new Chart(priorityCanvas, {
      type: 'bar',
      data: {
        labels: ['High', 'Medium', 'Low'],
        datasets: [{
          label: 'Complaints',
          data: [pMap.High, pMap.Medium, pMap.Low],
          backgroundColor: [
            'rgba(239, 68, 68, 0.75)',
            'rgba(245, 158, 11, 0.75)',
            'rgba(34, 197, 94, 0.75)'
          ],
          borderColor: [
            '#ef4444',
            '#f59e0b',
            '#22c55e'
          ],
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            titleColor: '#ffffff',
            bodyColor: '#38bdf8',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#cbd5e1',
              font: { weight: '600' }
            }
          },
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              precision: 0,
              color: '#64748b'
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            }
          }
        }
      }
    });
  }

  // 3. Monthly Trends (Smooth Line Chart)
  const monthlyCanvas = document.getElementById('monthlyTrendChart');
  if (monthlyCanvas && analyticsData.monthly_trends) {
    const rawTrends = analyticsData.monthly_trends || [];
    const labels = rawTrends.map(t => {
      const parts = (t.month || '').split('-');
      if (parts.length === 2) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const idx = parseInt(parts[1], 10) - 1;
        return (monthNames[idx] || parts[1]) + ' ' + parts[0].slice(2);
      }
      return t.month;
    });
    const counts = rawTrends.map(t => t.count);

    new Chart(monthlyCanvas, {
      type: 'line',
      data: {
        labels: labels.length ? labels : ['Current'],
        datasets: [{
          label: 'Grievances Lodged',
          data: counts.length ? counts : [0],
          fill: true,
          backgroundColor: 'rgba(56, 189, 248, 0.12)',
          borderColor: '#38bdf8',
          borderWidth: 2.5,
          tension: 0.35,
          pointBackgroundColor: '#38bdf8',
          pointBorderColor: '#030712',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            titleColor: '#ffffff',
            bodyColor: '#38bdf8',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#cbd5e1'
            }
          },
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              precision: 0,
              color: '#64748b'
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            }
          }
        }
      }
    });
  }
}

/**
 * Animate Campus Pulse Metrics counters with ease-out cubic animation
 */
function initCampusPulseCounters() {
  const counters = document.querySelectorAll('.pulse-counter');
  counters.forEach((counter) => {
    const rawVal = counter.getAttribute('data-target');
    if (!rawVal) return;
    const target = parseFloat(rawVal);
    if (isNaN(target)) return;

    const isFloat = rawVal.includes('.');
    const duration = 1000; // ms
    const startTime = performance.now();

    function updateCount(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic: 1 - (1 - t)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = isFloat ? (target * easeOut).toFixed(1) : Math.round(target * easeOut);
      counter.textContent = current;

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      } else {
        counter.textContent = isFloat ? target.toFixed(1) : target;
      }
    }
    requestAnimationFrame(updateCount);
  });
}

/**
 * Interactive Campus Problem Heatmap & Zone Telemetry Inspector
 */
function initCampusHeatmap() {
  const heatmapScript = document.getElementById('heatmapData');
  let heatmapData = [];
  if (heatmapScript) {
    try {
      heatmapData = JSON.parse(heatmapScript.textContent);
    } catch (e) {
      console.warn('Could not parse heatmap data from DOM script:', e);
    }
  }

  let zoneMap = {};
  function rebuildZoneMap() {
    zoneMap = {};
    heatmapData.forEach((z) => {
      zoneMap[z.id] = z;
      if (z.zone_key) zoneMap[z.zone_key] = z;
    });
  }
  rebuildZoneMap();

  let currentZoneId = (heatmapData && heatmapData.length > 0) ? heatmapData[0].id : 'block-a';
  let currentFilter = 'all';

  const zoneNodes = document.querySelectorAll('.heatmap-zone-node');
  const inspectorName = document.getElementById('inspectorZoneName');
  const inspectorType = document.getElementById('inspectorZoneType');
  const inspectorBadge = document.getElementById('inspectorIntensityBadge');
  const inspectorTotal = document.getElementById('inspectorTotalCount');
  const inspectorUnresolved = document.getElementById('inspectorUnresolvedCount');
  const inspectorHigh = document.getElementById('inspectorHighCount');
  const inspectorMedium = document.getElementById('inspectorMediumCount');
  const inspectorLow = document.getElementById('inspectorLowCount');
  const inspectorCategory = document.getElementById('inspectorTopCategory');
  const inspectorLink = document.getElementById('inspectorFilterLink');
  const complaintsHeader = document.getElementById('zoneComplaintsHeader');
  const complaintsBadge = document.getElementById('zoneComplaintsBadge');
  const complaintsContainer = document.getElementById('zoneComplaintsContainer');

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function renderZoneComplaints(complaints, zoneName) {
    if (!complaintsContainer) return;

    // Apply active filter to complaints in this zone
    let filtered = complaints || [];
    if (currentFilter === 'critical') {
      filtered = filtered.filter((c) => (c.priority === 'High' || c.priority === 'Critical'));
    } else if (currentFilter === 'active') {
      filtered = filtered.filter((c) => (c.status !== 'Resolved'));
    }

    if (complaintsHeader) {
      complaintsHeader.textContent = `COMPLAINTS IN ${zoneName ? zoneName.toUpperCase() : 'THIS ZONE'}`;
    }

    if (complaintsBadge) {
      complaintsBadge.textContent = `${filtered.length} issues`;
    }

    if (filtered.length === 0) {
      complaintsContainer.innerHTML = `
        <div id="zoneEmptyState" style="background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 1.75rem 1rem; text-align: center; color: #64748b;">
          <div style="font-size: 1.5rem; margin-bottom: 0.35rem;">🛡️</div>
          <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">No complaints recorded in this zone.</div>
          <div style="font-size: 0.75rem; margin-top: 0.2rem;">All facilities in this area are operating normally.</div>
        </div>
      `;
      return;
    }

    let html = '';
    filtered.forEach((c) => {
      const pColor = c.priority === 'High' ? 'background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5;'
                   : c.priority === 'Medium' ? 'background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.4); color: #fcd34d;'
                   : 'background: rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.4); color: #86efac;';

      const sColor = c.status === 'Resolved' ? 'background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.4); color: #34d399;'
                   : c.status === 'In Progress' ? 'background: rgba(56, 189, 248, 0.2); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8;'
                   : 'background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24;';

      let photoHtml = '';
      if (c.has_photo && c.photo_path) {
        const photoUrl = c.photo_path.startsWith('/') ? c.photo_path : `/${c.photo_path}`;
        photoHtml = `
          <div style="margin-bottom: 0.5rem;">
            <a href="${photoUrl}" target="_blank" style="display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; color: #38bdf8; text-decoration: none; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 0.25rem 0.5rem;">
              <span>📷</span>
              <span>Evidence Photo</span>
            </a>
          </div>
        `;
      }

      html += `
        <div class="zone-complaint-item" style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 0.85rem; transition: all 0.2s ease;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.4rem;">
            <span style="font-family: monospace; font-weight: 700; font-size: 0.8rem; color: #38bdf8;">#${escapeHtml(c.ticket_id)}</span>
            <div style="display: flex; gap: 0.35rem;">
              <span class="badge" style="font-size: 0.68rem; font-weight: 700; ${pColor}">${escapeHtml(c.priority)}</span>
              <span class="badge" style="font-size: 0.68rem; font-weight: 700; ${sColor}">${escapeHtml(c.status)}</span>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: #cbd5e1; font-weight: 600; margin-bottom: 0.25rem;">
            <span>📁 ${escapeHtml(c.category)}</span>
            <span style="color: #64748b;">•</span>
            <span style="color: #94a3b8;">👤 ${escapeHtml(c.student_name)}</span>
          </div>

          <div style="font-size: 0.825rem; color: #e2e8f0; line-height: 1.35; margin-bottom: 0.4rem; word-break: break-word;">
            ${escapeHtml(c.description)}
          </div>

          <div style="font-size: 0.75rem; color: #94a3b8; display: flex; align-items: center; gap: 0.35rem; margin-bottom: 0.4rem;">
            <span>📍</span>
            <span>${escapeHtml(c.location)}</span>
          </div>

          ${photoHtml}

          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.725rem; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 0.4rem; margin-top: 0.4rem;">
            <span>📅 ${escapeHtml(c.date_formatted || c.date)}</span>
            <a href="/admin/complaint/${c.complaint_id}" class="text-link" style="color: #38bdf8; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 0.2rem;">
              <span>Details</span>
              <span>&rarr;</span>
            </a>
          </div>
        </div>
      `;
    });

    complaintsContainer.innerHTML = html;
  }

  function selectZone(zoneId) {
    currentZoneId = zoneId;
    const zone = zoneMap[zoneId];
    if (!zone) return;

    // Highlight active zone node on map
    const allNodes = document.querySelectorAll('.heatmap-zone-node');
    allNodes.forEach((node) => {
      const rect = node.querySelector('.zone-rect');
      if (node.dataset.zoneId === zone.id || node.id === `zoneNode-${zone.id}`) {
        node.classList.add('zone-active-focus');
        if (rect) {
          rect.style.stroke = '#38bdf8';
          rect.style.strokeWidth = '2.5px';
        }
      } else {
        node.classList.remove('zone-active-focus');
        if (rect) {
          rect.style.stroke = '';
          rect.style.strokeWidth = '';
        }
      }
    });

    // Update inspector drawer details
    if (inspectorName) inspectorName.textContent = zone.name;
    if (inspectorType) inspectorType.textContent = zone.type;
    if (inspectorTotal) inspectorTotal.textContent = zone.total_complaints || 0;
    if (inspectorUnresolved) inspectorUnresolved.textContent = zone.unresolved_count || 0;
    if (inspectorHigh) inspectorHigh.textContent = zone.high_priority_count || 0;
    if (inspectorMedium) inspectorMedium.textContent = zone.medium_priority_count || 0;
    if (inspectorLow) inspectorLow.textContent = zone.low_priority_count || 0;
    if (inspectorCategory) inspectorCategory.textContent = zone.top_category || 'None Recorded';

    if (inspectorBadge) {
      inspectorBadge.textContent = zone.intensity || 'Low';
      inspectorBadge.className = 'badge';
      if (zone.intensity === 'Critical') {
        inspectorBadge.style.background = 'rgba(239, 68, 68, 0.25)';
        inspectorBadge.style.borderColor = 'rgba(239, 68, 68, 0.5)';
        inspectorBadge.style.color = '#f87171';
      } else if (zone.intensity === 'High') {
        inspectorBadge.style.background = 'rgba(245, 158, 11, 0.25)';
        inspectorBadge.style.borderColor = 'rgba(245, 158, 11, 0.5)';
        inspectorBadge.style.color = '#fbbf24';
      } else if (zone.intensity === 'Moderate') {
        inspectorBadge.style.background = 'rgba(6, 182, 212, 0.2)';
        inspectorBadge.style.borderColor = 'rgba(6, 182, 212, 0.4)';
        inspectorBadge.style.color = '#38bdf8';
      } else {
        inspectorBadge.style.background = 'rgba(16, 185, 129, 0.2)';
        inspectorBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        inspectorBadge.style.color = '#34d399';
      }
    }

    if (inspectorLink) {
      inspectorLink.href = `/admin/dashboard?q=${encodeURIComponent(zone.name)}`;
      inspectorLink.textContent = `🔍 Filter Table for ${zone.name}`;
    }

    // Render genuine database complaints for this zone
    renderZoneComplaints(zone.complaints, zone.name);
  }

  // Attach hover & click handlers to zone nodes
  zoneNodes.forEach((node) => {
    const zoneId = node.dataset.zoneId;
    node.addEventListener('mouseenter', () => selectZone(zoneId));
    node.addEventListener('click', () => selectZone(zoneId));
  });

  // Heatmap Filter buttons (All Zones, Critical / High, Active Issues)
  const filterBtns = document.querySelectorAll('.heatmap-filter-btn');
  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter || 'all';

      const allNodes = document.querySelectorAll('.heatmap-zone-node');
      allNodes.forEach((node) => {
        const intensity = node.dataset.intensity;
        const unresolved = parseInt(node.dataset.unresolved, 10) || 0;

        let visible = true;
        if (currentFilter === 'critical') {
          visible = (intensity === 'Critical' || intensity === 'High');
        } else if (currentFilter === 'active') {
          visible = unresolved > 0;
        }

        if (visible) {
          node.style.opacity = '1';
          node.style.pointerEvents = 'auto';
        } else {
          node.style.opacity = '0.22';
          node.style.pointerEvents = 'auto';
        }
      });

      // Refresh complaints in currently selected zone with active filter
      if (currentZoneId && zoneMap[currentZoneId]) {
        renderZoneComplaints(zoneMap[currentZoneId].complaints, zoneMap[currentZoneId].name);
      }
    });
  });

  // Real-time live polling & sync function
  async function fetchLiveZoneTelemetry() {
    try {
      const response = await fetch('/api/admin/zone-telemetry');
      if (!response.ok) return;
      const data = await response.json();
      if (data && data.success && Array.isArray(data.zones)) {
        heatmapData = data.zones;
        rebuildZoneMap();

        // Update SVG node data attributes and labels
        data.zones.forEach((z) => {
          const node = document.getElementById(`zoneNode-${z.id}`);
          if (node) {
            node.dataset.intensity = z.intensity;
            node.dataset.unresolved = z.unresolved_count;
            node.dataset.total = z.total_complaints;

            const rect = node.querySelector('.zone-rect');
            if (rect) {
              rect.className.baseVal = `zone-rect intensity-${z.intensity.toLowerCase()}`;
              if (z.intensity === 'Critical') {
                rect.setAttribute('fill', 'url(#grad-critical)');
                rect.setAttribute('stroke', '#ef4444');
                rect.setAttribute('stroke-width', '2');
                rect.setAttribute('filter', 'url(#glow-critical)');
              } else if (z.intensity === 'High') {
                rect.setAttribute('fill', 'url(#grad-high)');
                rect.setAttribute('stroke', '#f59e0b');
                rect.setAttribute('stroke-width', '2');
                rect.setAttribute('filter', 'url(#glow-high)');
              } else if (z.intensity === 'Moderate') {
                rect.setAttribute('fill', 'url(#grad-moderate)');
                rect.setAttribute('stroke', '#06b6d4');
                rect.setAttribute('stroke-width', '1.2');
                rect.removeAttribute('filter');
              } else if (z.total_complaints > 0) {
                rect.setAttribute('fill', 'url(#grad-low)');
                rect.setAttribute('stroke', '#10b981');
                rect.setAttribute('stroke-width', '1.2');
                rect.removeAttribute('filter');
              } else {
                rect.setAttribute('fill', 'url(#grad-neutral)');
                rect.setAttribute('stroke', 'rgba(255, 255, 255, 0.15)');
                rect.setAttribute('stroke-width', '1.2');
                rect.removeAttribute('filter');
              }
            }
          }
        });

        // Re-render currently selected zone
        if (currentZoneId && zoneMap[currentZoneId]) {
          selectZone(currentZoneId);
        }
      }
    } catch (err) {
      // Quiet fail: server-rendered elements persist
    }
  }

  window.refreshZoneTelemetry = fetchLiveZoneTelemetry;

  // Poll for live zone telemetry every 25 seconds
  setInterval(fetchLiveZoneTelemetry, 25000);
}


