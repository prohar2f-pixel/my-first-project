export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

export function sanitizeRichText(value) {
  return escapeHtml(value)
    .replace(/&lt;br\s*\/?&gt;/gi, '<br>')
    .replace(/&lt;span class=(?:&quot;|&#039;)accent(?:&quot;|&#039;)&gt;/gi, '<span class="accent">')
    .replace(/&lt;\/span&gt;/gi, '</span>');
}

export function safeContactUrl(value) {
  const raw = String(value ?? '').trim();
  if (raw === '#') return '#';
  try {
    const url = new URL(raw);
    return url.protocol === 'https:' ? url.href : '';
  } catch {
    return '';
  }
}

export function safeMediaPath(value) {
  const raw = String(value ?? '').trim().replace(/^\//, '');
  const valid = /^images\/[A-Za-zА-Яа-яЁё0-9._%+() -]+(?:\/[A-Za-zА-Яа-яЁё0-9._%+() -]+)*$/u.test(raw);
  const safeSegments = raw.split('/').every((segment) => segment && segment !== '.' && segment !== '..');
  return valid && safeSegments ? raw : '';
}

export function renderPriceCards(prices, icons = []) {
  const fallbackIcon = icons[1] || '';
  return (Array.isArray(prices) ? prices : []).map((price, index) => `
    <div class="price-card">
      <div class="p-icon">${icons[index] || fallbackIcon}</div>
      <h3>${escapeHtml(price.name)}</h3>
      <p class="p-desc">${escapeHtml(price.desc)}</p>
      <div class="p-amount">${escapeHtml(price.amount)}</div>
    </div>`).join('');
}

export function renderLocationCards(locations, icons = {}) {
  const { home = '', lotus = '', pin = '' } = icons;
  return (Array.isArray(locations) ? locations : []).map((location) => {
    const photo = safeMediaPath(location.photo);
    const image = photo ? `<img src="${escapeHtml(photo)}" alt="${escapeHtml(location.name)}" loading="lazy">` : '';
    return `
      <div class="location-card">
        <div class="loc-photo">${image}</div>
        <div class="loc-content">
          <div class="loc-icon-circle">${home}</div>
          <span class="loc-label">${escapeHtml(location.sub)}</span>
          <h3 class="loc-name">${escapeHtml(location.name)}</h3>
          <div class="loc-lotus">${lotus}</div>
          <div class="loc-address">${pin}<p>${escapeHtml(location.address)}</p></div>
        </div>
      </div>`;
  }).join('');
}
