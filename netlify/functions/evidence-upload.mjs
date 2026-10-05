import Busboy from 'busboy';
import { getSessionFromEvent } from './utils/auth.mjs';
import { saveEvidenceBlob, validateImageBuffer } from './utils/blobs.mjs';

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
    };
  }

  const session = getSessionFromEvent(event);
  if (!session.authenticated) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Authentication required.' })
    };
  }

  try {
    const contentType = event.headers['content-type'] || event.headers['Content-Type'] || '';

    // Handle base64 JSON payload
    if (contentType.includes('application/json')) {
      const body = JSON.parse(event.body || '{}');
      if (!body.fileData) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Photo evidence is required to submit this complaint.' })
        };
      }

      const buffer = Buffer.from(body.fileData, 'base64');
      const filename = body.filename || 'evidence.jpg';
      const result = await saveEvidenceBlob(buffer, filename, body.mimeType);

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: true,
          photo_path: result.key,
          filename: result.filename,
          size: result.size
        })
      };
    }

    // Handle multipart/form-data
    if (contentType.includes('multipart/form-data')) {
      const busboy = Busboy({
        headers: {
          'content-type': contentType
        },
        limits: {
          fileSize: 16 * 1024 * 1024
        }
      });

      return new Promise((resolve) => {
        let fileBuffer = null;
        let originalName = 'evidence.jpg';
        let mime = 'image/jpeg';
        let uploadError = null;

        busboy.on('file', (fieldname, file, info) => {
          originalName = info.filename || 'evidence.jpg';
          mime = info.mimeType || 'image/jpeg';
          const chunks = [];

          file.on('data', (data) => chunks.push(data));
          file.on('limit', () => {
            uploadError = 'File size exceeds maximum limit of 16MB.';
          });
          file.on('end', () => {
            fileBuffer = Buffer.concat(chunks);
          });
        });

        busboy.on('error', (err) => {
          resolve({
            statusCode: 400,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ success: false, error: err.message })
          });
        });

        busboy.on('finish', async () => {
          if (uploadError) {
            return resolve({
              statusCode: 400,
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ success: false, error: uploadError })
            });
          }

          if (!fileBuffer || fileBuffer.length === 0) {
            return resolve({
              statusCode: 400,
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ success: false, error: 'Photo evidence is required to submit this complaint.' })
            });
          }

          try {
            const result = await saveEvidenceBlob(fileBuffer, originalName, mime);
            resolve({
              statusCode: 200,
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                success: true,
                photo_path: result.key,
                filename: result.filename,
                size: result.size
              })
            });
          } catch (err) {
            resolve({
              statusCode: 400,
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ success: false, error: err.message })
            });
          }
        });

        const bodyBuffer = event.isBase64Encoded
          ? Buffer.from(event.body, 'base64')
          : Buffer.from(event.body || '', 'utf-8');

        busboy.write(bodyBuffer);
        busboy.end();
      });
    }

    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unsupported Content-Type for file upload' })
    };
  } catch (err) {
    console.error('[evidence-upload] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Server error processing file upload.' })
    };
  }
};
