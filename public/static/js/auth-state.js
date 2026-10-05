/**
 * CampusCare - Client Auth State & Dynamic Navbar Controller
 * Synchronizes session state with Netlify Functions backend and renders
 * user credentials, profile pills, and navigation links dynamically.
 */

(function () {
  'use strict';

  let currentSession = null;
  let sessionPromise = null;

  async function fetchSession() {
    if (sessionPromise) return sessionPromise;
    const token = localStorage.getItem('campuscare_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    sessionPromise = fetch('/api/auth-session', { headers })
      .then(res => res.json())
      .then(json => {
        currentSession = json.data || { authenticated: false };
        return currentSession;
      })
      .catch(err => {
        console.warn('[AuthState] Session check error:', err);
        currentSession = { authenticated: false };
        return currentSession;
      });
    return sessionPromise;
  }

  function renderNavbar(session) {
    const navbarMenu = document.getElementById('navbarMenu');
    const navbarActions = document.querySelector('.navbar-actions');
    const mobileDrawer = document.getElementById('mobileNavDrawer');
    const currentPath = window.location.pathname;

    const isStudent = session.authenticated && session.user?.role === 'student';
    const isAdmin = session.authenticated && session.user?.role === 'admin';

    // 1. Desktop Nav Items
    if (navbarMenu) {
      let navHtml = '<ul class="navbar-nav">';

      if (isStudent) {
        navHtml += `
          <li class="nav-item">
            <a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}" title="Public Campus Home">
              <span class="nav-link-icon">⌂</span>
              <span class="nav-link-text">Home</span>
            </a>
          </li>
          <li class="nav-item">
            <a href="/student-dashboard" class="nav-link ${currentPath.includes('student-dashboard') ? 'active' : ''}" title="Student Dashboard">
              <span class="nav-link-icon">▣</span>
              <span class="nav-link-text">Dashboard</span>
            </a>
          </li>
          <li class="nav-item nav-dropdown-wrapper" id="complaintsDropdownWrapper">
            <button
              type="button"
              class="nav-link nav-dropdown-toggle ${['submit-complaint', 'my-complaints', 'complaint-detail'].some(p => currentPath.includes(p)) ? 'active' : ''}"
              id="complaintsDropdownBtn"
              aria-haspopup="true"
              aria-expanded="false"
              title="Complaints Management"
            >
              <span class="nav-link-icon">✎</span>
              <span class="nav-link-text">Complaints</span>
              <span class="dropdown-caret">▾</span>
            </button>
            <div class="nav-glass-dropdown" id="complaintsDropdown" role="menu" aria-labelledby="complaintsDropdownBtn">
              <a href="/submit-complaint" class="nav-dropdown-item ${currentPath.includes('submit-complaint') ? 'active' : ''}" role="menuitem">
                <span class="dropdown-item-icon">📝</span>
                <span class="dropdown-item-text">Submit Complaint</span>
              </a>
              <a href="/my-complaints" class="nav-dropdown-item ${currentPath.includes('my-complaints') ? 'active' : ''}" role="menuitem">
                <span class="dropdown-item-icon">📋</span>
                <span class="dropdown-item-text">My Complaints</span>
              </a>
            </div>
          </li>
          <li class="nav-item">
            <a href="/profile" class="nav-link ${currentPath.includes('profile') ? 'active' : ''}" title="My Profile">
              <span class="nav-link-icon">◉</span>
              <span class="nav-link-text">Profile</span>
            </a>
          </li>
        `;
      } else if (isAdmin) {
        navHtml += `
          <li class="nav-item">
            <a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}" title="Public Campus Home">
              <span class="nav-link-icon">⌂</span>
              <span class="nav-link-text">Home</span>
            </a>
          </li>
          <li class="nav-item">
            <a href="/admin-dashboard" class="nav-link ${currentPath.includes('admin-dashboard') ? 'active' : ''}" title="Management Dashboard">
              <span class="nav-link-icon">📊</span>
              <span class="nav-link-text">Dashboard</span>
            </a>
          </li>
          <li class="nav-item">
            <a href="/admin/soc" class="nav-link ${currentPath.includes('soc') ? 'active' : ''}" title="SOC Operations">
              <span class="nav-link-icon">🔒</span>
              <span class="nav-link-text">SOC Audit</span>
            </a>
          </li>
          <li class="nav-item">
            <a href="/profile" class="nav-link ${currentPath.includes('profile') ? 'active' : ''}" title="Admin Profile">
              <span class="nav-link-icon">🛡️</span>
              <span class="nav-link-text">Profile</span>
            </a>
          </li>
        `;
      } else {
        navHtml += `
          <li class="nav-item">
            <a href="/" class="nav-link ${currentPath === '/' ? 'active' : ''}">
              <span class="nav-link-icon">⌂</span>
              <span class="nav-link-text">Home</span>
            </a>
          </li>
          <li class="nav-item">
            <a href="/login" class="nav-link ${currentPath.includes('login') && !currentPath.includes('admin') ? 'active' : ''}">
              Student Login
            </a>
          </li>
          <li class="nav-item">
            <a href="/register" class="nav-link ${currentPath.includes('register') ? 'active' : ''}">
              Register
            </a>
          </li>
          <li class="nav-item">
            <a href="/admin/login" class="nav-link ${currentPath.includes('admin') ? 'active' : ''}">
              Admin Portal
            </a>
          </li>
        `;
      }

      navHtml += '</ul>';
      navbarMenu.innerHTML = navHtml;
    }

    // 2. Right Side Navbar Actions (Profile Pill & Logout / Sign In)
    if (navbarActions) {
      // Retain notification bell & mobile toggle
      const notifWrapper = navbarActions.querySelector('.navbar-notif-wrapper');
      const mobileToggle = navbarActions.querySelector('#mobileNavToggle');

      let userActionHtml = '';
      if (isStudent) {
        const studentName = session.user.student_name || 'Student';
        userActionHtml = `
          <a href="/profile" class="nav-student-profile-pill" title="View Student Profile">
            <div class="nav-profile-avatar">👤</div>
            <div class="nav-profile-meta">
              <span class="nav-profile-name">${escapeHtml(studentName)}</span>
              <span class="nav-profile-badge">STUDENT</span>
            </div>
          </a>
          <button type="button" class="nav-logout-btn" id="logoutBtn" title="Sign out of student account" style="background: none; border: none; cursor: pointer;">
            <span class="logout-icon">🚪</span>
            <span class="logout-text">Logout</span>
          </button>
        `;
      } else if (isAdmin) {
        const adminName = session.user.admin_username || 'Admin';
        const role = session.user.admin_role || 'ADMIN';
        userActionHtml = `
          <a href="/profile" class="nav-student-profile-pill nav-admin-profile-pill" title="View Admin Profile">
            <div class="nav-profile-avatar">🛡️</div>
            <div class="nav-profile-meta">
              <span class="nav-profile-name">${escapeHtml(adminName)}</span>
              <span class="nav-profile-badge nav-admin-badge">${escapeHtml(role.toUpperCase())}</span>
            </div>
          </a>
          <button type="button" class="nav-logout-btn" id="logoutBtn" title="Sign out of admin account" style="background: none; border: none; cursor: pointer;">
            <span class="logout-icon">🚪</span>
            <span class="logout-text">Logout</span>
          </button>
        `;
      } else {
        userActionHtml = `
          <a href="/login" class="btn-navbar-signin">
            Sign In
          </a>
        `;
      }

      navbarActions.innerHTML = '';
      if (notifWrapper) navbarActions.appendChild(notifWrapper);
      const actionSpan = document.createElement('span');
      actionSpan.style.display = 'inline-flex';
      actionSpan.style.alignItems = 'center';
      actionSpan.style.gap = '0.5rem';
      actionSpan.innerHTML = userActionHtml;
      navbarActions.appendChild(actionSpan);
      if (mobileToggle) navbarActions.appendChild(mobileToggle);

      // Attach logout listener
      const logoutBtn = navbarActions.querySelector('#logoutBtn');
      if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
      }
    }

    // 3. Mobile Drawer
    if (mobileDrawer) {
      let drawerHtml = '<div class="mobile-nav-drawer-inner"><ul class="mobile-nav-list">';
      if (isStudent) {
        drawerHtml += `
          <li><a href="/" class="mobile-nav-link"><span class="mobile-nav-icon">⌂</span><span>Home</span></a></li>
          <li><a href="/student-dashboard" class="mobile-nav-link"><span class="mobile-nav-icon">▣</span><span>Dashboard</span></a></li>
          <li class="mobile-nav-group">
            <div class="mobile-group-header"><span class="mobile-nav-icon">✎</span><span>Complaints</span></div>
            <ul class="mobile-sub-list">
              <li><a href="/submit-complaint" class="mobile-sub-link"><span>📝</span> Submit Complaint</a></li>
              <li><a href="/my-complaints" class="mobile-sub-link"><span>📋</span> My Complaints</a></li>
            </ul>
          </li>
          <li><a href="/profile" class="mobile-nav-link"><span class="mobile-nav-icon">◉</span><span>Profile (${escapeHtml(session.user.student_name || 'Student')})</span></a></li>
          <li class="mobile-nav-divider"></li>
          <li><a href="#" class="mobile-nav-link mobile-logout-link" id="mobileLogoutBtn"><span class="mobile-nav-icon">🚪</span><span>Logout</span></a></li>
        `;
      } else if (isAdmin) {
        drawerHtml += `
          <li><a href="/" class="mobile-nav-link"><span class="mobile-nav-icon">⌂</span><span>Home</span></a></li>
          <li><a href="/admin-dashboard" class="mobile-nav-link"><span class="mobile-nav-icon">📊</span><span>Admin Dashboard</span></a></li>
          <li><a href="/admin/soc" class="mobile-nav-link"><span class="mobile-nav-icon">🔒</span><span>SOC Audit</span></a></li>
          <li><a href="/profile" class="mobile-nav-link"><span class="mobile-nav-icon">🛡️</span><span>Admin Profile</span></a></li>
          <li class="mobile-nav-divider"></li>
          <li><a href="#" class="mobile-nav-link mobile-logout-link" id="mobileLogoutBtn"><span class="mobile-nav-icon">🚪</span><span>Logout</span></a></li>
        `;
      } else {
        drawerHtml += `
          <li><a href="/" class="mobile-nav-link"><span class="mobile-nav-icon">⌂</span><span>Home</span></a></li>
          <li><a href="/login" class="mobile-nav-link"><span class="mobile-nav-icon">👤</span><span>Student Login</span></a></li>
          <li><a href="/register" class="mobile-nav-link"><span class="mobile-nav-icon">📝</span><span>Register</span></a></li>
          <li><a href="/admin/login" class="mobile-nav-link"><span class="mobile-nav-icon">🛡️</span><span>Admin Portal</span></a></li>
        `;
      }
      drawerHtml += '</ul></div>';
      mobileDrawer.innerHTML = drawerHtml;

      const mobLogout = mobileDrawer.querySelector('#mobileLogoutBtn');
      if (mobLogout) {
        mobLogout.addEventListener('click', (e) => {
          e.preventDefault();
          handleLogout();
        });
      }
    }
  }

  async function handleLogout() {
    try {
      await fetch('/api/auth-logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout request failed:', e);
    }
    localStorage.removeItem('campuscare_token');
    localStorage.removeItem('campuscare_user');
    window.location.href = '/login';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Route protection helpers
  async function requireStudent() {
    const session = await fetchSession();
    if (!session.authenticated || session.user?.role !== 'student') {
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
      return false;
    }
    return session.user;
  }

  async function requireAdmin() {
    const session = await fetchSession();
    if (!session.authenticated || session.user?.role !== 'admin') {
      window.location.href = `/admin/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
      return false;
    }
    return session.user;
  }

  // Auto-init on page load
  document.addEventListener('DOMContentLoaded', async () => {
    const session = await fetchSession();
    renderNavbar(session);
  });

  window.CampusCareAuth = {
    fetchSession,
    requireStudent,
    requireAdmin,
    handleLogout
  };
})();
