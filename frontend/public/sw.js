// Simple service worker for PWA caching
const CACHE_NAME = 'astock-v1'

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  )
})

self.addEventListener('fetch', (event) => {
  // Network-first strategy for API calls, cache for static assets
  if (event.request.url.includes('/api/')) {
    return // Don't cache API calls
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        if (response.ok && (event.request.url.endsWith('.js') || event.request.url.endsWith('.css') || event.request.url.endsWith('.woff2'))) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
        }
        return response
      })
    })
  )
})
