import { toV2 } from './utils/v2.mjs';
import { createLogoutCookie } from './utils/auth.mjs';

const handler = async (event, context) => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': createLogoutCookie()
    },
    body: JSON.stringify({
      success: true,
      message: 'Logged out successfully',
      redirectUrl: '/login'
    })
  };
};

// Modern Netlify Function (gets the Netlify Database connection).
export default toV2(handler);
