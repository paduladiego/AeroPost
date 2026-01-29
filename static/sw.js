const CACHE_NAME = 'aeropost-v3';
const urlsToCache = [
    '/static/img/Logo-A-Box.png',
    '/static/img/Logo-AeroPost-Text.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return Promise.all(
                    urlsToCache.map(url => {
                        return cache.add(url).catch(err => console.log('Erro de cache (ignorado):', url));
                    })
                );
            })
    );
});

self.addEventListener('fetch', event => {
    // Deixa o navegador lidar com tudo. 
    // Removendo o respondWith para evitar bloqueio de redirecionamentos 302.
});
