import { createHash, createHmac, randomBytes } from 'node:crypto';

const COOKIE_NAME = 'inna_oauth';
const DEFAULT_SITE_URL = 'https://my-first-project-rouge-iota.vercel.app';

function siteUrl() {
  return new URL(process.env.SITE_URL || DEFAULT_SITE_URL).origin;
}

function encodeCookie(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const signature = createHmac('sha256', process.env.GITHUB_CLIENT_SECRET).update(body).digest('base64url');
  return `${body}.${signature}`;
}

export default function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store, private');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    res.statusCode = 405;
    res.end('Method Not Allowed');
    return;
  }
  if (!process.env.GITHUB_CLIENT_ID || !process.env.GITHUB_CLIENT_SECRET) {
    res.statusCode = 500;
    res.end('OAuth is not configured');
    return;
  }

  const state = randomBytes(32).toString('base64url');
  const verifier = randomBytes(48).toString('base64url');
  const challenge = createHash('sha256').update(verifier).digest('base64url');
  const origin = siteUrl();
  const params = new URLSearchParams({
    client_id: process.env.GITHUB_CLIENT_ID,
    scope: 'public_repo',
    redirect_uri: `${origin}/api/callback`,
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });

  res.setHeader('Set-Cookie', `${COOKIE_NAME}=${encodeCookie({ state, verifier, createdAt: Date.now() })}; Path=/api; Max-Age=600; HttpOnly; Secure; SameSite=Lax`);
  res.statusCode = 307;
  res.setHeader('Location', `https://github.com/login/oauth/authorize?${params}`);
  res.end();
}
