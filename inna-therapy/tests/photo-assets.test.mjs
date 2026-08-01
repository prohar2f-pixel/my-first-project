import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');
const content = JSON.parse(readFileSync(join(projectDir, 'content.json'), 'utf8'));

const heroPath = '/images/inna-hero-seated-v3.png';
const processPaths = [
  '/images/inna-process-abdomen.png',
  '/images/inna-process-neck.png',
  '/images/inna-process-posture.png',
];

function readPngSize(relativePath) {
  const absolutePath = join(projectDir, relativePath.replace(/^\//, ''));
  assert.ok(existsSync(absolutePath), `Missing image: ${relativePath}`);
  const image = readFileSync(absolutePath);
  assert.equal(image.toString('ascii', 1, 4), 'PNG', `${relativePath} is not a PNG`);
  return {
    width: image.readUInt32BE(16),
    height: image.readUInt32BE(20),
  };
}

test('uses the approved AI hero image everywhere', () => {
  assert.match(html, new RegExp(`<img src="${heroPath}"`));
  assert.match(html, new RegExp(`property="og:image" content="[^"]+${heroPath}"`));
  assert.match(html, new RegExp(`name="twitter:image" content="[^"]+${heroPath}"`));
  assert.deepEqual(readPngSize(heroPath), { width: 1536, height: 1024 });
});

test('uses the three approved work-process images for locations', () => {
  assert.deepEqual(content.locations.map(({ photo }) => photo), processPaths);
  for (const path of processPaths) {
    assert.ok(html.includes(`src="${path}"`), `Fallback markup does not use ${path}`);
    assert.deepEqual(readPngSize(path), { width: 1024, height: 1536 });
  }
});
