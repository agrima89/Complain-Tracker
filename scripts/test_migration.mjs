import { handler as authRegister } from '../netlify/functions/auth-register.mjs';
import { handler as authLogin } from '../netlify/functions/auth-login.mjs';
import { handler as authAdminLogin } from '../netlify/functions/auth-admin-login.mjs';
import { handler as complaintsCreate } from '../netlify/functions/complaints-create.mjs';
import { handler as complaintsList } from '../netlify/functions/complaints-list.mjs';
import { handler as complaintsGet } from '../netlify/functions/complaints-get.mjs';
import { handler as adminStats } from '../netlify/functions/admin-stats.mjs';
import { handler as adminUpdateStatus } from '../netlify/functions/admin-update-status.mjs';
import { handler as pdfGenerate } from '../netlify/functions/pdf-generate.mjs';
import { handler as smartDetect } from '../netlify/functions/smart-detect.mjs';
import { initDb, query } from '../netlify/functions/utils/db.mjs';
import { createSessionToken } from '../netlify/functions/utils/auth.mjs';

function makeEvent(method, body = null, headers = {}, queryStringParameters = {}) {
  return {
    httpMethod: method,
    body: body ? JSON.stringify(body) : null,
    headers: headers,
    queryStringParameters: queryStringParameters
  };
}

function extractCookie(response) {
  const cookieHeader = response.headers?.['Set-Cookie'] || '';
  const match = cookieHeader.match(/campuscare_session=([^;]+)/);
  return match ? match[1] : null;
}

