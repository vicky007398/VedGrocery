(() => {
  const source = document.getElementById('catalog-data');
  if (!source) return;
  // Keep the selected chip in view after a category link loads a new page.
  requestAnimationFrame(() => {
    for (const selector of ['.category-scroll', '.subcategory-scroll']) {
      const strip = document.querySelector(selector);
      const selected = strip?.querySelector('.selected');
      if (!selected) continue;
      const stripLeft = strip.getBoundingClientRect().left;
      const chipLeft = selected.getBoundingClientRect().left;
      strip.scrollLeft += chipLeft - stripLeft - (strip.clientWidth - selected.clientWidth) / 2;
    }
  });
  const config = JSON.parse(document.getElementById('shop-data').textContent);
  let products = JSON.parse(source.textContent);
  const key = 'ved-grocery-shopping-list-v2';
  const olderKey = 'ved-grocery-shopping-list-v1';
  const gu = config.lang === 'gu';
  const messages = gu
    ? { empty: 'તમારી યાદી ખાલી છે', hint: 'ઉમેરવા માટે કોઈ વસ્તુ પર + દબાવો.', order: 'નમસ્તે, મને નીચેની વસ્તુઓ જોઈએ છે:', total: 'અંદાજિત કુલ', check: 'કૃપા કરીને ભાવ અને ઉપલબ્ધતા જણાવો.' }
    : { empty: 'Your list is empty', hint: 'Tap + on an item to add it.', order: 'Hello, I would like these items:', total: 'Estimated total', check: 'Please confirm the price and availability.' };
  const money = value => '₹' + (Math.round(Number(value) * 100) / 100).toLocaleString('en-IN');
  const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const allVariants = () => new Map(products.flatMap(p => p.variants.map(v => [String(v.id), {product:p,variant:v}])));
  function readCart() {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || '{}');
      if (saved && typeof saved === 'object' && !Array.isArray(saved))
        return Object.fromEntries(Object.entries(saved).filter(([id,qty]) => /^\d+$/.test(id) && Number.isInteger(qty) && qty > 0).map(([id,qty]) => [id,Math.min(qty,99)]));
      return {};
    } catch { return {}; }
  }
  let cart = readCart();
  try {
    if (!localStorage.getItem(key)) {
      const old = JSON.parse(localStorage.getItem(olderKey) || '{}');
      for (const [id,qty] of Object.entries(old)) {
        const p = products.find(item => String(item.id) === id);
        if (p && p.variants.length && Number.isInteger(qty) && qty > 0) cart[p.variants[0].id] = Math.min(qty,99);
      }
      localStorage.setItem(key,JSON.stringify(cart));
    }
  } catch { /* private browsing */ }
  const save = () => { try { localStorage.setItem(key,JSON.stringify(cart)); } catch { /* private browsing */ } };
  let lastSync = 0;
  function refreshProducts() {
    if (Date.now() - lastSync < 30000) return;
    lastSync = Date.now();
    fetch('/api/products',{cache:'no-store'}).then(r => r.ok ? r.json() : products)
      .then(data => { products = data; render(); }).catch(() => { lastSync = 0; });
  }
  function render() {
    const map = allVariants();
    const lines = Object.entries(cart).map(([id,qty]) => ({match:map.get(id),id,qty})).filter(x => x.match);
    const subtotal = lines.reduce((sum,x) => sum+x.qty*x.match.variant.price,0);
    const count = lines.reduce((sum,x) => sum+x.qty,0);
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = count; });
    document.querySelector('[data-clear-cart]').disabled = !count;
    document.getElementById('cart-total').textContent = money(subtotal);
    const container = document.getElementById('cart-items');
    if (!lines.length) container.innerHTML = `<div class="cart-empty"><div class="empty-icon">☷</div><h3>${messages.empty}</h3><p>${messages.hint}</p></div>`;
    else container.innerHTML = lines.map(({match:{product:p,variant:v},id,qty}) =>
      `<div class="cart-line"><img src="${escapeHtml(p.image_url||p.fallback_url)}" alt="" onerror="this.onerror=null;this.src='/static/fallback.svg'"><div><strong>${escapeHtml(gu?p.name_gu:p.name_en)}</strong><small>${escapeHtml(v.brand ? v.brand+' · ' : '')}${escapeHtml(gu?v.unit_gu:v.unit_en)} · ${money(v.price)}</small><div class="quantity-control"><button type="button" data-qty="-1" data-id="${id}" aria-label="Remove one">−</button><b>${qty}</b><button type="button" data-qty="1" data-id="${id}" aria-label="Add one">+</button></div></div><span class="cart-line-price">${money(qty*v.price)}</span></div>`).join('');
    const listText = lines.map(({match:{product:p,variant:v},qty}) =>
      `${qty} × ${gu?p.name_gu:p.name_en} ${v.brand ? '('+v.brand+')' : ''} ${gu?v.unit_gu:v.unit_en} — ${money(qty*v.price)}`).join('\n');
    const link = document.getElementById('cart-whatsapp');
    link.href = `https://wa.me/${config.wa}?text=${encodeURIComponent(messages.order+'\n\n'+listText+'\n\n'+messages.total+': '+money(subtotal)+'\n'+messages.check)}`;
    link.classList.toggle('disabled',!lines.length);
    link.setAttribute('aria-disabled',lines.length?'false':'true');
    const checkout = document.getElementById('checkout-total');
    const delivery = document.querySelector('input[name="fulfillment"]:checked')?.value === 'delivery';
    checkout.textContent = money(subtotal+(delivery?Number(config.fee):0));
    const submit = document.getElementById('submit-order');
    submit.disabled = !lines.length || subtotal < Number(config.minimum);
    if (subtotal < Number(config.minimum)) submit.title = 'Minimum order '+money(config.minimum);
    else submit.removeAttribute('title');
  }
  function showCart(open) {
    const drawer = document.querySelector('.cart-drawer');
    drawer.classList.toggle('open',open);
    drawer.setAttribute('aria-hidden',String(!open));
    document.querySelector('.cart-backdrop').hidden = !open;
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) { drawer.querySelector('.close-cart').focus(); refreshProducts(); }
  }
  function deliveryFields() {
    const delivery = document.querySelector('input[name="fulfillment"]:checked')?.value === 'delivery';
    const fields = document.querySelector('.delivery-fields');
    fields.hidden = !delivery;
    fields.querySelector('[name=address]').required = delivery;
    fields.querySelector('[name=pincode]').required = delivery;
    document.querySelector('.pickup-location').hidden = delivery;
    render();
  }
  document.querySelectorAll('input[name="fulfillment"]').forEach(el => el.addEventListener('change',deliveryFields));
  document.querySelectorAll('.variant-select').forEach(select => select.addEventListener('change', () => {
    const card = select.closest('.product-card');
    const match = allVariants().get(select.value);
    if (!match) return;
    const v = match.variant;
    card.querySelector('[data-card-price]').textContent = money(v.price);
    card.querySelector('[data-card-unit]').textContent = '/ '+(gu?v.unit_gu:v.unit_en);
    card.querySelector('[data-add]').dataset.add = v.id;
    card.querySelector('[data-add]').disabled = !v.in_stock;
  }));
  document.addEventListener('click',e => {
    const add = e.target.closest('[data-add]');
    if (add) { const id=add.dataset.add; cart[id]=Math.min(99,(cart[id]||0)+1); save(); render(); showCart(true); return; }
    const change = e.target.closest('[data-qty]');
    if (change) { const id=change.dataset.id; cart[id]=Math.min(99,(cart[id]||0)+Number(change.dataset.qty)); if(cart[id]<=0) delete cart[id]; save(); render(); return; }
    if (e.target.closest('[data-clear-cart]')) {
      if (Object.keys(cart).length && window.confirm(gu ? 'આખી ખરીદીની યાદી ખાલી કરવી છે?' : 'Clear your entire shopping cart?')) {
        cart = {}; save(); render();
      }
      return;
    }
    if (e.target.closest('[data-open-cart]')) showCart(true);
    if (e.target.closest('[data-close-cart]')) showCart(false);
  });
  document.addEventListener('keydown',e => { if(e.key==='Escape') showCart(false); });
  const orderForm = document.getElementById('order-form');
  orderForm.addEventListener('submit',async e => {
    e.preventDefault();
    const error = orderForm.querySelector('.checkout-error');
    error.hidden = true;
    const map = allVariants();
    const items = Object.entries(cart).filter(([id,qty]) => map.has(id) && qty>0).map(([id,qty]) => ({id:Number(id),qty}));
    if (!items.length) return;
    orderForm.querySelector('#cart-json').value = JSON.stringify(items);
    const button = document.getElementById('submit-order');
    button.disabled = true;
    try {
      const response = await fetch(orderForm.action,{method:'POST',body:new FormData(orderForm),credentials:'same-origin'});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error||'Unable to send request.');
      window.location.assign(data.url);
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
      button.disabled = false;
    }
  });
  deliveryFields();
})();
