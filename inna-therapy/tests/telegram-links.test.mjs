import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');
const cmsConfig = readFileSync(join(projectDir, 'admin/config.yml'), 'utf8');
const content = JSON.parse(readFileSync(join(projectDir, 'content.json'), 'utf8'));

test('routes review visitors to the Telegram channel', () => {
  assert.equal(content.contacts.telegram_channel, 'https://t.me/ladanieInna');
  assert.match(
    html,
    /href="https:\/\/t\.me\/ladanieInna" class="btn-tg" data-contact="telegram_channel"/,
  );
  assert.match(html, /const rawUrl = key === 'prepay' \? c\.prepay_link : c\[key\]/);
});

test('routes questions and direct messages to Inna personal chat', () => {
  assert.equal(content.contacts.telegram, 'https://t.me/httpstmeinnayusmola433');
  assert.equal(
    (html.match(/href="https:\/\/t\.me\/httpstmeinnayusmola433"[^>]+data-contact="telegram"/g) ?? []).length,
    2,
  );
});

test('lets the CMS manage channel and personal Telegram links separately', () => {
  assert.match(cmsConfig, /name: telegram, widget: string/);
  assert.match(cmsConfig, /name: telegram_channel, widget: string/);
});
