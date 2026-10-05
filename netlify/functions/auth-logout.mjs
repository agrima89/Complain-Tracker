import { createLogoutCookie } from './utils/auth.mjs';

export const handler = async (event, context) => {
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
