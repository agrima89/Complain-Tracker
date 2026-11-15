/* CampusCare "Living Campus" map: one reusable SVG component.
   Usage: CampusMap.mount(el, { data: { 'Block A': {open, urgent, fixed}, ... }, onSelect(name, info) })
   Returns { update(data), select(name) }. */
(function (global) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';

  // Hand-placed layout on an 800 x 500 canvas. Keys match the block values stored on complaints.
  const BLOCKS = [
    { key: 'Academic Block', label: 'Academic', x: 300, y: 150, w: 200, h: 90, icon: 'A' },
    { key: 'Block A', label: 'Block A', x: 90, y: 160, w: 120, h: 70 },
    { key: 'Block B', label: 'Block B', x: 90, y: 270, w: 120, h: 70 },
    { key: 'Block C', label: 'Block C', x: 300, y: 290, w: 95, h: 80 },
    { key: 'Block D', label: 'Block D', x: 405, y: 290, w: 95, h: 80 },
    { key: 'Block E', label: 'Block E', x: 590, y: 160, w: 120, h: 70 },
    { key: 'Block F', label: 'Block F', x: 590, y: 270, w: 120, h: 70 },
    { key: 'Library', label: 'Library', x: 330, y: 50, w: 140, h: 60 },
    { key: 'Hostel', label: 'Hostel', x: 560, y: 395, w: 180, h: 70 },
    { key: 'Sports', label: 'Sports', x: 60, y: 395, w: 190, h: 70, round: true },
    { key: 'Campus', label: 'Mess and grounds', x: 300, y: 405, w: 200, h: 55 }
  ];

  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };

  function istHour() {
    try { return Number(new Intl.DateTimeFormat('en-IN', { hour: 'numeric', hour12: false, timeZone: 'Asia/Kolkata' }).format(new Date())) % 24; }
    catch { return new Date().getHours(); }
  }
  function phase(h = istHour()) {
    if (h >= 5 && h < 11) return { name: 'morning', greet: 'Good morning', icon: '☀' };
    if (h >= 11 && h < 16) return { name: 'afternoon', greet: 'Good afternoon', icon: '◐' };
    if (h >= 16 && h < 19) return { name: 'evening', greet: 'Good evening', icon: '◑' };
    return { name: 'night', greet: 'Good night', icon: '☾' };
  }

  function stateOf(info) {
    if (!info || (!info.open && !info.fixed)) return 'quiet';
    if (info.urgent > 0) return 'urgent';
    if (info.open > 0) return 'care';
    return 'healthy';
  }

  function health(data) {
    let open = 0, fixed = 0, urgent = 0;
    for (const k in data) { open += data[k].open || 0; fixed += data[k].fixed || 0; urgent += data[k].urgent || 0; }
    const total = open + fixed;
    // Weighted: urgent issues hurt more than ordinary open ones.
    const score = total ? Math.max(0, Math.round(100 * (fixed + 0.5 * (open - urgent)) / total)) : 100;
    return { score, open, fixed, urgent };
  }

  function mount(container, opts = {}) {
    const svg = el('svg', { viewBox: '0 0 800 500', class: 'cm-svg', role: 'group', 'aria-label': 'Campus map showing open issues by block' });
    const ph = phase();
    container.classList.add('cm', `cm-${ph.name}`);
    container.dataset.phase = ph.name;

    // Ground, paths and greenery
    el('rect', { x: 0, y: 0, width: 800, height: 500, rx: 24, class: 'cm-ground' }, svg);
    const paths = el('g', { class: 'cm-paths' }, svg);
    ['M40 255 H760', 'M400 20 V480', 'M150 120 V470', 'M650 120 V470', 'M150 380 H650'].forEach((d) => el('path', { d }, paths));
    const trees = el('g', { class: 'cm-trees', 'aria-hidden': 'true' }, svg);
    [[250, 70], [270, 95], [540, 70], [560, 100], [245, 360], [555, 240], [40, 120], [760, 120], [520, 470], [270, 470]]
      .forEach(([cx, cy]) => el('circle', { cx, cy, r: 9 }, trees));

    const blocksG = el('g', {}, svg);
    const nodes = {};
    BLOCKS.forEach((b) => {
      const g = el('g', { class: 'cm-block', tabindex: '0', role: 'button', 'data-key': b.key }, blocksG);
      el('rect', { x: b.x + 4, y: b.y + 6, width: b.w, height: b.h, rx: b.round ? 34 : 12, class: 'cm-shadow' }, g);
      el('rect', { x: b.x, y: b.y, width: b.w, height: b.h, rx: b.round ? 34 : 12, class: 'cm-roof' }, g);
      // window strip for a bit of character
      if (!b.round) for (let i = 0; i < Math.floor(b.w / 22); i++) el('rect', { x: b.x + 12 + i * 22, y: b.y + b.h - 18, width: 10, height: 6, rx: 2, class: 'cm-win' }, g);
      const t = el('text', { x: b.x + 12, y: b.y + 22, class: 'cm-label' }, g); t.textContent = b.label;
      const pin = el('g', { class: 'cm-pin', transform: `translate(${b.x + b.w - 14} ${b.y - 2})` }, g);
      el('circle', { r: 20, class: 'cm-halo' }, pin);
      el('circle', { r: 13, class: 'cm-dot' }, pin);
      const n = el('text', { class: 'cm-count', 'text-anchor': 'middle', dy: '4.5' }, pin);
      nodes[b.key] = { g, pin, n, b };
      const choose = () => api.select(b.key);
      g.addEventListener('click', choose);
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); } });
    });
    container.appendChild(svg);

    let data = {};
    let selected = null;
    const api = {
      phase: ph,
      update(next) {
        data = next || {};
        for (const key in nodes) {
          const info = data[key] || { open: 0, urgent: 0, fixed: 0 };
          const st = stateOf(info);
          const { g, n, b } = nodes[key];
          g.dataset.state = st;
          n.textContent = info.open ? String(info.open) : (info.fixed ? '✓' : '');
          g.setAttribute('aria-label', `${b.label}: ${info.open} open${info.urgent ? `, ${info.urgent} urgent` : ''}, ${info.fixed} fixed`);
        }
        if (opts.onUpdate) opts.onUpdate(health(data));
        if (selected) api.select(selected);
      },
      select(key) {
        selected = key;
        for (const k in nodes) nodes[k].g.classList.toggle('on', k === key);
        const info = data[key] || { open: 0, urgent: 0, fixed: 0 };
        if (opts.onSelect) opts.onSelect(key, info, stateOf(info), nodes[key].b.label);
      }
    };
    api.update(opts.data || {});
    return api;
  }

  global.CampusMap = { mount, phase, health, stateOf, BLOCKS };
})(window);
