self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith('/tcf-tv5monde/')) return;

  const mappedUrl = new URL('/public' + url.pathname, url.origin);
  event.respondWith(fetch(mappedUrl, {
    method: event.request.method,
    headers: event.request.headers,
    cache: event.request.cache,
    credentials: 'same-origin',
    redirect: event.request.redirect
  }));
});
