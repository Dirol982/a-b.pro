(() => {
  // Мобильное меню
  const toggle = document.getElementById('nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open);
    });
    document.querySelectorAll('#nav-links a').forEach(a =>
      a.addEventListener('click', () => { document.body.classList.remove('nav-open'); toggle.setAttribute('aria-expanded', false); }));
    window.addEventListener('keydown', e => { if (e.key === 'Escape') document.body.classList.remove('nav-open'); });
  }

  // Появление блоков при прокрутке
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(el => io.observe(el));
    window.__observeReveal = el => io.observe(el);
  } else reveals.forEach(el => el.classList.add('in'));

  // Счётчики
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const counters = document.querySelectorAll('[data-count]');
  if (!reduce && 'IntersectionObserver' in window) {
    const fmt = n => n.toLocaleString('ru-RU');
    const co = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        const el = en.target, target = +el.dataset.count, t0 = performance.now(), d = 1400;
        const tick = t => {
          const k = Math.min(1, (t - t0) / d), v = Math.round(target * (1 - Math.pow(1 - k, 3)));
          el.textContent = fmt(v);
          if (k < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
        co.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(el => co.observe(el));
  }

  // Горизонтальные карусели
  document.querySelectorAll('[data-scroll]').forEach(btn => {
    const sc = document.getElementById(btn.dataset.scroll);
    if (!sc) return;
    const update = () => {
      document.querySelectorAll(`[data-scroll="${sc.id}"]`).forEach(b => {
        b.disabled = +b.dataset.dir < 0 ? sc.scrollLeft < 4 : sc.scrollLeft + sc.clientWidth >= sc.scrollWidth - 4;
      });
    };
    btn.addEventListener('click', () => sc.scrollBy({ left: +btn.dataset.dir * sc.clientWidth * 0.8, behavior: 'smooth' }));
    sc.addEventListener('scroll', update, { passive: true });
    update();
  });

  // Cookie
  const cookie = document.getElementById('cookie');
  let consent = null;
  try { consent = localStorage.getItem('ab-cookie'); } catch (e) {}
  if (cookie && !consent) {
    setTimeout(() => cookie.classList.add('show'), 1200);
    cookie.querySelectorAll('[data-cookie]').forEach(b => b.addEventListener('click', () => {
      try { localStorage.setItem('ab-cookie', b.dataset.cookie); } catch (e) {}
      cookie.classList.remove('show');
    }));
  }

  // Форма заявки → письмо
  const form = document.getElementById('request-form');
  if (form) {
    form.addEventListener('submit', ev => {
      ev.preventDefault();
      let ok = true;
      form.querySelectorAll('[required]').forEach(i => {
        const bad = !i.value.trim();
        i.setAttribute('aria-invalid', bad);
        if (bad && ok) { i.focus(); ok = false; }
      });
      if (!ok) return;
      const f = new FormData(form);
      const body = [`Имя: ${f.get('name')}`, `Компания: ${f.get('company') || '—'}`, `Телефон: ${f.get('phone')}`,
        `Email: ${f.get('email') || '—'}`, `Интересует: ${f.get('category')}`, '', f.get('message') || ''].join('\n');
      location.href = `mailto:info@a-b.pro?subject=${encodeURIComponent('Заявка с сайта: ' + f.get('category'))}&body=${encodeURIComponent(body)}`;
    });
    const params = new URLSearchParams(location.search);
    if (params.get('product')) {
      const msg = document.getElementById('f-msg');
      msg.value = `Прошу прислать цену и условия поставки: ${params.get('product')}`;
    }
  }
})();
