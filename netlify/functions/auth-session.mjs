import { toV2 } from './utils/v2.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';

const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      success: true,
      data: session
    })
  };
};

// Modern Netlify Function (gets the Netlify Database connection).
export default toV2(handler);
