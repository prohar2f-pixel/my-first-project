import assert from 'node:assert/strict';
import test from 'node:test';

import authHandler from '../api/auth.js';
import callbackHandler from '../api/callback.js';

function responseMock() {
  return {
    headers: {},
    statusCode: 200,
    body: '',
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    status(code) { this.statusCode = code; return this; },
    redirect(location) { this.statusCode = 307; this.headers.location = location; },
    end(body = '') { this.body = body; },
  };
}

test('OAuth authorization uses state, PKCE, a secure cookie and minimum scope', () => {
  process.env.GITHUB_CLIENT_ID = 'client-id';
  process.env.GITHUB_CLIENT_SECRET = 'secret';
  process.env.SITE_URL = 'https://example.test';
  const req = { method: 'GET', headers: {} };
  const res = responseMock();

  authHandler(req, res);

  const url = new URL(res.headers.location);
  assert.equal(url.searchParams.get('scope'), 'public_repo');
  assert.ok(url.searchParams.get('state')?.length >= 32);
  assert.ok(url.searchParams.get('code_challenge')?.length >= 43);
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.match(String(res.headers['set-cookie']), /HttpOnly/i);
  assert.match(String(res.headers['set-cookie']), /Secure/i);
  assert.match(String(res.headers['set-cookie']), /SameSite=Lax/i);
  assert.match(String(res.headers['set-cookie']).split(';')[0], /^[^=]+=([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)$/);
});

test('OAuth callback rejects missing state before exchanging a code', async () => {
  process.env.GITHUB_CLIENT_SECRET = 'secret';
  const originalFetch = global.fetch;
  let called = false;
  global.fetch = async () => { called = true; throw new Error('must not run'); };
  const res = responseMock();
  try {
    await callbackHandler({ method: 'GET', query: { code: 'code' }, headers: {} }, res);
  } finally {
    global.fetch = originalFetch;
  }
  assert.equal(res.statusCode, 400);
  assert.equal(called, false);
  assert.doesNotMatch(res.body, /authorization:github:success/);
});

test('OAuth callback rejects a tampered state cookie', async () => {
  process.env.GITHUB_CLIENT_ID = 'client-id';
  process.env.GITHUB_CLIENT_SECRET = 'secret';
  process.env.SITE_URL = 'https://example.test';
  const authRes = responseMock();
  authHandler({ method: 'GET', headers: {} }, authRes);
  const state = new URL(authRes.headers.location).searchParams.get('state');
  const cookie = String(authRes.headers['set-cookie']).split(';')[0] + 'tampered';
  const originalFetch = global.fetch;
  let called = false;
  global.fetch = async () => { called = true; throw new Error('must not run'); };
  const res = responseMock();
  try {
    await callbackHandler({ method: 'GET', query: { code: 'code', state }, headers: { cookie } }, res);
  } finally {
    global.fetch = originalFetch;
  }
  assert.equal(res.statusCode, 400);
  assert.equal(called, false);
});

test('OAuth callback returns token only to the configured same-origin opener', async () => {
  process.env.GITHUB_CLIENT_ID = 'client-id';
  process.env.GITHUB_CLIENT_SECRET = 'secret';
  process.env.SITE_URL = 'https://example.test';
  const authRes = responseMock();
  authHandler({ method: 'GET', headers: {} }, authRes);
  const state = new URL(authRes.headers.location).searchParams.get('state');
  const cookie = String(authRes.headers['set-cookie']).split(';')[0];
  const originalFetch = global.fetch;
  global.fetch = async (_url, options) => {
    const payload = JSON.parse(options.body);
    assert.equal(payload.code, 'valid-code');
    assert.ok(payload.code_verifier?.length >= 43);
    return { ok: true, json: async () => ({ access_token: 'test-token' }) };
  };
  const res = responseMock();
  try {
    await callbackHandler({ method: 'GET', query: { code: 'valid-code', state }, headers: { cookie } }, res);
  } finally {
    global.fetch = originalFetch;
  }
  assert.equal(res.statusCode, 200);
  assert.equal(res.headers['cache-control'], 'no-store, private');
  assert.equal(res.headers['referrer-policy'], 'no-referrer');
  assert.match(res.body, /https:\/\/example\.test/);
  assert.doesNotMatch(res.body, /postMessage\([^)]*,\s*['"]\*['"]\)/);
  assert.match(res.body, /e\.origin !== targetOrigin/);
  assert.match(res.body, /e\.source !== window\.opener/);
});

test('OAuth callback reports token exchange failure without a fake success', async () => {
  process.env.GITHUB_CLIENT_ID = 'client-id';
  process.env.GITHUB_CLIENT_SECRET = 'secret';
  process.env.SITE_URL = 'https://example.test';
  const authRes = responseMock();
  authHandler({ method: 'GET', headers: {} }, authRes);
  const state = new URL(authRes.headers.location).searchParams.get('state');
  const cookie = String(authRes.headers['set-cookie']).split(';')[0];
  const originalFetch = global.fetch;
  global.fetch = async () => ({ ok: false, status: 401, json: async () => ({ error: 'bad_verification_code' }) });
  const res = responseMock();
  try {
    await callbackHandler({ method: 'GET', query: { code: 'bad', state }, headers: { cookie } }, res);
  } finally {
    global.fetch = originalFetch;
  }
  assert.equal(res.statusCode, 502);
  assert.doesNotMatch(res.body, /authorization:github:success|undefined/);
});
