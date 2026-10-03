(() => {
  const source = document.getElementById('catalog-data');
  if (!source) return;
  const config = JSON.parse(document.getElementById('shop-data').textContent);
  let products = JSON.parse(source.textContent);
  const fallback = '/static/fallback.svg';
  const key = 'ved-grocery-shopping-list-v1';
  const messages = config.lang === 'gu'
    ? { empty: 'તમારી યાદી ખાલી છે', hint: 'ઉમેરવા માટે કોઈ વસ્તુ પર + દબાવો.', order: 'નમસ્તે, મને નીચેની વસ્તુઓ જોઈએ છે:', total: 'અંદાજિત કુલ', check: 'કૃપા કરીને ભાવ અને ઉપલબ્ધતા જણાવો.' }
    : { empty: 'Your list is empty', hint: 'Tap + on any item to add it here.', order: 'Hello, I would like these items:', total: 'Estimated total', check: 'Please confirm the price and availability.' };

  function readCart() {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '{}');
      if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
      return Object.fromEntries(Object.entries(value)
        .filter(([id, qty]) => /^\d+$/.test(id) && Number.isInteger(qty) && qty > 0)
        .map(([id, qty]) => [id, Math.min(qty, 99)]));
    } catch { return {}; }
  }
  let cart = readCart();
  function save() { try { localStorage.setItem(key, JSON.stringify(cart)); } catch { /* private browsing */ } }
  const findItem = id => products.find(p => String(p.id) === String(id));
  const money = number => '₹' + Math.round(number * 100) / 100;
  const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render() {
    const lines = Object.entries(cart).map(([id, qty]) => ({ item: findItem(id), qty, id })).filter(x => x.item);
    const count = lines.reduce((sum, x) => sum + x.qty, 0);
    const total = lines.reduce((sum, x) => sum + x.qty * x.item.price, 0);
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = count; });
    document.getElementById('cart-total').textContent = money(total);
    const container = document.getElementById('cart-items');
    if (!lines.length) {
      container.innerHTML = `<div class="cart-empty"><div class="empty-icon">☷</div><h3>${messages.empty}</h3><p>${messages.hint}</p></div>`;
    } else {
      container.innerHTML = lines.map(({ item, qty, id }) => `<div class="cart-line"><img src="${escapeHtml(item.image_url || item.fallback_url || fallback)}" alt="" onerror="this.onerror=null;this.src='${escapeHtml(item.fallback_url || fallback)}'"><div><strong>${escapeHtml(config.lang === 'gu' ? item.name_gu : item.name_en)}</strong><small>${escapeHtml(config.lang === 'gu' ? item.unit_gu : item.unit_en)} · ${money(item.price)}</small><div class="quantity-control"><button type="button" data-qty="-1" data-id="${id}" aria-label="Remove one">−</button><b>${qty}</b><button type="button" data-qty="1" data-id="${id}" aria-label="Add one">+</button></div></div><span class="cart-line-price">${money(qty * item.price)}</span></div>`).join('');
    }
    const text = `${messages.order}\n\n` + lines.map(({item,qty}) => `${qty} × ${config.lang === 'gu' ? item.name_gu : item.name_en} (${config.lang === 'gu' ? item.unit_gu : item.unit_en}) — ${money(qty * item.price)}`).join('\n') + `\n\n${messages.total}: ${money(total)}\n${messages.check}`;
    const link = document.getElementById('cart-whatsapp');
    link.href = `https://wa.me/${config.wa}?text=${encodeURIComponent(text)}`;
    link.classList.toggle('disabled', !lines.length);
    link.setAttribute('aria-disabled', lines.length ? 'false' : 'true');
  }
  function showCart(open) {
    const drawer = document.querySelector('.cart-drawer');
    drawer.classList.toggle('open', open);
    drawer.setAttribute('aria-hidden', String(!open));
    document.querySelector('.cart-backdrop').hidden = !open;
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) drawer.querySelector('.close-cart').focus();
  }
  document.addEventListener('click', e => {
    const add = e.target.closest('[data-add]');
    if (add) { const id = add.dataset.add; cart[id] = Math.min(99, (cart[id] || 0) + 1); save(); render(); showCart(true); return; }
    const change = e.target.closest('[data-qty]');
    if (change) { const id = change.dataset.id; cart[id] = Math.min(99, (cart[id] || 0) + Number(change.dataset.qty)); if (cart[id] <= 0) delete cart[id]; save(); render(); return; }
    if (e.target.closest('[data-open-cart]')) showCart(true);
    if (e.target.closest('[data-close-cart]')) showCart(false);
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') showCart(false); });
  // Price and stock data come from the live catalog, while only item IDs/quantities live on the device.
  fetch('/api/products', {cache:'no-store'}).then(r => r.ok ? r.json() : products).then(data => { products = data; render(); }).catch(() => render());
  render();
})();
