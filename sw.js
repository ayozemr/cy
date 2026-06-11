/* Service worker: precache de todos los recursos, estrategia cache-first.
   Incrementar CACHE_VERSION al publicar cambios para forzar actualizacion. */
const CACHE_VERSION = 'cy-quiz-v3';
const ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './data.js',
  './manifest.webmanifest',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((cached) =>
      cached ||
      fetch(e.request).then((resp) => {
        if (resp.ok && new URL(e.request.url).origin === location.origin) {
          const copy = resp.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(e.request, copy));
        }
        return resp;
      })
    )
  );
});
