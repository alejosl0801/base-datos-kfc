self.addEventListener('install',e=>{self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim())});
self.addEventListener('fetch',e=>{
  if(e.request.mode!=='navigate')return;
  e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open('kfc').then(x=>x.put('./index.html',c));return r}).catch(()=>caches.match('./index.html')));
});
