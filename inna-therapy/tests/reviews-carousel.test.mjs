import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');
const cmsConfig = readFileSync(join(projectDir, 'admin/config.yml'), 'utf8');
const content = JSON.parse(readFileSync(join(projectDir, 'content.json'), 'utf8'));
const require = createRequire(import.meta.url);

function loadCarouselApi() {
  try {
    return require('../reviews-carousel.js');
  } catch {
    return null;
  }
}

test('keeps text and audio reviews in independent complete collections', () => {
  assert.ok(content.reviews.length >= 2);
  for (const review of content.reviews) {
    assert.equal(typeof review.text, 'string');
    assert.equal(typeof review.author, 'string');
    assert.equal(typeof review.role, 'string');
    assert.equal(typeof review.photo, 'string');
  }

  assert.ok(content.audio_reviews.length >= 3);
  for (const review of content.audio_reviews) {
    assert.equal(typeof review.author, 'string');
    assert.equal(typeof review.role, 'string');
    assert.equal(typeof review.photo, 'string');
    assert.equal(typeof review.audio, 'string');
    assert.equal(typeof review.duration, 'string');
  }
});

test('renders initials when a client photo is missing', () => {
  const api = loadCarouselApi();
  assert.ok(api, 'reviews-carousel.js must export its rendering API');
  const card = api.renderTextReviewCard({
    text: 'Стало легче двигаться.',
    author: 'Мария, 38 лет',
    role: 'Клиентка',
    photo: '',
  });
  assert.match(card, /review-avatar-fallback[^>]*>М</);
  assert.doesNotMatch(card, /<img/);
});

test('renders real audio only when a file exists', () => {
  const api = loadCarouselApi();
  assert.ok(api, 'reviews-carousel.js must export its rendering API');
  const placeholder = api.renderAudioReviewCard({
    author: 'Клиентка', role: '', photo: '', audio: '', duration: '',
  });
  assert.match(placeholder, /Аудио скоро появится/);
  assert.doesNotMatch(placeholder, /<audio/);

  const playable = api.renderAudioReviewCard({
    author: 'Елена', role: 'Клиентка', photo: '',
    audio: '/audio/elena-review.mp3', duration: '1:24',
  });
  assert.match(playable, /<audio[^>]+controls[^>]+preload="none"/);
  assert.match(playable, /src="\/audio\/elena-review\.mp3"/);
});

test('moves carousel indexes without crossing collection boundaries', () => {
  const api = loadCarouselApi();
  assert.ok(api, 'reviews-carousel.js must export its rendering API');
  assert.equal(api.getNextSlideIndex(0, 3, -1), 2);
  assert.equal(api.getNextSlideIndex(2, 3, 1), 0);
  assert.equal(api.getNextSlideIndex(1, 3, 1), 2);
  assert.equal(api.getNextSlideIndex(0, 0, 1), 0);
});

test('renders text and audio collections into different tracks', () => {
  const api = loadCarouselApi();
  const tracks = {
    'text-reviews': { innerHTML: '', dataset: {} },
    'audio-reviews': { innerHTML: '', dataset: {} },
  };
  const documentStub = {
    getElementById(id) { return tracks[id] ?? null; },
    querySelectorAll() { return []; },
  };

  api.renderReviewCarousels({
    reviews: [{ text: 'Текстовый отзыв', author: 'Мария', role: '', photo: '' }],
    audio_reviews: [{ author: 'Елена', role: '', photo: '', audio: '', duration: '' }],
  }, documentStub);

  assert.match(tracks['text-reviews'].innerHTML, /Текстовый отзыв/);
  assert.doesNotMatch(tracks['text-reviews'].innerHTML, /Аудио скоро появится/);
  assert.match(tracks['audio-reviews'].innerHTML, /Аудио скоро появится/);
  assert.doesNotMatch(tracks['audio-reviews'].innerHTML, /Текстовый отзыв/);
  assert.equal(tracks['text-reviews'].dataset.slideCount, '1');
  assert.equal(tracks['audio-reviews'].dataset.slideCount, '1');
});

test('ships the supplied review photos and playable audio files', () => {
  for (const review of content.reviews) {
    assert.match(review.photo, /^\/images\/reviews\/client-\d+\.webp$/);
    assert.ok(readFileSync(join(projectDir, review.photo.slice(1))).length > 0);
  }
  for (const review of content.audio_reviews) {
    assert.match(review.photo, /^\/images\/reviews\/client-\d+\.webp$/);
    assert.match(review.audio, /^\/audio\/review-\d+\.mp3$/);
    assert.match(review.duration, /^\d+:\d{2}$/);
    assert.ok(readFileSync(join(projectDir, review.photo.slice(1))).length > 0);
    assert.ok(readFileSync(join(projectDir, review.audio.slice(1))).length > 0);
  }
});

test('frames every review avatar with a four-pixel plaque-colored border', () => {
  assert.match(html, /\.review-avatar\s*\{[^}]*border:\s*4px solid #FFD6E7;/s);
  assert.doesNotMatch(html, /\.audio-review-person \.review-avatar\s*\{[^}]*border-width:/s);
});

test('ships two accessible scroll-snap carousels without the fake voice player', () => {
  assert.equal((html.match(/data-review-carousel/g) ?? []).length, 2);
  assert.match(html, /id="text-reviews"[^>]*data-carousel-track/);
  assert.match(html, /id="audio-reviews"[^>]*data-carousel-track/);
  assert.match(html, /src="reviews-carousel\.js"/);
  assert.match(html, /scroll-snap-type:\s*x mandatory/);
  assert.match(html, /:focus-visible/);
  assert.match(html, /prefers-reduced-motion:\s*reduce/);
  assert.doesNotMatch(html, /class="voice-reviews"/);
  assert.doesNotMatch(html, /class="play-btn"/);
});

test('lets the CMS replace every photo and audio placeholder', () => {
  assert.match(cmsConfig, /name: photo, widget: image, required: false/);
  assert.match(cmsConfig, /name: audio_reviews/);
  assert.match(cmsConfig, /name: audio, widget: file, required: false/);
});
