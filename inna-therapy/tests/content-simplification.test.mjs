import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const projectDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(projectDir, 'index.html'), 'utf8');
const content = JSON.parse(readFileSync(join(projectDir, 'content.json'), 'utf8'));

test('shows the approved plain-language positioning and result', () => {
  assert.equal(
    content.texts.about_p2,
    'Мой подход объединяет работу с телом, мышлением и родовыми программами, чтобы вернуть вам лёгкость, радость и жизнь без боли.',
  );
  assert.equal(
    content.texts.steps_result,
    'ясность, лёгкость, свобода движений, устранение боли и возможность достичь желаемого',
  );
});

test('uses the approved specialty names', () => {
  assert.deepEqual(content.specialties.slice(0, 4), [
    'Терапевт телесной практики (лечебный массаж)',
    'Нейросоматолог',
    'Психолог',
    'Работа с образом боли (устраняю боль)',
  ]);
});

test('removes the four-session tariff from data and fallback markup', () => {
  assert.equal(content.prices.some(({ name }) => name === '4 сеанса'), false);
  assert.doesNotMatch(html, /<h3>4 сеанса<\/h3>/);
});

test('shows a compact referral offer without the old steps', () => {
  assert.equal(
    content.texts.offer2_title,
    'Приведите подругу —<br>получите приятный бонус!',
  );
  assert.doesNotMatch(html, /class="offer-steps"/);
  assert.doesNotMatch(html, /class="offer-thankyou"/);
});
