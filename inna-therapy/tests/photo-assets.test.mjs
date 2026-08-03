import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');
const content = JSON.parse(readFileSync(join(projectDir, 'content.json'), 'utf8'));

const heroPath = '/images/inna-hero-seated-v3.webp';
const processPaths = [
  '/images/inna-process-abdomen.webp',
  '/images/inna-process-neck.webp',
  '/images/inna-process-posture.webp',
];

function readWebp(relativePath) {
  const absolutePath = join(projectDir, relativePath.replace(/^\//, ''));
  assert.ok(existsSync(absolutePath), `Missing image: ${relativePath}`);
  const image = readFileSync(absolutePath);
  assert.equal(image.toString('ascii', 0, 4), 'RIFF', `${relativePath} is not a WebP`);
  assert.equal(image.toString('ascii', 8, 12), 'WEBP', `${relativePath} is not a WebP`);
  return image;
}

test('uses the approved AI hero image everywhere', () => {
  assert.match(html, new RegExp(`<img src="${heroPath}"`));
  assert.match(html, new RegExp(`property="og:image" content="[^"]+${heroPath}"`));
  assert.match(html, new RegExp(`name="twitter:image" content="[^"]+${heroPath}"`));
  readWebp(heroPath);
});

test('uses the three approved work-process images for locations', () => {
  assert.deepEqual(content.locations.map(({ photo }) => photo), processPaths);
  for (const path of processPaths) {
    assert.ok(html.includes(`src="${path}"`), `Fallback markup does not use ${path}`);
    readWebp(path);
  }
});

test('keeps the four primary photos below a 1.5 MiB transfer budget', () => {
  const totalBytes = [heroPath, ...processPaths]
    .map(readWebp)
    .reduce((total, image) => total + image.length, 0);
  assert.ok(totalBytes <= 1.5 * 1024 * 1024, `Primary photos use ${totalBytes} bytes`);
});
