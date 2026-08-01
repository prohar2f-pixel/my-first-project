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
  assert.equal(
    content.texts.approach_p2,
    'Лечебный массаж и работа с мышлением неразделимы: тело хранит все переживания, а психика влияет на здоровье. Работая с причиной боли, вы меняете жизнь на всех уровнях.',
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
    'Акция<br>«Приведи подругу»',
  );
  assert.equal(
    content.texts.offer2_text,
    'Рекомендуйте меня своим подругам. Когда они придут по вашей рекомендации, вы получите бонус: скидку 10% на следующую сессию или бесплатный мини-разбор матрицы судьбы.',
  );
  assert.match(html, /class="referral-text" data-key="offer2_text"/);
  assert.doesNotMatch(html, /class="offer-steps"/);
  assert.doesNotMatch(html, /class="offer-thankyou"/);
});

test('lays out four service cards per row on desktop', () => {
  const pricesGridRule = html.match(/\.prices-grid\s*\{([^}]*)\}/)?.[1] ?? '';
  assert.match(pricesGridRule, /grid-template-columns:\s*repeat\(4,\s*1fr\)/);
});
