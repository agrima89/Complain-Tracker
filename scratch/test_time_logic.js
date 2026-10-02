// Test script for CampusCare background time logic
function getCampusBackground(dateObj) {
  const now = dateObj || new Date();
  const hour = now.getHours(); // 0 - 23 in user's local timezone

  if (hour >= 4 && hour < 10) {
    return 'morning';
  } else if (hour >= 10 && hour < 17) {
    return 'afternoon';
  } else if (hour >= 17 && hour < 19) {
    return 'evening';
  } else {
    return 'night';
  }
}

const testCases = [
  { hour: 8, expected: 'morning', label: '8 AM' },
  { hour: 12, expected: 'afternoon', label: '12 PM' },
  { hour: 17, expected: 'evening', label: '5 PM (17:00)' },
  { hour: 21, expected: 'night', label: '9 PM (21:00)' },
  { hour: 2, expected: 'night', label: '2 AM' },
  // Boundaries
  { hour: 4, expected: 'morning', label: '4:00 AM (Morning start)' },
  { hour: 9, expected: 'morning', label: '9:59 AM (Morning end)' },
  { hour: 10, expected: 'afternoon', label: '10:00 AM (Afternoon start)' },
  { hour: 16, expected: 'afternoon', label: '4:59 PM (Afternoon end)' },
  { hour: 17, expected: 'evening', label: '5:00 PM (Evening start)' },
  { hour: 18, expected: 'evening', label: '6:59 PM (Evening end)' },
  { hour: 19, expected: 'night', label: '7:00 PM (Night start)' },
  { hour: 23, expected: 'night', label: '11:00 PM (Night)' },
  { hour: 0, expected: 'night', label: '12:00 AM Midnight (Night)' },
  { hour: 3, expected: 'night', label: '3:59 AM (Night end)' }
];

let allPassed = true;

console.log("=== Testing CampusCare Time Category Schedule ===");
testCases.forEach(tc => {
  const d = new Date();
  d.setHours(tc.hour, 30, 0, 0);
  const result = getCampusBackground(d);
  const pass = result === tc.expected;
  if (!pass) allPassed = false;
  console.log(`[${pass ? 'PASS' : 'FAIL'}] Hour ${tc.hour} (${tc.label}) -> Got: '${result}', Expected: '${tc.expected}'`);
});

if (allPassed) {
  console.log("\nAll 15 test cases passed successfully!");
} else {
  console.error("\nSome test cases failed!");
  process.exit(1);
}
