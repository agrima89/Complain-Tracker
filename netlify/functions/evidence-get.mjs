import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { getEvidenceBlob } from './utils/blobs.mjs';

export const handler = async (event, context) => {
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
  const directKey = event.queryStringParameters?.key;

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

    // Check authorization: Admins have access to all; students only to their complaints
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
      'Cache-Control': 'private, max-age=3600',
      'Content-Disposition': 'inline'
    },
    body: blob.data.toString('base64'),
    isBase64Encoded: true
  };
};
