/* CampusCare landing page interactions */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* Nav: scroll state + mobile drawer */
  const nav = $('#hNav');
  const onScroll = () => nav && nav.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  const burger = $('#hBurger'), drawer = $('#hDrawer');
  burger?.addEventListener('click', () => {
    const open = drawer.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
  });
  drawer?.addEventListener('click', (e) => { if (e.target.tagName === 'A') { drawer.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); } });

  /* Living campus map */
  const SAMPLE = { 'Block C': { open: 3, urgent: 1, fixed: 4 }, 'Hostel': { open: 2, urgent: 0, fixed: 6 }, 'Library': { open: 0, urgent: 0, fixed: 3 },
    'Academic Block': { open: 1, urgent: 0, fixed: 5 }, 'Block A': { open: 0, urgent: 0, fixed: 2 }, 'Campus': { open: 1, urgent: 0, fixed: 1 } };
  let map = null;
  if (window.CampusMap && $('#campusMap')) {
    const ph = CampusMap.phase();
    document.body.dataset.phase = ph.name;
    const pg = $('#phaseGreet'); if (pg) pg.textContent = ph.greet;
    const pi = $('#phaseIcon'); if (pi) pi.textContent = ph.icon;
    map = CampusMap.mount($('#campusMap'), {
      onUpdate(h) {
        const ring = $('#healthRing'); if (ring) ring.style.setProperty('--p', h.score);
        set($('#healthScore'), h.score);
        const line = $('#healthLine');
        if (line) line.textContent = h.open + h.fixed === 0 ? 'Nothing reported yet. The whole campus is healthy.'
          : `${h.fixed} fixed, ${h.open} still need care${h.urgent ? `, ${h.urgent} urgent` : ''}.`;
      },
      onSelect(key, info, state, label) {
        const msg = { quiet: 'All quiet here. Nothing has been reported.', healthy: 'Everything reported here has been fixed.',
          care: 'Being looked after by staff.', urgent: 'Has an urgent issue that staff are prioritising.' }[state];
        $('#blockCard').innerHTML = `<span class="lv-k cc-mono">${esc(label)}</span><b>${info.open} open · ${info.fixed} fixed</b><p>${msg}</p><a href="/submit-complaint?block=${encodeURIComponent(key)}">Report something here →</a>`;
      }
    });
  }

  function set(el, v) { if (el) { el.classList.remove('cc-skeleton'); el.textContent = v; } }

  /* Reveal on scroll + merge animation */
  const io = new IntersectionObserver((entries) => entries.forEach((en) => {
    if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
  }), { threshold: 0.15 });
  document.querySelectorAll('.cc-reveal').forEach((el) => io.observe(el));
  const merge = $('.h-merge');
  if (merge) new IntersectionObserver(([en]) => merge.classList.toggle('merged', en.isIntersecting), { threshold: .6 }).observe(merge);

  /* Session-aware CTAs */
  fetch('/api/auth-session', { credentials: 'same-origin' }).then((r) => r.ok ? r.json() : null).then((s) => {
    if (!s || !s.authenticated) return;
    const isAdmin = s.user?.role === 'admin';
    const href = isAdmin ? '/admin-dashboard' : '/student-dashboard';
    const label = isAdmin ? 'Open triage console →' : 'Go to my dashboard →';
    ['#heroPrimary', '#finalPrimary'].forEach((id) => { const a = $(id); if (a) { a.href = href; a.textContent = label; } });
    const act = $('#hActions');
    if (act) act.innerHTML = `<span class="h-link-quiet">${esc(s.user?.student_name || s.user?.username || 'Signed in')}</span><a href="${href}" class="cc-btn cc-btn-primary h-cta">Dashboard</a>`;
  }).catch(() => {});

  /* Live stats */
  const countUp = (el, to, suffix = '') => {
    if (!el) return;
    el.classList.remove('cc-skeleton');
    const n = Number(to);
    if (!Number.isFinite(n)) { el.textContent = to; return; }
    const dur = 900, t0 = performance.now();
    const step = (t) => { const p = Math.min(1, (t - t0) / dur); el.textContent = Math.round(n * (1 - Math.pow(1 - p, 3))) + suffix; if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  };
  
  fetch('/api/public-stats').then((r) => r.json()).then((j) => {
    const s = j && (j.data || j.stats); if (!s) throw new Error('no data');
    const rate = s.resolution_rate_display || `${s.resolution_rate ?? 0}%`;
    const avg = s.average_response_display || '--';
    set($('#heroOpen'), s.open_complaints ?? 0);
    if (map) { if (s.block_health && Object.keys(s.block_health).length) map.update(s.block_health); else if (!s.block_health) { map.update(SAMPLE); $('#sampleTag').hidden = false; } else map.update({}); }
    countUp($('#sTotal'), s.total_complaints ?? 0); countUp($('#sResolved'), s.resolved_complaints ?? 0);
    set($('#sRate'), rate); set($('#sAvg'), avg);

    const parts = [
      ['Open', s.open_complaints, 'var(--cc-medium)'], ['In progress', s.in_progress, 'var(--cc-info)'],
      ['Awaiting confirmation', s.awaiting, 'var(--cc-accent-2)'], ['Reopened', s.regenerated, 'var(--cc-critical)'],
      ['Resolved', s.resolved_complaints, 'var(--cc-low)']
    ].map(([l, v, c]) => [l, Number(v) || 0, c]);
    const total = parts.reduce((a, p) => a + p[1], 0);
    $('#pipeBar').innerHTML = total ? parts.filter((p) => p[1]).map(([l, v, c]) => `<i style="flex-grow:${v};background:${c}" title="${l}: ${v}"></i>`).join('') : '';
    $('#pipeLegend').innerHTML = parts.map(([l, v, c]) => `<li><i style="background:${c}"></i>${l}<b>${v}</b></li>`).join('');

    const depts = Object.entries(s.department_activity || {}).sort((a, b) => b[1] - a[1]);
    const max = Math.max(1, ...depts.map((d) => d[1]));
    $('#deptList').innerHTML = depts.length
      ? depts.slice(0, 6).map(([d, c]) => `<li><span>${esc(d)}</span><b>${c}</b><div class="h-conf"><i style="width:${(c / max) * 100}%"></i></div></li>`).join('')
      : '<li style="color:var(--cc-muted)">No complaints recorded yet.</li>';
  }).catch(() => {
    if (map) { map.update(SAMPLE); const t = $('#sampleTag'); if (t) t.hidden = false; }
    ['#heroOpen', '#sTotal', '#sResolved', '#sRate', '#sAvg'].forEach((id) => set($(id), '–'));
    const d = $('#deptList'); if (d) d.innerHTML = '<li style="color:var(--cc-muted)">Live stats are unavailable right now.</li>';
  });

  /* In-browser smart detector (explainable rules) */
  const RULES = [
    { cat: 'Electrical', dept: 'Electrical', kw: ['light', 'fan', 'switch', 'socket', 'power', 'electric', 'wire', 'spark', 'bulb', 'ac ', 'air conditioner', 'projector', 'fuse'] },
    { cat: 'Wi-Fi/Internet', dept: 'Wi-Fi/Internet', kw: ['wifi', 'wi-fi', 'internet', 'network', 'lan', 'router', 'slow net', 'no signal', 'connectivity'] },
    { cat: 'Plumbing & Water Supply', dept: 'Cleaning', kw: ['water', 'leak', 'tap', 'pipe', 'flush', 'drain', 'cooler', 'plumb', 'flood'] },
    { cat: 'Cleanliness & Hygiene', dept: 'Cleaning', kw: ['dirty', 'garbage', 'trash', 'smell', 'clean', 'dust', 'washroom', 'toilet', 'pest', 'cockroach'] },
    { cat: 'Mess/Canteen', dept: 'Hostel', kw: ['mess', 'food', 'canteen', 'meal', 'stale', 'lunch', 'dinner', 'breakfast'] },
    { cat: 'Hostel', dept: 'Hostel', kw: ['hostel', 'warden', 'bed', 'room mate', 'mattress', 'laundry'] },
    { cat: 'Library', dept: 'Library', kw: ['library', 'book', 'reading room', 'librarian'] },
    { cat: 'Classroom', dept: 'Classroom', kw: ['classroom', 'bench', 'desk', 'board', 'lecture', 'chair', 'marker'] },
    { cat: 'Infrastructure & Maintenance', dept: 'Infrastructure', kw: ['door', 'window', 'ceiling', 'wall', 'crack', 'lift', 'elevator', 'stairs', 'roof', 'broken'] },
    { cat: 'Transport Complaint', dept: 'Transport', kw: ['bus', 'transport', 'driver', 'shuttle', 'route'] },
    { cat: 'Security', dept: 'Other', kw: ['theft', 'stolen', 'guard', 'security', 'harass', 'stranger', 'cctv'] }
  ];
  const URGENT = ['spark', 'fire', 'smoke', 'burning', 'shock', 'flood', 'injur', 'danger', 'gas', 'harass', 'collapse'];
  const SOON = ['since morning', 'since yesterday', 'days', 'week', 'not working', 'urgent', 'again', 'exam'];

  function analyse(text) {
    const t = ' ' + text.toLowerCase() + ' ';
    const reasons = [];
    let best = null, bestHits = [];
    for (const r of RULES) {
      const hits = r.kw.filter((k) => t.includes(k));
      if (hits.length > bestHits.length) { best = r; bestHits = hits; }
    }
    if (best) reasons.push(`Matched ${bestHits.map((k) => `“${k.trim()}”`).join(', ')} → ${best.cat}`);
    const urgent = URGENT.filter((k) => t.includes(k));
    const soon = SOON.filter((k) => t.includes(k));
    let sev = 'low', sevLabel = 'Low';
    if (urgent.length) { sev = 'critical'; sevLabel = 'High · safety'; reasons.push(`Safety cue ${urgent.map((k) => `“${k}”`).join(', ')} raises priority`); }
    else if (soon.length) { sev = 'medium'; sevLabel = 'Medium'; reasons.push(`Ongoing-impact cue “${soon[0]}” → Medium`); }
    const room = text.match(/\b([A-F])[-\s]?(\d{2,3})\b/i) || text.match(/\broom\s*(?:no\.?\s*)?(\d{2,4})\b/i);
    const block = text.match(/\b(?:block|hostel)\s*([A-F])\b/i);
    let loc = '—';
    if (room) { loc = room[2] ? `${room[1].toUpperCase()}-${room[2]}` : `Room ${room[1]}`; reasons.push(`Location “${room[0]}” used for duplicate check`); }
    else if (block) { loc = `Block ${block[1].toUpperCase()}`; reasons.push(`Block “${block[0]}” detected`); }
    else if (best) reasons.push('No room number. Adding one helps staff find it faster.');
    const conf = Math.min(98, (best ? 45 + bestHits.length * 15 : 15) + (room || block ? 15 : 0));
    return { best, sev, sevLabel, loc, reasons, conf };
  }

  const input = $('#detInput'), out = $('#detOut');
  function render() {
    const v = input.value.trim();
    if (v.length < 4) { out.innerHTML = '<div class="h-verdict-empty">Start typing. The verdict updates as you go.</div>'; return; }
    const a = analyse(v);
    out.innerHTML = `
      <div class="h-v-row">
        <div><span>Category</span><b>${a.best ? esc(a.best.cat) : 'Other'}</b></div>
        <div><span>Routed to</span><b>${a.best ? esc(a.best.dept) : 'General desk'}</b></div>
        <div><span>Priority</span><b><span class="cc-sev ${a.sev}">${a.sevLabel}</span></b></div>
      </div>
      <div class="h-v-row" style="grid-template-columns:1fr 2fr">
        <div><span>Location</span><b>${esc(a.loc)}</b></div>
        <div><span>Confidence ${a.conf}%</span><div class="h-conf"><i style="width:${a.conf}%"></i></div></div>
      </div>
      <ul class="h-reasons">${(a.reasons.length ? a.reasons : ['No strong keywords yet. Try naming the object or the place.']).map((r) => `<li>${esc(r)}</li>`).join('')}</ul>`;
  }
  input?.addEventListener('input', render);
  document.querySelectorAll('[data-ex]').forEach((b) => b.addEventListener('click', () => { input.value = b.dataset.ex; render(); input.focus(); }));
})();
