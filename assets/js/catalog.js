(() => {
  const data = JSON.parse(document.getElementById('products-data').textContent);
  const byId = Object.fromEntries(data.map(p => [p.id, p]));
  const cards = [...document.querySelectorAll('#groups .product')];
  const groups = [...document.querySelectorAll('.catalog-group')];
  const chips = [...document.querySelectorAll('.cat-chip')];
  const brandBtns = [...document.querySelectorAll('.segmented button')];
  const q = document.getElementById('q');
  const meta = document.getElementById('result-meta');
  const empty = document.getElementById('empty');
  const state = { cat: 'all', brand: '', q: '' };

  const plural = n => {
    const a = n % 10, b = n % 100;
    return n + ' ' + (a === 1 && b !== 11 ? 'продукт' : a >= 2 && a <= 4 && (b < 12 || b > 14) ? 'продукта' : 'продуктов');
  };

  function apply() {
    let shown = 0;
    const words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    cards.forEach(c => {
      const ok = (state.cat === 'all' || c.dataset.cats.split(' ').includes(state.cat))
        && (!state.brand || c.dataset.brand === state.brand)
        && words.every(w => c.dataset.search.includes(w));
      c.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(g => {
      const any = g.querySelector('.product:not([hidden])');
      // при выборе категории «эконом»/«масло» товары могут лежать в соседней группе — показываем любую группу с результатами
      g.hidden = !any;
    });
    chips.forEach(ch => ch.classList.toggle('active', ch.dataset.cat === state.cat));
    chips.forEach(ch => ch.setAttribute('aria-selected', ch.dataset.cat === state.cat));
    brandBtns.forEach(b => b.setAttribute('aria-pressed', b.dataset.brand === state.brand));
    meta.textContent = 'Показано ' + plural(shown);
    empty.hidden = shown > 0;
  }

  // Категории, где нет текущего бренда, остаются доступными; бренды без товаров в категории приглушаем
  function updateBrands() {
    brandBtns.forEach(b => {
      if (!b.dataset.brand) return;
      const has = cards.some(c => c.dataset.brand === b.dataset.brand && (state.cat === 'all' || c.dataset.cats.split(' ').includes(state.cat)));
      b.style.display = has ? '' : 'none';
      if (!has && state.brand === b.dataset.brand) state.brand = '';
    });
  }

  function setCat(cat, scroll) {
    state.cat = cat;
    updateBrands();
    apply();
    if (scroll) {
      const top = document.querySelector('.toolbar').getBoundingClientRect().top + scrollY - 120;
      scrollTo({ top, behavior: 'smooth' });
    }
  }

  chips.forEach(ch => ch.addEventListener('click', e => {
    e.preventDefault();
    history.replaceState(null, '', ch.dataset.cat === 'all' ? location.pathname : '#' + ch.dataset.cat);
    setCat(ch.dataset.cat, true);
  }));
  document.querySelectorAll('.subnav-links a').forEach(a => a.addEventListener('click', e => {
    e.preventDefault();
    const cat = a.getAttribute('href').slice(1);
    history.replaceState(null, '', '#' + cat);
    setCat(cat, true);
  }));
  brandBtns.forEach(b => b.addEventListener('click', () => { state.brand = b.dataset.brand; apply(); }));
  q.addEventListener('input', () => { state.q = q.value.trim(); apply(); });
  document.getElementById('reset').addEventListener('click', () => {
    state.brand = ''; state.q = ''; q.value = ''; setCat('all');
  });

  // Карточка товара
  const dlg = document.getElementById('pd');
  function openProduct(id, push) {
    const p = byId[id];
    if (!p) return;
    dlg.querySelector('#pd-img').src = p.img;
    dlg.querySelector('#pd-img').alt = p.name;
    dlg.querySelector('#pd-brand').textContent = p.brand || p.cats[0] || '';
    dlg.querySelector('#pd-title').textContent = p.title;
    const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const secs = p.sections || [];
    const intro = secs.find(s => s[0] === 'Описание');
    const rest = secs.filter(s => s !== intro);
    let html = `<p>${esc(intro ? intro[1] : 'Поставляем оптом со склада в Минской области. Цены и минимальная партия — по запросу.')}</p>`;
    html += rest.map(([t, b]) => `<details><summary>${esc(t)}</summary><p>${esc(b)}</p></details>`).join('');
    dlg.querySelector('#pd-desc').innerHTML = html;
    const specs = [['Категория', p.cats.join(', ')], ['Бренд', p.brand], ['Объём', p.vol], ['Штук в упаковке', p.pack], ['Штрих-код', p.barcode], ['Оплата', 'Безналичная: BYN, RUB, USD, EUR'], ['Доставка', 'Собственный автопарк или самовывоз']]
      .filter(s => s[1]);
    dlg.querySelector('#pd-specs').innerHTML = specs.map(([a, b]) => `<li><span>${a}</span><span>${esc(b)}</span></li>`).join('');
    dlg.querySelector('#pd-request').href = 'contacts.html?product=' + encodeURIComponent(p.name) + '#request';
    if (push) history.replaceState(null, '', '#p-' + id);
    if (!dlg.open) dlg.showModal();
  }
  cards.forEach(c => c.addEventListener('click', e => {
    if (e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    openProduct(+c.dataset.id, true);
  }));
  const close = () => dlg.close();
  document.getElementById('pd-close').addEventListener('click', close);
  dlg.addEventListener('click', e => { if (e.target === dlg) close(); });
  dlg.addEventListener('close', () => {
    if (location.hash.startsWith('#p-')) history.replaceState(null, '', state.cat === 'all' ? location.pathname : '#' + state.cat);
  });

  // Начальное состояние из адреса
  function fromHash() {
    const h = location.hash.slice(1);
    if (h.startsWith('p-')) openProduct(+h.slice(2));
    else if (chips.some(c => c.dataset.cat === h)) setCat(h, true);
  }
  updateBrands();
  apply();
  fromHash();
  addEventListener('hashchange', fromHash);
})();
