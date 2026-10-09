import fs from 'fs';
import path from 'path';

function createMockElement() {
  return {
    textContent: '',
    attrs: {},
    style: {},
    className: '',
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k] || null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    appendChild() {}
  };
}

const mockElements = {
  worldLiveTimeText: createMockElement(),
  worldPhaseSymbol: createMockElement(),
  worldSignatureGreeting: createMockElement(),
  cinematicCampusWorld: createMockElement()
};

const mockDoc = {
  documentElement: createMockElement(),
  getElementById(id) {
    if (!mockElements[id]) {
      mockElements[id] = createMockElement();
    }
    return mockElements[id];
  },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  createElement(tag) { return createMockElement(); },
  addEventListener() {},
  readyState: 'complete'
};

const mockWindow = {
  document: mockDoc,
  matchMedia() { return { matches: false }; },
  addEventListener() {},
  setInterval() { return 123; },
  clearInterval() {},
  requestAnimationFrame() {},
  console: console
};

globalThis.window = mockWindow;
globalThis.document = mockDoc;
globalThis.setInterval = () => 123;
globalThis.clearInterval = () => {};
globalThis.requestAnimationFrame = () => 1;

const campusWorldPath = path.resolve('static', 'js', 'campus-world.js');
const campusWorldCode = fs.readFileSync(campusWorldPath, 'utf8');

eval(campusWorldCode);

console.log('=== TEST 1: Required Times Validation ===');
const validationSuite = [
  { timeStr: '8:00 AM IST',  iso: '2026-10-09T08:00:00+05:30', expectedPhase: 'morning',   expectedLabel: 'MORNING CAMPUS',   expectedGreeting: 'Good morning — campus is active.' },
  { timeStr: '11:38 AM IST', iso: '2026-10-09T11:38:00+05:30', expectedPhase: 'morning',   expectedLabel: 'MORNING CAMPUS',   expectedGreeting: 'Good morning — campus is active.' },
  { timeStr: '11:59 AM IST', iso: '2026-10-09T11:59:00+05:30', expectedPhase: 'morning',   expectedLabel: 'MORNING CAMPUS',   expectedGreeting: 'Good morning — campus is active.' },
  { timeStr: '12:00 PM IST', iso: '2026-10-09T12:00:00+05:30', expectedPhase: 'afternoon', expectedLabel: 'AFTERNOON CAMPUS', expectedGreeting: 'Good afternoon — campus is active.' },
  { timeStr: '3:00 PM IST',  iso: '2026-10-09T15:00:00+05:30', expectedPhase: 'afternoon', expectedLabel: 'AFTERNOON CAMPUS', expectedGreeting: 'Good afternoon — campus is active.' },
  { timeStr: '4:59 PM IST',  iso: '2026-10-09T16:59:00+05:30', expectedPhase: 'afternoon', expectedLabel: 'AFTERNOON CAMPUS', expectedGreeting: 'Good afternoon — campus is active.' },
  { timeStr: '5:00 PM IST',  iso: '2026-10-09T17:00:00+05:30', expectedPhase: 'evening',   expectedLabel: 'EVENING CAMPUS',   expectedGreeting: 'Good evening — campus is active.' },
  { timeStr: '7:59 PM IST',  iso: '2026-10-09T19:59:00+05:30', expectedPhase: 'evening',   expectedLabel: 'EVENING CAMPUS',   expectedGreeting: 'Good evening — campus is active.' },
  { timeStr: '8:00 PM IST',  iso: '2026-10-09T20:00:00+05:30', expectedPhase: 'night',     expectedLabel: 'NIGHT CAMPUS',     expectedGreeting: 'Good night — campus is quiet, but your voice is still heard.' },
  { timeStr: '9:00 PM IST',  iso: '2026-10-09T21:00:00+05:30', expectedPhase: 'night',     expectedLabel: 'NIGHT CAMPUS',     expectedGreeting: 'Good night — campus is quiet, but your voice is still heard.' },
  { timeStr: '12:00 AM IST', iso: '2026-10-09T00:00:00+05:30', expectedPhase: 'night',     expectedLabel: 'NIGHT CAMPUS',     expectedGreeting: 'Good night — campus is quiet, but your voice is still heard.' },
  { timeStr: '4:59 AM IST',  iso: '2026-10-09T04:59:00+05:30', expectedPhase: 'night',     expectedLabel: 'NIGHT CAMPUS',     expectedGreeting: 'Good night — campus is quiet, but your voice is still heard.' },
  { timeStr: '5:00 AM IST',  iso: '2026-10-09T05:00:00+05:30', expectedPhase: 'morning',   expectedLabel: 'MORNING CAMPUS',   expectedGreeting: 'Good morning — campus is active.' }
];

