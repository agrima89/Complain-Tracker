import { getSessionFromEvent } from './utils/auth.mjs';

export const handler = async (event, context) => {
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
