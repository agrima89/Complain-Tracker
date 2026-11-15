/**
 * CampusCare - client session helpers.
 * The session lives only in the httpOnly `campuscare_session` cookie; nothing is kept in
 * localStorage, so a script injected into a page can't read or steal it.
 */
(function () {
  'use strict';

  let sessionPromise = null;

  // Clear tokens saved by older versions of the site.
  try { localStorage.removeItem('campuscare_token'); localStorage.removeItem('campuscare_user'); } catch { /* storage blocked */ }

  function fetchSession() {
    if (!sessionPromise) {
      sessionPromise = fetch('/api/auth-session', { credentials: 'same-origin', cache: 'no-store' })
        .then(res => res.json())
        .then(json => json.data || { authenticated: false })
        .catch(() => ({ authenticated: false }));
    }
    return sessionPromise;
  }

  function goToLogin(path) {
    window.location.href = `${path}?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`;
  }

  async function requireStudent() {
    const session = await fetchSession();
    if (session.authenticated && session.user?.role === 'student') return session.user;
    if (session.authenticated && session.user?.role === 'admin') { window.location.href = '/admin-dashboard'; return false; }
    goToLogin('/login');
    return false;
  }

  async function requireAdmin() {
    const session = await fetchSession();
    if (session.authenticated && session.user?.role === 'admin') return session.user;
    if (session.authenticated && session.user?.role === 'student') { window.location.href = '/student-dashboard'; return false; }
    goToLogin('/admin-login');
    return false;
  }

  async function handleLogout() {
    try { await fetch('/api/auth-logout', { method: 'POST', credentials: 'same-origin' }); } catch { /* offline */ }
    window.location.href = '/login';
  }

  // Flat session shape, kept for older callers.
  window.checkAuthSession = async function checkAuthSession() {
    const session = await fetchSession();
    return { authenticated: !!session.authenticated, ...(session.user || {}) };
  };

  window.CampusCareAuth = { fetchSession, requireStudent, requireAdmin, handleLogout };

  // Links marked data-super (e.g. Staff accounts) are only for the all-departments admin.
  document.addEventListener('DOMContentLoaded', async () => {
    const links = document.querySelectorAll('[data-super]');
    if (!links.length) return;
    const s = await fetchSession();
    if (s.authenticated && s.user?.role === 'admin' && !s.user.admin_department) links.forEach(l => { l.hidden = false; });
  });
})();
