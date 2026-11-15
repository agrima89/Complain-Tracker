/* CampusCare cinematic landing: pull-up words, scroll-linked reveal, card entrances, live map */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Split text into pull-up words (WordsPullUp / WordsPullUpMultiStyle) */
  let i = 0;
  function splitWords(node, asterisk) {
    const words = node.textContent.trim().split(/\s+/);
    node.textContent = '';
    words.forEach((w, idx) => {
      const wrap = document.createElement('span'); wrap.className = 'wrap';
      const s = document.createElement('span'); s.className = 'w'; s.style.setProperty('--i', i++);
      s.setAttribute('aria-hidden', 'true');
      if (asterisk && idx === words.length - 1) {
        s.innerHTML = `${esc(w.slice(0, -1))}<span class="cn-last">${esc(w.slice(-1))}<span class="cn-ast">*</span></span>`;
      } else s.textContent = w;
      wrap.appendChild(s); node.appendChild(wrap);
      if (idx < words.length - 1) node.appendChild(document.createTextNode(' '));
    });
  }
  document.querySelectorAll('[data-pullup]').forEach((n) => { i = 0; const label = n.textContent.trim(); splitWords(n, n.hasAttribute('data-asterisk')); n.setAttribute('aria-label', label); });
  document.querySelectorAll('[data-multi]').forEach((n) => {
    i = 0; n.setAttribute('aria-label', n.textContent.replace(/\s+/g, ' ').trim());
    n.querySelectorAll('[data-seg]').forEach((seg) => splitWords(seg));
  });

  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -100px 0px' });
  document.querySelectorAll('[data-pullup],[data-multi],.cn-cards').forEach((n) => io.observe(n));
  document.querySelectorAll('.cn-card').forEach((c, k) => c.style.setProperty('--i', k));
  requestAnimationFrame(() => document.body.classList.add('ready'));

  /* Optional hero video: only shown if /static/video/campus.mp4 exists */
  const vid = $('#heroVideo');
  if (vid && !reduce) {
    fetch(vid.dataset.src, { method: 'HEAD' }).then((r) => {
      if (!r.ok || !(r.headers.get('content-type') || '').startsWith('video')) return;
      vid.src = vid.dataset.src;
      vid.addEventListener('playing', () => vid.classList.add('playing'), { once: true });
      vid.play().catch(() => {});
    }).catch(() => {});
  }

  /* Scroll-linked character reveal (offset start 0.8 → end 0.2) */
  const rv = $('#revealText');
  if (rv) {
    const text = rv.textContent.trim();
    rv.setAttribute('aria-label', text);
    rv.innerHTML = [...text].map((c) => `<span class="ch" aria-hidden="true">${c === ' ' ? ' ' : esc(c)}</span>`).join('');
    const chars = rv.querySelectorAll('.ch'), n = chars.length;
    const update = () => {
      const r = rv.getBoundingClientRect(), vh = innerHeight;
      const start = vh * 0.8, end = vh * 0.2;               // element top at 80% → element bottom at 20%
      const total = (r.height + start - end) || 1;
      const p = Math.min(1, Math.max(0, (start - r.top) / total));
      chars.forEach((ch, k) => {
        const cp = k / n, a = cp - 0.1, b = cp + 0.05;
        const t = Math.min(1, Math.max(0, (p - a) / (b - a)));
        ch.style.opacity = (0.2 + 0.8 * t).toFixed(2);
      });
    };
    if (reduce) chars.forEach((c) => (c.style.opacity = 1));
    else { let raf = 0; addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(update); }, { passive: true }); update(); }
  }

  /* Session-aware CTAs */
  fetch('/api/auth-session', { credentials: 'same-origin' }).then((r) => (r.ok ? r.json() : null)).then((s) => {
    if (!s || !s.authenticated) return;
    const admin = s.user?.role === 'admin', href = admin ? '/admin-dashboard' : '/student-dashboard';
    $('#heroCta').href = href; $('#heroCtaText').textContent = admin ? 'Open console' : 'My dashboard';
    $('#finalCta').href = href;
    const a = $('#navAuth'); a.href = href; a.textContent = 'Dashboard';
  }).catch(() => {});

  /* Live campus map + stats */
  const SAMPLE = { 'Block C': { open: 3, urgent: 1, fixed: 4 }, Hostel: { open: 2, urgent: 0, fixed: 6 }, Library: { open: 0, urgent: 0, fixed: 3 },
    'Academic Block': { open: 1, urgent: 0, fixed: 5 }, 'Block A': { open: 0, urgent: 0, fixed: 2 }, Campus: { open: 1, urgent: 0, fixed: 1 } };
  const set = (sel, v) => { const e = $(sel); if (e) e.textContent = v; };
  let map = null;
  if (window.CampusMap && $('#campusMap')) {
    const ph = CampusMap.phase();
    set('#phaseName', `${ph.icon} ${ph.name}`);
    map = CampusMap.mount($('#campusMap'), {
      onUpdate(h) {
        $('#healthRing').style.setProperty('--p', h.score); set('#healthScore', h.score);
        set('#healthLine', h.open + h.fixed === 0 ? 'Nothing reported yet. The whole campus is healthy.'
          : `${h.fixed} fixed, ${h.open} still need care${h.urgent ? `, ${h.urgent} urgent` : ''}.`);
      },
      onSelect(key, info, state, label) {
        const msg = { quiet: 'All quiet here.', healthy: 'Everything reported here is fixed.', care: 'Staff are looking after it.', urgent: 'Has an urgent issue being prioritised.' }[state];
        $('#blockCard').innerHTML = `<span class="cn-label">${esc(label)}</span><b>${info.open} open · ${info.fixed} fixed</b><p>${msg}</p><a href="/submit-complaint?block=${encodeURIComponent(key)}">Report here →</a>`;
      }
    });
  }
  const useSample = () => { if (map) { map.update(SAMPLE); $('#sampleTag').hidden = false; } ['#sTotal', '#sResolved', '#sRate'].forEach((s) => set(s, '–')); };
  fetch('/api/public-stats').then((r) => r.json()).then((j) => {
    const s = j && (j.data || j.stats); if (!s) return useSample();
    set('#sTotal', s.total_complaints ?? 0); set('#sResolved', s.resolved_complaints ?? 0);
    set('#sRate', s.resolution_rate_display || `${s.resolution_rate ?? 0}%`);
    if (map) { if (s.block_health) map.update(s.block_health); else { map.update(SAMPLE); $('#sampleTag').hidden = false; } }
  }).catch(useSample);
})();
