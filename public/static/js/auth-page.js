/* CampusCare: shared logic for login, register and admin login */
(function () {
  'use strict';
  const form = document.querySelector('[data-auth-form]');
  if (!form) return;
  const mode = form.dataset.authForm; // student | register | admin
  const btn = form.querySelector('button[type=submit]');
  const btnLabel = btn.innerHTML;
  const alertBox = document.getElementById('authAlert');

  const ENDPOINTS = {
    student: ['/api/login', '/.netlify/functions/auth-login'],
    register: ['/api/register', '/.netlify/functions/auth-register'],
    admin: ['/api/auth-admin-login', '/.netlify/functions/auth-admin-login']
  };
  const DEFAULT_NEXT = { student: '/student-dashboard', register: '/student-dashboard', admin: '/admin-dashboard' };

  function safeRedirect(target, fallback) {
    // Only allow same-origin relative paths (blocks //evil.com and absolute URLs)
    if (typeof target === 'string' && /^\/(?!\/)[\w\-./?=&%#]*$/.test(target)) return target;
    return fallback;
  }

  function showAlert(html, kind = 'error') {
    alertBox.className = `a-alert ${kind}`;
    alertBox.innerHTML = `<span aria-hidden="true">${kind === 'error' ? '!' : '✓'}</span><div>${html}</div>`;
    alertBox.hidden = false;
  }

  /* Password reveal */
  form.querySelectorAll('[data-reveal]').forEach((b) => b.addEventListener('click', () => {
    const input = document.getElementById(b.dataset.reveal);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    b.textContent = show ? 'Hide' : 'Show';
    b.setAttribute('aria-pressed', String(show));
  }));

  /* Password strength (register) */
  const pw = document.getElementById('password'), meter = document.getElementById('pwMeter');
  if (meter && pw) pw.addEventListener('input', () => {
    const v = pw.value;
    const score = [v.length >= 8, /[A-Z]/.test(v) && /[a-z]/.test(v), /\d/.test(v), /[^A-Za-z0-9]/.test(v), v.length >= 12].filter(Boolean).length;
    const labels = ['Too short', 'Weak', 'Fair', 'Good', 'Strong', 'Excellent'];
    meter.dataset.score = String(v ? score : 0);
    meter.querySelector('span').textContent = v ? labels[score] : '';
  });

  /* Caps lock hint */
  const caps = document.getElementById('capsHint');
  if (caps && pw) pw.addEventListener('keyup', (e) => { caps.hidden = !(e.getModifierState && e.getModifierState('CapsLock')); });

  async function post(body) {
    const [primary, fallback] = ENDPOINTS[mode];
    const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify(body) };
    let res;
    try { res = await fetch(primary, opts); } catch { res = null; }
    if (!res || res.status === 404) res = await fetch(fallback, opts);
    let json = {};
    try { json = await res.json(); } catch { /* non-JSON */ }
    return { res, json };
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alertBox.hidden = true;
    if (!form.checkValidity()) { form.reportValidity(); return; }
    const data = Object.fromEntries(new FormData(form));
    if (data.email) data.email = data.email.trim();
    if (data.name) data.name = data.name.trim();
    if (data.username) data.username = data.username.trim();

    btn.disabled = true;
    btn.innerHTML = '<span class="a-spin" aria-hidden="true"></span> Please wait…';
    try {
      const { res, json } = await post(data);
      if (res.ok && json.success) {
        // The server sets an httpOnly session cookie; nothing to store client-side.
        showAlert(mode === 'register' ? 'Account created. Taking you to your dashboard…' : 'Signed in. Redirecting…', 'success');
        const next = new URLSearchParams(location.search).get('redirect');
        setTimeout(() => { location.href = safeRedirect(next, safeRedirect(json.data?.redirectUrl, DEFAULT_NEXT[mode])); }, 450);
        return;
      }
      let msg = json.error || json.message || `Something went wrong (status ${res.status}).`;
      const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
      msg = esc(msg);
      if (mode === 'register' && (res.status === 409 || /already/i.test(msg))) msg += ' <a href="/login">Sign in instead →</a>';
      if (mode === 'student' && /admin/i.test(data.email || '')) msg += ' <a href="/admin-login">Staff sign in →</a>';
      showAlert(msg);
    } catch (err) {
      showAlert('Network error. Check your connection and try again.');
    }
    btn.disabled = false;
    btn.innerHTML = btnLabel;
  });

  /* Live stat on the side panel */
  const sr = document.getElementById('sideResolved'), sa = document.getElementById('sideAvg');
  if (sr || sa) fetch('/api/public-stats').then((r) => r.json()).then((j) => {
    const s = j.data || j.stats || {};
    if (sr) sr.textContent = s.resolved_complaints ?? '–';
    if (sa) sa.textContent = s.average_response_display || '–';
  }).catch(() => { if (sr) sr.textContent = '–'; if (sa) sa.textContent = '–'; });
})();
