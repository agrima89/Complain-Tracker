// Generates public/login.html, register.html and admin-login.html from one layout.
import fs from 'node:fs';

const head = (title, desc) => `<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="${desc}">
  <meta name="theme-color" content="#09090b">
  <title>${title} · CampusCare</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@400..700&family=Bodoni+Moda:ital,wght@1,500&family=Geist:wght@300..700&family=Geist+Mono:wght@400..600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/theme.css">
  <link rel="stylesheet" href="/static/css/home.css">
  <link rel="stylesheet" href="/static/css/auth-page.css">
</head>`;

const logo = `<span class="h-logo" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M12 2 3 6v6c0 5 3.8 9.3 9 10 5.2-.7 9-5 9-10V6l-9-4Z" stroke="currentColor" stroke-width="1.8"/><path d="m8.5 12 2.5 2.5 4.5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`;

const side = (eyebrow, h1, p, extra) => `
  <aside class="a-side" aria-hidden="false">
    <a href="/" class="h-brand">${logo} CampusCare</a>
    <div>
      <span class="cc-eyebrow"><b>●</b> ${eyebrow}</span>
      <h1 class="cc-display" style="margin-top:1rem">${h1}</h1>
      <p>${p}</p>
      ${extra}
    </div>
    <div class="a-side-stats">
      <div><b id="sideResolved">–</b><span>Issues resolved</span></div>
      <div><b id="sideAvg">–</b><span>Avg first response</span></div>
    </div>
  </aside>`;

const ticket = `
      <div class="a-ticket cc-panel">
        <div class="a-ticket-top"><span>#0142 · Electrical</span><span class="cc-sev info">In progress</span></div>
        <b>Lights flickering, Block C corridor</b>
        <div class="a-track"><i class="on"></i><i class="on"></i><i></i><i></i></div>
        <span class="a-hint">Submitted → Routed → <b style="color:var(--cc-text)">In progress</b> → Resolved</span>
      </div>`;

const pw = (id, label, autocomplete, extra = '') => `
        <div class="a-field">
          <label for="${id}">${label}</label>
          <div class="a-pw">
            <input type="password" id="${id}" name="password" required autocomplete="${autocomplete}" ${extra}>
            <button type="button" data-reveal="${id}" aria-pressed="false" aria-label="Show password">Show</button>
          </div>
          <span class="a-hint warn" id="capsHint" hidden>Caps Lock is on</span>
        </div>`;

const page = (o) => `${head(o.title, o.desc)}
<body class="a-body${o.cls || ''}">
${o.side}
  <main class="a-main">
    <nav class="a-top">${o.top}</nav>
    <div class="a-card">
      <a href="/" class="h-brand" style="display:none" data-mobile-brand>${logo} CampusCare</a>
      <span class="cc-eyebrow">${o.eyebrow}</span>
      <h2 class="cc-display">${o.h2}</h2>
      <p>${o.sub}</p>
      <div id="authAlert" class="a-alert" role="alert" hidden></div>
      <form data-auth-form="${o.mode}" novalidate>
${o.fields}
        <button type="submit" class="cc-btn cc-btn-primary a-submit">${o.cta} <span aria-hidden="true">→</span></button>
      </form>
      <p class="a-alt">${o.alt}</p>
    </div>
  </main>
  <style>@media (max-width:900px){[data-mobile-brand]{display:inline-flex!important;margin-bottom:2.5rem}}</style>
  <script src="/static/js/auth-page.js" defer></script>
</body>
</html>
`;

const pages = {
  'login.html': page({
    mode: 'student', title: 'Student sign in', desc: 'Sign in to CampusCare to report and track campus issues.',
    side: side('Student portal', 'Your campus.<br><span class="cc-accent">Your voice.</span>', 'Track every complaint you have raised, step by step. Nothing is lost in an inbox.', ticket),
    top: '<a href="/">Home</a><a href="/admin-login">Staff</a><a href="/register">Create account</a>',
    eyebrow: 'Welcome back', h2: 'Sign in', sub: 'Use the email you registered with.',
    fields: `
        <div class="a-field">
          <label for="email">University email</label>
          <input type="email" id="email" name="email" required autocomplete="email" inputmode="email" placeholder="you@university.edu" autofocus>
        </div>${pw('password', 'Password', 'current-password')}`,
    cta: 'Sign in', alt: 'New to CampusCare? <a href="/register">Create an account</a>'
  }),
  'register.html': page({
    mode: 'register', title: 'Create account', desc: 'Create a CampusCare account to report campus issues.',
    side: side('Takes 30 seconds', 'Report it once.<br><span class="cc-serif">Watch it get fixed.</span>', 'One account lets you report issues, attach photos, follow progress and confirm when it is fixed.', `
      <ul class="a-hint" style="list-style:none;padding:0;margin:2rem 0 0;display:grid;gap:.7rem;font-size:.92rem;color:var(--cc-text-2)">
        <li>↳ Smart routing to the right department</li><li>↳ Duplicate reports are merged automatically</li><li>↳ A full timeline and a PDF record of every case</li>
      </ul>`),
    top: '<a href="/">Home</a><a href="/login">Sign in</a>',
    eyebrow: 'Get started', h2: 'Create your account', sub: 'Use your university email so departments can reach you.',
    fields: `
        <div class="a-field">
          <label for="name">Full name</label>
          <input type="text" id="name" name="name" required minlength="2" autocomplete="name" placeholder="Aarav Sharma" autofocus>
        </div>
        <div class="a-field">
          <label for="email">University email</label>
          <input type="email" id="email" name="email" required autocomplete="email" inputmode="email" placeholder="you@university.edu">
        </div>${pw('password', 'Password', 'new-password', 'minlength="8"')}
        <div class="a-meter" id="pwMeter" data-score="0" style="margin:-.4rem 0 1rem"><i></i><i></i><i></i><i></i><span></span></div>`,
    cta: 'Create account', alt: 'Already registered? <a href="/login">Sign in</a>'
  }),
  'admin-login.html': page({
    mode: 'admin', cls: ' a-staff', title: 'Staff sign in', desc: 'CampusCare staff and department console sign in.',
    side: side('Staff console', 'Triage, route,<br><span class="cc-accent">resolve.</span>', 'Department staff see only their own queue. The super admin sees everything. Every status change is logged.', `
      <div class="a-ticket cc-panel">
        <div class="a-ticket-top"><span>Today · Electrical</span><span class="cc-sev critical">2 urgent</span></div>
        <b>4 complaints need a decision</b>
        <span class="a-hint">Two point to the same fault in Block C.</span>
      </div>`),
    top: '<a href="/">Home</a><a href="/login">Student sign in</a>',
    eyebrow: 'Authorized staff only', h2: 'Staff sign in', sub: 'Sign in with the department account issued to you.',
    fields: `
        <div class="a-field">
          <label for="username">Username</label>
          <input type="text" id="username" name="username" required autocomplete="username" autocapitalize="off" spellcheck="false" autofocus>
        </div>${pw('password', 'Password', 'current-password')}`,
    cta: 'Open console', alt: 'Are you a student? <a href="/login">Student sign in</a>'
  })
};

for (const [file, html] of Object.entries(pages)) fs.writeFileSync(`public/${file}`, html);
console.log('generated', Object.keys(pages).join(', '));
