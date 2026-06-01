const CACHE = 'supermarché-v7';
const API_CACHE = 'supermarché-api-v1';
const STATIC_EXT = /\.(css|js|json|woff2?|ttf|png|jpg|jpeg|gif|svg|ico|webp)(\?.*)?$/;
const CORE_URLS = [
  '/',
  '/produits/',
  '/vente/',
  '/tableau-de-bord/',
  '/produits/etiquettes/',
  '/static/css/bootstrap.min.css',
  '/static/css/bootstrap-icons.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/chart.umd.min.js',
  '/static/pwa/manifest.json'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(CORE_URLS).catch(() => undefined))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE && k !== API_CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;

  // HTML navigations: network-first, fallback to cache
  if (request.destination === 'document') {
    event.respondWith(
      fetch(request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(request, clone));
        }
        return response;
      }).catch(() => caches.match(request).then(cached => cached || caches.match('/')))
    );
    return;
  }

  // Static assets: cache-first, update in background
  if (!STATIC_EXT.test(url.pathname) && request.destination !== 'font' && request.destination !== 'image') return;

  event.respondWith(
    caches.match(request).then(cached => {
      const fetchPromise = fetch(request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(request, clone));
        }
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