let failed = 0;

for (const t of validationSuite) {
  const d = new Date(t.iso);
  const phase = mockWindow.getCampusBackground(d);
  const formattedTime = mockWindow.formatCampusTime(d);
  const config = mockWindow.WORLD_CONFIG[phase];

  const phaseOk = phase === t.expectedPhase;
  const labelOk = config && config.name === t.expectedLabel;
  const greetingOk = config && config.greeting === t.expectedGreeting;

  // Test setMockTime live DOM updates
  mockWindow.setMockTime(t.iso);
  const liveText = mockElements.worldLiveTimeText.textContent;
  const liveGreeting = mockElements.worldSignatureGreeting.textContent;

  const liveMatches = liveText.includes(t.expectedLabel) && liveGreeting.includes(t.expectedGreeting);

  if (phaseOk && labelOk && greetingOk && liveMatches) {
    console.log(`[PASS] ${t.timeStr.padEnd(14)} -> Phase: ${phase.padEnd(9)} | Label: ${config.name.padEnd(16)} | Time: ${formattedTime} | Display: "${liveText}"`);
  } else {
    failed++;
    console.error(`[FAIL] ${t.timeStr}: phaseOk=${phaseOk}, labelOk=${labelOk}, greetingOk=${greetingOk}, liveMatches=${liveMatches}`);
    console.error(`       Got phase=${phase}, name=${config?.name}, greeting="${config?.greeting}"`);
    console.error(`       Live DOM text="${liveText}", greeting="${liveGreeting}"`);
  }
}

console.log('\n=== TEST 2: Hour by Hour 0 to 23 Verification ===');
for (let h = 0; h < 24; h++) {
  const phase = mockWindow.getPhaseForHour(h);
  let expected;
  if (h >= 5 && h < 12) expected = 'morning';
  else if (h >= 12 && h < 17) expected = 'afternoon';
  else if (h >= 17 && h < 20) expected = 'evening';
  else expected = 'night';

  if (phase !== expected) {
    failed++;
    console.error(`[FAIL] Hour ${h}: expected ${expected}, got ${phase}`);
  }
}
console.log('All 24 hours verified successfully.');

console.log('\n=== TEST 3: Midnight 0 vs 24 Handling ===');
const phase0 = mockWindow.getPhaseForHour(0);
const phase24 = mockWindow.getPhaseForHour(24);
if (phase0 === 'night' && phase24 === 'night') {
  console.log('[PASS] Midnight (0 and 24) handled correctly as "night"');
} else {
  failed++;
  console.error(`[FAIL] Midnight handling: 0=${phase0}, 24=${phase24}`);
}

console.log('\n=== TEST 4: Non-IST System Timezone Resilience ===');
// A date created with UTC midnight is 5:30 AM in IST (Morning)
const utcMidnight = new Date('2026-10-09T00:00:00Z');
const phaseUtc = mockWindow.getCampusBackground(utcMidnight);
const timeUtc = mockWindow.formatCampusTime(utcMidnight);
if (phaseUtc === 'morning' && timeUtc.includes('5:30 AM')) {
  console.log(`[PASS] UTC 00:00 is IST 05:30 AM -> Phase: ${phaseUtc}, Time: ${timeUtc}`);
} else {
  failed++;
  console.error(`[FAIL] UTC conversion failed: phase=${phaseUtc}, time=${timeUtc}`);
}

// A date created with US EST 2:08 AM (11:38 AM IST)
const usEstTime = new Date('2026-10-09T06:08:00Z'); // 6:08 UTC = 11:38 IST
const phaseEst = mockWindow.getCampusBackground(usEstTime);
const timeEst = mockWindow.formatCampusTime(usEstTime);
if (phaseEst === 'morning' && timeEst.includes('11:38 AM')) {
  console.log(`[PASS] UTC 06:08 is IST 11:38 AM -> Phase: ${phaseEst}, Time: ${timeEst}`);
} else {
  failed++;
  console.error(`[FAIL] US/UTC to IST 11:38 AM failed: phase=${phaseEst}, time=${timeEst}`);
}

console.log('\n----------------------------------------');
if (failed === 0) {
  console.log('ALL TESTS PASSED WITH ZERO ERRORS!');
  process.exit(0);
} else {
  console.error(`TEST RUN FAILED with ${failed} errors.`);
  process.exit(1);
}