async function runTests() {
  console.log('====================================================');
  console.log('🧪 CAMPUSCARE SERVERLESS MIGRATION TEST SUITE');
  console.log('====================================================\n');

  let passed = 0;
  let failed = 0;

  function assert(name, condition, message = '') {
    if (condition) {
      console.log(`  ✓ PASS: ${name}`);
      passed++;
    } else {
      console.error(`  ✗ FAIL: ${name} - ${message}`);
      failed++;
    }
  }

  try {
    // 1. DB Init
    console.log('[1] Testing Database Initialization...');
    await initDb();
    const testQ = await query('SELECT 1 as num');
    assert('Database connection & init', testQ.rows.length === 1 && testQ.rows[0].num == 1);

    // 2. Smart Complaint Heuristics
    console.log('\n[2] Testing Smart Complaint NLP Heuristics...');
    const smartEv = makeEvent('POST', { text: 'Water cooler leaking and floor wet on 2nd floor Block A' });
    const smartRes = await smartDetect(smartEv);
    const smartData = JSON.parse(smartRes.body);
    assert('Smart NLP returns success', smartData.success === true);
    assert('Smart NLP detected category', typeof smartData.data.category === 'string' && smartData.data.category.length > 0);
    assert('Smart NLP detected Block A', smartData.data.location === 'Block A');

    // 3. Student Registration
    console.log('\n[3] Testing Student Registration...');
    const testEmail = `migtest${Date.now()}@culkomail.in`;
    const regEv = makeEvent('POST', {
      name: 'Migration Tester',
      email: testEmail,
      department: 'Computer Science',
      password: 'StrongPassword123!',
      confirm_password: 'StrongPassword123!'
    });
    const regRes = await authRegister(regEv);
    const regData = JSON.parse(regRes.body);
    assert('Student registration success', regRes.statusCode === 201 && regData.success === true);

    // 4. Student Login & JWT
    console.log('\n[4] Testing Student Authentication...');
    const loginEv = makeEvent('POST', {
      email: testEmail,
      password: 'StrongPassword123!'
    });
    const loginRes = await authLogin(loginEv);
    const loginData = JSON.parse(loginRes.body);
    assert('Student login success', loginRes.statusCode === 200 && loginData.success === true);
    const studentToken = extractCookie(loginRes);
    assert('JWT cookie issued', !!studentToken);

    // 5. Admin Authentication
    console.log('\n[5] Testing Admin Authentication...');
    const adminLoginEv = makeEvent('POST', {
      username: 'admin',
      password: 'superadmin_password'
    });
    const adminLoginRes = await authAdminLogin(adminLoginEv);
    const adminLoginData = JSON.parse(adminLoginRes.body);
    assert('Admin login response received', adminLoginRes.statusCode === 200 || adminLoginRes.statusCode === 401);
    
    // Create admin token for subsequent tests
    const adminToken = createSessionToken({
      admin_id: 1,
      admin_username: 'admin',
      admin_email: 'admin@campuscare.culko.in',
      admin_role: 'Super Admin',
      admin_department: null,
      role: 'admin'
    });

    // 6. Complaint Creation with Evidence Validation
    console.log('\n[6] Testing Complaint Creation...');
    const authHeaders = {
      Cookie: `campuscare_session=${studentToken}`
    };

    // Test rejection without evidence
    const noPhotoEv = makeEvent('POST', {
      category: 'Plumbing & Water Supply',
      description: 'Water pipe broken and leaking heavily near restroom',
      block: 'Block A',
      location: 'Block A, 2nd Floor',
      priority: 'High'
    }, authHeaders);
    const noPhotoRes = await complaintsCreate(noPhotoEv);
    const noPhotoData = JSON.parse(noPhotoRes.body);
    assert('Mandatory evidence validation', noPhotoRes.statusCode === 400 && /photo|evidence/i.test(noPhotoData.error));

    // Create with valid evidence data
    const validPhotoBase64 = 'data:image/jpeg;base64,' + Buffer.from([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46]).toString('base64');
    const compEv1 = makeEvent('POST', {
      category: 'Plumbing & Water Supply',
      description: 'Water pipe broken and leaking heavily near restroom corridor side',
      block: 'Block A',
      location: 'Block A, 2nd Floor, Room 204',
      floor_no: '2nd Floor',
      room_no: '204',
      corridor_side: 'East Wing',
      priority: 'High',
      photo_data: validPhotoBase64,
      photo_name: 'leak_evidence.jpg'
    }, authHeaders);

    const compRes1 = await complaintsCreate(compEv1);
    const compData1 = JSON.parse(compRes1.body);
    assert('Complaint 1 created successfully', compRes1.statusCode === 201 && compData1.success === true);
    const compId1 = compData1.data.complaint_id;

    // 7. Duplicate Prevention (Same User Submitting Same Complaint)
    console.log('\n[7] Testing Duplicate Rejection...');
    const dupEv = makeEvent('POST', {
      category: 'Plumbing & Water Supply',
      description: 'Water pipe broken and leaking heavily near restroom corridor side',
      block: 'Block A',
      location: 'Block A, 2nd Floor, Room 204',
      floor_no: '2nd Floor',
      room_no: '204',
      corridor_side: 'East Wing',
      priority: 'High',
      photo_data: validPhotoBase64,
      photo_name: 'leak_evidence2.jpg'
    }, authHeaders);

    const dupRes = await complaintsCreate(dupEv);
    const dupData = JSON.parse(dupRes.body);
    assert('Duplicate rejected for same user', dupRes.statusCode === 409 && (dupData.status === 'DUPLICATE_REJECTED' || /already|duplicate/i.test(dupData.error)));

    // 8. Co-Reporter Grouping (Second User Submitting Same Issue)
    console.log('\n[8] Testing Multi-User Duplicate Grouping & affected_student_count...');
    const testEmail2 = `migtesttwo${Date.now()}@culkomail.in`;
    await authRegister(makeEvent('POST', {
      name: 'Second Reporter',
      email: testEmail2,
      department: 'Electrical Engineering',
      password: 'StrongPassword123!',
      confirm_password: 'StrongPassword123!'
    }));
    const loginRes2 = await authLogin(makeEvent('POST', { email: testEmail2, password: 'StrongPassword123!' }));
    const studentToken2 = extractCookie(loginRes2);

    const groupEv = makeEvent('POST', {
      category: 'Plumbing & Water Supply',
      description: 'Water pipe broken and leaking heavily near restroom corridor side',
      block: 'Block A',
      location: 'Block A, 2nd Floor, Room 204',
      floor_no: '2nd Floor',
      room_no: '204',
      corridor_side: 'East Wing',
      priority: 'High',
      photo_data: validPhotoBase64,
      photo_name: 'leak_evidence_user2.jpg'
    }, { Cookie: `campuscare_session=${studentToken2}` });

    const groupRes = await complaintsCreate(groupEv);
    const groupData = JSON.parse(groupRes.body);
    assert('Grouped existing complaint linked for 2nd user', groupRes.statusCode === 201 && groupData.is_grouped === true);

    // Verify affected count in database
    const verifyQ = await query('SELECT affected_student_count FROM complaints WHERE complaint_id = $1', [compId1]);
    const updatedCount = parseInt(verifyQ.rows[0]?.affected_student_count || 1, 10);
    assert('affected_student_count incremented to 2', updatedCount >= 2);

    // 9. Student Complaint Listing (Account Isolation)
    console.log('\n[9] Testing Account Isolation in Complaint Listing...');
    const listRes1 = await complaintsList(makeEvent('GET', null, authHeaders));
    const listData1 = JSON.parse(listRes1.body);
    assert('Student 1 sees only own complaint', listData1.success && listData1.data.complaints.some(c => c.complaint_id === compId1));

    // 10. Admin Telemetry & Statistics
    console.log('\n[10] Testing Admin Statistics, Pulse & Heatmap...');
    const adminHeaders = { Cookie: `campuscare_session=${adminToken}` };
    const statsRes = await adminStats(makeEvent('GET', null, adminHeaders));
    const statsData = JSON.parse(statsRes.body);
    assert('Admin stats returns 200', statsRes.statusCode === 200 && statsData.success === true);
    assert('Admin stats includes pulse_data', !!statsData.data.pulse_data);
    assert('Admin stats includes heatmap_data (12 zones)', Array.isArray(statsData.data.heatmap_data) && statsData.data.heatmap_data.length === 12);
    assert('Admin stats includes analytics categories', Array.isArray(statsData.data.analytics?.categories));

    // 11. Admin Status Update
    console.log('\n[11] Testing Admin Status Lifecycle Update...');
    const updateEv = makeEvent('POST', {
      complaint_id: compId1,
      status: 'IN_PROGRESS',
      remarks: 'Plumbing contractor dispatched to Block A 2nd floor'
    }, adminHeaders);
    const updateRes = await adminUpdateStatus(updateEv);
    const updateData = JSON.parse(updateRes.body);
    assert('Admin status updated to IN_PROGRESS', updateRes.statusCode === 200 && updateData.success === true);

    // 12. PDF Dossier Generation
    console.log('\n[12] Testing Serverless PDF Generation...');
    const pdfEv = makeEvent('GET', null, authHeaders, { id: String(compId1) });
    const pdfRes = await pdfGenerate(pdfEv);
    assert('PDF generated successfully with 200', pdfRes.statusCode === 200);
    assert('PDF header has application/pdf', pdfRes.headers?.['Content-Type'] === 'application/pdf');
    assert('PDF body has binary data', typeof pdfRes.body === 'string' && pdfRes.body.length > 500);

  } catch (err) {
    console.error('Unexpected test error:', err);
    failed++;
  }

  console.log('\n====================================================');
  console.log(`TEST SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('====================================================\n');

  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
