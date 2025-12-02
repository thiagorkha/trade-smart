// Nome do cache para a versão atual. Mude a versão se modificar os arquivos estáticos.
const CACHE_NAME = 'smart-trader-v1';

// Lista de arquivos estáticos a serem cacheados (incluindo o HTML, CSS e scripts essenciais)
const urlsToCache = [
  './',
  './index.html',
  // O Tailwind CSS CDN não pode ser cacheadado diretamente aqui, mas o navegador fará o cache.
  // Em uma aplicação real, você deve gerenciar os ícones do manifest.json.
  // '/icons/icon-72x72.png',
  // '/icons/icon-512x512.png'
];

// Instalação do Service Worker: Abre o cache e armazena os arquivos essenciais.
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalação...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Cache aberto com sucesso.');
        return cache.addAll(urlsToCache);
      })
      .catch(err => {
        console.error('[Service Worker] Falha ao adicionar ao cache:', err);
      })
  );
});

// Ativação do Service Worker: Remove caches antigos para garantir que a nova versão seja usada.
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Ativação...');
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('[Service Worker] Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Garante que o service worker assume o controle imediatamente
  return self.clients.claim();
});

// Estratégia de cache: Cache First, Network Second
// Tenta obter o recurso do cache primeiro. Se falhar, vai para a rede.
self.addEventListener('fetch', (event) => {
  // Ignora requisições de API (que devem sempre ir para a rede para dados em tempo real)
  if (event.request.url.includes('/api/')) {
    return fetch(event.request);
  }

  // Se não for uma requisição de API, aplica a estratégia Cache First
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Retorna o recurso do cache se encontrado
        if (response) {
          return response;
        }
        // Se não estiver no cache, faz a requisição na rede
        return fetch(event.request).then((response) => {
          // Opcional: Adicionar novas requisições bem-sucedidas ao cache
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });
          return response;
        });
      })
      .catch(() => {
        // Isto é útil se você tiver uma página offline para exibir
        // Por exemplo: return caches.match('/offline.html');
        return new Response('Offline: Não foi possível carregar o recurso.');
      })
  );
});
