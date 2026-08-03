import assert from 'node:assert/strict';
import test from 'node:test';

import {
  renderLocationCards,
  renderPriceCards,
  safeContactUrl,
  sanitizeRichText,
} from '../content-renderer.js';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');

test('CMS rich text keeps approved formatting but strips executable markup', () => {
  const rendered = sanitizeRichText("Текст<br><span class='accent'>акцент</span><img src=x onerror=alert(1)>");
  assert.equal(rendered, 'Текст<br><span class="accent">акцент</span>&lt;img src=x onerror=alert(1)&gt;');
});

test('CMS price and location cards escape content and unsafe media URLs', () => {
  const prices = renderPriceCards([{ name: '<img onerror=1>', desc: '<script>x</script>', amount: '1000' }]);
  assert.doesNotMatch(prices, /<script|<img onerror/);
  assert.match(prices, /&lt;script&gt;/);

  const locations = renderLocationCards([{ name: 'Кабинет" onerror="1', sub: '<b>x</b>', address: '<svg onload=1>', photo: 'javascript:alert(1)' }]);
  assert.doesNotMatch(locations, /javascript:|<[^>]+\son(?:error|load)=|<b>/);
  assert.match(locations, /&lt;b&gt;/);
});

test('contact links allow only expected protocols', () => {
  assert.equal(safeContactUrl('https://t.me/example'), 'https://t.me/example');
  assert.equal(safeContactUrl('javascript:alert(1)'), '');
  assert.equal(safeContactUrl('data:text/html,x'), '');
});

test('page routes CMS content through the safe renderers', () => {
  assert.match(html, /type="module"/);
  assert.match(html, /renderPriceCards\(data\.prices/);
  assert.match(html, /renderLocationCards\(data\.locations/);
  assert.match(html, /el\.innerHTML = sanitizeRichText\(val\)/);
  assert.doesNotMatch(html, /<h3>\$\{p\.name\}<\/h3>/);
  assert.doesNotMatch(html, /src="\$\{l\.photo/);
});
