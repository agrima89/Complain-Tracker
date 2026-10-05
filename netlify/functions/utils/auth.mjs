/**
 * CampusCare - Authentication & Password Security Module
 * Supports Werkzeug compatible scrypt & pbkdf2 hashes and secure JWT sessions.
 */

import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import { parse as parseCookie, serialize as serializeCookie } from 'cookie';

const JWT_SECRET = process.env.JWT_SECRET || process.env.SESSION_SECRET || 'campuscare_secure_jwt_secret_key_2026_change_in_production';
export const SESSION_COOKIE_NAME = 'campuscare_session';

export const CU_EMAIL_REGEX = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/i;
export const CU_EMAIL_ERROR_MSG = "Please enter a valid email address.";

export function isValidCollegeEmail(email) {
  if (!email || typeof email !== 'string') return { valid: false, message: CU_EMAIL_ERROR_MSG };
  const clean = email.trim();
  if (!CU_EMAIL_REGEX.test(clean)) {
    return { valid: false, message: CU_EMAIL_ERROR_MSG };
  }
  return { valid: true, message: "" };
}

export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const N = 32768, r = 8, p = 1;
  const key = crypto.scryptSync(password, salt, 64, { N, r, p, maxmem: 128 * 1024 * 1024 });
  return `scrypt:${N}:${r}:${p}$${salt}$${key.toString('hex')}`;
}

export function verifyPassword(storedPassword, providedPassword) {
  if (!storedPassword || !providedPassword) return false;

  // 1. Werkzeug scrypt: scrypt:N:r:p$salt$hash
  if (storedPassword.startsWith('scrypt:')) {
    try {
      const parts = storedPassword.split('$');
      const [prefix, N, r, p] = parts[0].split(':').map((v, i) => i === 0 ? v : parseInt(v, 10));
      const salt = parts[1];
      const expectedHash = parts[2];
      const derived = crypto.scryptSync(providedPassword, salt, expectedHash.length / 2, {
        N, r, p, maxmem: 128 * 1024 * 1024
      });
      return crypto.timingSafeEqual(Buffer.from(derived.toString('hex')), Buffer.from(expectedHash));
    } catch (e) {
      console.error("[Auth] scrypt verification error:", e.message);
      return false;
    }
  }

  // 2. Werkzeug pbkdf2: pbkdf2:sha256:iterations$salt$hash
  if (storedPassword.startsWith('pbkdf2:')) {
    try {
      const parts = storedPassword.split('$');
      const algoParts = parts[0].split(':');
      const hashAlgo = algoParts[1] || 'sha256';
      const iterations = parseInt(algoParts[2] || '600000', 10);
      const salt = parts[1];
      const expectedHash = parts[2];
      const derived = crypto.pbkdf2Sync(providedPassword, salt, iterations, expectedHash.length / 2, hashAlgo);
      return crypto.timingSafeEqual(Buffer.from(derived.toString('hex')), Buffer.from(expectedHash));
    } catch (e) {
      console.error("[Auth] pbkdf2 verification error:", e.message);
      return false;
    }
  }

  // 3. Fallback for legacy plaintext (only if stored plaintext matches provided)
  if (storedPassword === providedPassword) {
    return true;
  }

  return false;
}

export function createSessionToken(payload) {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' });
}

export function verifySessionToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (e) {
    return null;
  }
}

export function getSessionFromEvent(event) {
  const headers = event?.headers || {};
  const cookieHeader = headers.cookie || headers.Cookie || headers.COOKIE || '';
  const cookies = parseCookie(cookieHeader);
  let token = cookies[SESSION_COOKIE_NAME];

  if (!token) {
    const authHeader = headers.authorization || headers.Authorization || headers.AUTHORIZATION;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.slice(7).trim();
    }
  }

  if (!token) return { authenticated: false, user: null };

  const decoded = verifySessionToken(token);
  if (!decoded) return { authenticated: false, user: null };

  return { authenticated: true, user: decoded };
}

export function createSessionCookie(token) {
  return serializeCookie(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: 7 * 24 * 60 * 60 // 7 days
  });
}

export function createLogoutCookie() {
  return serializeCookie(SESSION_COOKIE_NAME, '', {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: 0
  });
}
