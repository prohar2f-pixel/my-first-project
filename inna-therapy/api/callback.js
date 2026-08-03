import { createHmac, timingSafeEqual } from 'node:crypto';

const COOKIE_NAME = 'inna_oauth';
const DEFAULT_SITE_URL = 'https://my-first-project-rouge-iota.vercel.app';

function siteUrl() {
  return new URL(process.env.SITE_URL || DEFAULT_SITE_URL).origin;
}

function readCookie(header = '') {
  const match = String(header).split(';').map((part) => part.trim()).find((part) => part.startsWith(`${COOKIE_NAME}=`));
  if (!match) return null;
  try {
    const [body, signature, ...extra] = match.slice(COOKIE_NAME.length + 1).split('.');
    if (!body || !signature || extra.length || !process.env.GITHUB_CLIENT_SECRET) return null;
    const expected = createHmac('sha256', process.env.GITHUB_CLIENT_SECRET).update(body).digest('base64url');
    if (!equalSecret(signature, expected)) return null;
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    if (!Number.isFinite(payload.createdAt) || Date.now() - payload.createdAt > 600_000 || payload.createdAt > Date.now() + 30_000) return null;
    return payload;
  } catch {
    return null;
  }
}

function equalSecret(left, right) {
  const a = Buffer.from(String(left || ''));
  const b = Buffer.from(String(right || ''));
  return a.length > 0 && a.length === b.length && timingSafeEqual(a, b);
}

function fail(res, statusCode, message) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.end(message);
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store, private');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Set-Cookie', `${COOKIE_NAME}=; Path=/api; Max-Age=0; HttpOnly; Secure; SameSite=Lax`);
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    fail(res, 405, 'Method Not Allowed');
    return;
  }

  const code = typeof req.query?.code === 'string' ? req.query.code : '';
  const state = typeof req.query?.state === 'string' ? req.query.state : '';
  const saved = readCookie(req.headers?.cookie);
  if (!code || !state || !saved?.state || !saved?.verifier || !equalSecret(state, saved.state)) {
    fail(res, 400, 'Invalid OAuth request');
    return;
  }
  if (!process.env.GITHUB_CLIENT_ID || !process.env.GITHUB_CLIENT_SECRET) {
    fail(res, 500, 'OAuth is not configured');
    return;
  }

  const origin = siteUrl();
  let tokenResponse;
  try {
    tokenResponse = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        client_id: process.env.GITHUB_CLIENT_ID,
        client_secret: process.env.GITHUB_CLIENT_SECRET,
        code,
        redirect_uri: `${origin}/api/callback`,
        code_verifier: saved.verifier,
      }),
    });
  } catch {
    fail(res, 502, 'GitHub authentication failed');
    return;
  }

  let payload = {};
  try { payload = await tokenResponse.json(); } catch { /* handled below */ }
  if (!tokenResponse.ok || typeof payload.access_token !== 'string' || !payload.access_token) {
    fail(res, 502, 'GitHub authentication failed');
    return;
  }

  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'");
  res.end(`<!DOCTYPE html><html><body><script>
(function() {
  var targetOrigin = ${JSON.stringify(origin)};
  var token = ${JSON.stringify(payload.access_token)};
  var msg = 'authorization:github:success:' + JSON.stringify({ token: token, provider: 'github' });
  function receiveMessage(e) {
    if (e.origin !== targetOrigin || e.source !== window.opener) return;
    window.opener.postMessage(msg, targetOrigin);
  }
  window.addEventListener('message', receiveMessage, false);
  if (window.opener) window.opener.postMessage('authorizing:github', targetOrigin);
})();
<\/script></body></html>`);
}
