/**
 * CampusCare - Netlify Blobs Evidence Storage Module
 * Stores and retrieves complaint evidence persistently using Netlify Blobs
 * with a local fallback for offline development.
 */

import fs from 'fs';
import path from 'path';
import { getStore } from '@netlify/blobs';

const STORE_NAME = 'campuscare-evidence';
const MAX_UPLOAD_BYTES = 16 * 1024 * 1024; // 16 MB

export function validateImageBuffer(buffer, mimeType = '') {
  if (!buffer || buffer.length === 0) {
    return { valid: false, error: 'Empty file received.' };
  }
  if (buffer.length > MAX_UPLOAD_BYTES) {
    return { valid: false, error: 'File size exceeds maximum limit of 16MB.' };
  }

  // Magic bytes inspection
  const isJpeg = buffer.length >= 3 && buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF;
  const isPng = buffer.length >= 8 &&
    buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47 &&
    buffer[4] === 0x0D && buffer[5] === 0x0A && buffer[6] === 0x1A && buffer[7] === 0x0A;
  const isWebp = buffer.length >= 12 &&
    buffer[0] === 0x52 && buffer[1] === 0x49 && buffer[2] === 0x46 && buffer[3] === 0x46 &&
    buffer[8] === 0x57 && buffer[9] === 0x45 && buffer[10] === 0x42 && buffer[11] === 0x50;

  if (!isJpeg && !isPng && !isWebp) {
    return { valid: false, error: 'Invalid file format. Please upload a genuine JPG, PNG, or WEBP image.' };
  }

  let detectedMime = 'image/jpeg';
  let ext = 'jpg';
  if (isPng) { detectedMime = 'image/png'; ext = 'png'; }
  else if (isWebp) { detectedMime = 'image/webp'; ext = 'webp'; }

  return { valid: true, mimeType: detectedMime, extension: ext };
}

export async function saveEvidenceBlob(buffer, filename, mimeType) {
  const validation = validateImageBuffer(buffer, mimeType);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const rawName = typeof filename === 'string' && filename.trim() ? filename : 'evidence.jpg';
  const cleanFilename = path.basename(rawName).replace(/[^a-zA-Z0-9._-]/g, '_');
  const timestamp = Date.now();
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  const blobKey = `evidence_${timestamp}_${randomSuffix}_${cleanFilename}`;

  // Try saving to Netlify Blobs
  try {
    const store = getStore(STORE_NAME);
    await store.set(blobKey, buffer, {
      metadata: {
        contentType: validation.mimeType,
        originalName: cleanFilename,
        size: buffer.length,
        uploadedAt: new Date().toISOString()
      }
    });
    return {
      key: blobKey,
      filename: cleanFilename,
      mimeType: validation.mimeType,
      size: buffer.length,
      storage: 'blobs'
    };
  } catch (err) {
    // If running in local standalone environment or serverless without Blobs token, fallback to safe disk path
    console.warn("[Blobs] Netlify Blobs storage unavailable, using disk fallback:", err.message);
    const isServerless = !!(
      process.env.NETLIFY ||
      process.env.AWS_LAMBDA_FUNCTION_NAME ||
      process.env.LAMBDA_TASK_ROOT ||
      (process.cwd() && process.cwd().startsWith('/var/task'))
    );
    const uploadsDir = isServerless
      ? path.resolve('/tmp', 'uploads', 'evidence')
      : path.resolve(process.cwd(), 'uploads', 'evidence');

    if (!fs.existsSync(uploadsDir)) {
      try {
        fs.mkdirSync(uploadsDir, { recursive: true });
      } catch (_) {}
    }
    const localFilePath = path.join(uploadsDir, blobKey);
    fs.writeFileSync(localFilePath, buffer);
    return {
      key: blobKey,
      filename: cleanFilename,
      mimeType: validation.mimeType,
      size: buffer.length,
      storage: 'local'
    };
  }
}

export async function getEvidenceBlob(blobKey) {
  if (!blobKey || typeof blobKey !== 'string') return null;
  const cleanKey = path.basename(blobKey);

  // 1. Try Netlify Blobs
  try {
    const store = getStore(STORE_NAME);
    const blob = await store.get(cleanKey, { type: 'arrayBuffer' });
    const metadata = await store.getMetadata(cleanKey);
    if (blob) {
      return {
        data: Buffer.from(blob),
        contentType: metadata?.metadata?.contentType || 'image/jpeg'
      };
    }
  } catch (err) {
    // Continue to local disk check
  }

  // 2. Check /tmp/uploads/evidence (serverless fallback)
  const tmpPath = path.join('/tmp', 'uploads', 'evidence', cleanKey);
  if (fs.existsSync(tmpPath)) {
    const data = fs.readFileSync(tmpPath);
    let contentType = 'image/jpeg';
    if (cleanKey.endsWith('.png')) contentType = 'image/png';
    else if (cleanKey.endsWith('.webp')) contentType = 'image/webp';
    return { data, contentType };
  }

  // 3. Check local uploads/evidence
  const localDir = path.resolve(process.cwd(), 'uploads', 'evidence');
  const localPath = path.join(localDir, cleanKey);
  if (fs.existsSync(localPath)) {
    const data = fs.readFileSync(localPath);
    let contentType = 'image/jpeg';
    if (cleanKey.endsWith('.png')) contentType = 'image/png';
    else if (cleanKey.endsWith('.webp')) contentType = 'image/webp';
    return { data, contentType };
  }

  // 4. Check legacy uploads/complaints
  const legacyDir = path.resolve(process.cwd(), 'uploads', 'complaints');
  const legacyPath = path.join(legacyDir, cleanKey);
  if (fs.existsSync(legacyPath)) {
    const data = fs.readFileSync(legacyPath);
    let contentType = 'image/jpeg';
    if (cleanKey.endsWith('.png')) contentType = 'image/png';
    else if (cleanKey.endsWith('.webp')) contentType = 'image/webp';
    return { data, contentType };
  }

  return null;
}
