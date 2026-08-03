(function attachReviewsCarousel(globalScope) {
  'use strict';

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function getInitial(author) {
    const match = String(author ?? '').trim().match(/[A-Za-zА-Яа-яЁё]/u);
    return match ? match[0].toUpperCase() : '•';
  }

  function normalizeMediaPath(path, kind) {
    const raw = String(path ?? '').trim();
    const roots = kind === 'audio' ? ['audio'] : ['images'];
    const root = roots.join('|');
    const valid = new RegExp(`^/(?:${root})/[A-Za-zА-Яа-яЁё0-9._%+() /-]+$`, 'u').test(raw);
    const safeSegments = raw.split('/').every((segment, index) => index === 0 || (segment && segment !== '.' && segment !== '..'));
    return valid && safeSegments ? raw : '';
  }

  function renderAvatar(review) {
    const author = escapeHtml(review.author || 'Клиентка');
    const photo = normalizeMediaPath(review.photo, 'image');
    if (photo) {
      return `<span class="review-avatar"><img src="${escapeHtml(photo)}" alt="Фото: ${author}" loading="lazy"></span>`;
    }
    return `<span class="review-avatar review-avatar-fallback" aria-label="Фото пока не добавлено">${escapeHtml(getInitial(review.author))}</span>`;
  }

  function renderTextReviewCard(review) {
    return `<article class="review-card review-slide">
      <div class="review-portrait-row">${renderAvatar(review)}<span class="review-quote-mark" aria-hidden="true">“</span></div>
      <blockquote>${escapeHtml(review.text)}</blockquote>
      <div class="review-meta"><strong>${escapeHtml(review.author)}</strong><span>${escapeHtml(review.role)}</span></div>
    </article>`;
  }

  function renderAudioReviewCard(review) {
    const audio = normalizeMediaPath(review.audio, 'audio');
    const player = audio
      ? `<audio class="review-audio" controls preload="none" src="${escapeHtml(audio)}">Ваш браузер не поддерживает аудио.</audio>`
      : '<div class="audio-placeholder" role="status"><span aria-hidden="true">♪</span>Аудио скоро появится</div>';
    const duration = review.duration
      ? `<span class="audio-duration">${escapeHtml(review.duration)}</span>`
      : '';

    return `<article class="audio-review-card review-slide">
      <div class="audio-review-person">${renderAvatar(review)}<div><strong>${escapeHtml(review.author)}</strong><span>${escapeHtml(review.role)}</span></div></div>
      <div class="audio-review-player">${player}${duration}</div>
    </article>`;
  }

  function getNextSlideIndex(current, total, direction) {
    if (!Number.isInteger(total) || total <= 0) return 0;
    return (current + direction + total) % total;
  }

  function initReviewCarousel(root) {
    if (!root || root.dataset.carouselReady === 'true') return;
    const track = root.querySelector('[data-carousel-track]');
    const cards = Array.from(track?.children ?? []);
    const previous = root.querySelector('[data-carousel-prev]');
    const next = root.querySelector('[data-carousel-next]');
    const dots = root.querySelector('[data-carousel-dots]');
    if (!track || !cards.length || !previous || !next || !dots) return;

    let activeIndex = 0;
    const reducedMotion = globalScope.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    dots.innerHTML = cards.map((_, index) => `<button type="button" aria-label="Показать отзыв ${index + 1}" data-carousel-dot="${index}"></button>`).join('');
    const dotButtons = Array.from(dots.children);

    function updateDots() {
      dotButtons.forEach((dot, dotIndex) => {
        dot.setAttribute('aria-current', dotIndex === activeIndex ? 'true' : 'false');
      });
    }

    function show(index) {
      activeIndex = getNextSlideIndex(index, cards.length, 0);
      cards[activeIndex].scrollIntoView({
        behavior: reducedMotion ? 'auto' : 'smooth',
        block: 'nearest',
        inline: 'start',
      });
      updateDots();
    }

    previous.addEventListener('click', () => show(getNextSlideIndex(activeIndex, cards.length, -1)));
    next.addEventListener('click', () => show(getNextSlideIndex(activeIndex, cards.length, 1)));
    dots.addEventListener('click', (event) => {
      const dot = event.target.closest('[data-carousel-dot]');
      if (dot) show(Number(dot.dataset.carouselDot));
    });
    root.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        show(getNextSlideIndex(activeIndex, cards.length, -1));
      }
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        show(getNextSlideIndex(activeIndex, cards.length, 1));
      }
    });
    let scrollFrame = 0;
    track.addEventListener('scroll', () => {
      globalScope.cancelAnimationFrame?.(scrollFrame);
      scrollFrame = globalScope.requestAnimationFrame?.(() => {
        activeIndex = cards.reduce((nearestIndex, card, index) => {
          const currentDistance = Math.abs(card.offsetLeft - track.scrollLeft);
          const nearestDistance = Math.abs(cards[nearestIndex].offsetLeft - track.scrollLeft);
          return currentDistance < nearestDistance ? index : nearestIndex;
        }, 0);
        updateDots();
      }) ?? 0;
    }, { passive: true });

    root.dataset.carouselReady = 'true';
    updateDots();
  }

  function renderReviewCarousels(data, documentScope) {
    const documentRef = documentScope || globalScope.document;
    if (!documentRef) return;
    const textTrack = documentRef.getElementById('text-reviews');
    const audioTrack = documentRef.getElementById('audio-reviews');
    if (textTrack && Array.isArray(data.reviews)) {
      textTrack.innerHTML = data.reviews.map(renderTextReviewCard).join('');
      textTrack.dataset.slideCount = String(data.reviews.length);
    }
    if (audioTrack && Array.isArray(data.audio_reviews)) {
      audioTrack.innerHTML = data.audio_reviews.map(renderAudioReviewCard).join('');
      audioTrack.dataset.slideCount = String(data.audio_reviews.length);
    }
    documentRef.querySelectorAll('[data-review-carousel]').forEach(initReviewCarousel);
  }

  const api = {
    escapeHtml,
    getNextSlideIndex,
    initReviewCarousel,
    normalizeMediaPath,
    renderAudioReviewCard,
    renderReviewCarousels,
    renderTextReviewCard,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else globalScope.ReviewsCarousel = api;
})(typeof window !== 'undefined' ? window : globalThis);
