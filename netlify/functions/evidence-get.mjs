import { toV2 } from './utils/v2.mjs';
import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent, adminCanAccessComplaint } from './utils/auth.mjs';
import { getEvidenceBlob } from './utils/blobs.mjs';

const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Authentication required.' })
    };
  }

  await initDb();

  const complaintId = event.queryStringParameters?.complaint_id || event.queryStringParameters?.id;
  // Fetching by raw storage key skips the ownership check, so only admins may do it.
  const directKey = session.user.role === 'admin' ? event.queryStringParameters?.key : undefined;

  let photoPath = directKey;

  if (complaintId) {
    const compRes = await query('SELECT * FROM complaints WHERE complaint_id = $1', [complaintId]);
    const complaint = compRes.rows[0];

    if (!complaint) {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint not found' })
      };
    }

    if (session.user.role === 'admin' && !adminCanAccessComplaint(session.user, complaint)) {
      return {
        statusCode: 403,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'This complaint belongs to another department.' })
      };
    }

    // Students may only see evidence for complaints they filed or co-reported.
    if (session.user.role !== 'admin') {
      const studentId = session.user.student_id;
      const isOwner = complaint.student_id === studentId;
      const repRes = await query(
        'SELECT 1 FROM complaint_reporters WHERE complaint_id = $1 AND student_id = $2',
        [complaintId, studentId]
      );
      const isReporter = repRes.rows.length > 0;

      if (!isOwner && !isReporter) {
        return {
          statusCode: 403,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Access denied: You are not authorized to view evidence for this complaint.' })
        };
      }
    }

    photoPath = complaint.photo_path;
  }

  if (!photoPath) {
    return {
      statusCode: 404,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'No evidence attached to this complaint' })
    };
  }

  const blob = await getEvidenceBlob(photoPath);
  if (!blob) {
    return {
      statusCode: 404,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Evidence file not found' })
    };
  }

  return {
    statusCode: 200,
    headers: {
      'Content-Type': blob.contentType,
      // Never let a shared (e.g. college lab) browser keep another user's evidence.
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'Content-Disposition': 'inline'
    },
    body: blob.data.toString('base64'),
    isBase64Encoded: true
  };
};

// Modern Netlify Function (gets the Netlify Database connection).
export default toV2(handler);
