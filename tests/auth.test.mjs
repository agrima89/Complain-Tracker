import test from 'node:test';
import assert from 'node:assert/strict';
process.env.JWT_SECRET ||= 'test-secret';
const { adminCanAccessComplaint } = await import('../netlify/functions/utils/auth.mjs');

test('super admin can access any complaint', () => {
  assert.equal(adminCanAccessComplaint({ admin_department: '' }, { department: 'Hostel' }), true);
});

test('department admin is limited to their department', () => {
  const user = { admin_department: 'Cleaning' };
  assert.equal(adminCanAccessComplaint(user, { department: 'cleaning', category: 'Plumbing & Water Supply' }), true);
  assert.equal(adminCanAccessComplaint(user, { department: 'Hostel', category: 'Hostel' }), false);
});
