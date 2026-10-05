const CACHE = 'ved-grocery-shell-v4';
const ASSETS = ['/static/style.css?v=11', '/static/app.js?v=11', '/static/fallback.svg', '/static/manifest.webmanifest', '/static/icon-192.png', '/static/icon-512.png', '/static/offline.html'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;
  const url = new URL(request.url);
  if (request.mode === 'navigate') {
    // Prices and order status must not be served from an old HTML page.
    event.respondWith(fetch(request).catch(() => caches.match('/static/offline.html')));
    return;
  }
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin') || url.pathname.startsWith('/order/') || url.pathname.startsWith('/image/')) return;
  if (url.pathname.startsWith('/static/') && ASSETS.includes(url.pathname + url.search) || ASSETS.includes(url.pathname)) {
    event.respondWith(caches.match(request).then(hit => hit || fetch(request)));
  }
});
