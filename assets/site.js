// Fade-in scroll observer
const _io = new IntersectionObserver((entries) => {
  let d = 0;
  entries.forEach(e => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('vis'), d);
      d += 85;
      _io.unobserve(e.target);
    }
  });
}, { threshold: 0.08, rootMargin: '0px 0px -36px 0px' });
document.querySelectorAll('.fi').forEach(el => _io.observe(el));

// Mobile nav toggle
const _navToggle = document.getElementById('navToggle');
const _siteNav   = document.getElementById('siteNav');
if (_navToggle && _siteNav) {
  _navToggle.addEventListener('click', () => _siteNav.classList.toggle('open'));
  _siteNav.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => _siteNav.classList.remove('open'))
  );
}
