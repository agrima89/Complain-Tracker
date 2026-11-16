// Temporary diagnostic: reports only whether the Netlify Database URL is visible to v2 functions.
export default async () => {
  const viaNetlify = !!(globalThis.Netlify?.env?.get?.('NETLIFY_DB_URL'));
  const viaProcess = !!process.env.NETLIFY_DB_URL;
  return Response.json({ viaNetlify, viaProcess });
};
