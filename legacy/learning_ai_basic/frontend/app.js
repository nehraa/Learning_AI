// Frontend app.js - handles UI interactions and talks to backend endpoints
const el = (s) => document.querySelector(s);
const htmlEscape = (s) => { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

let recommendations = [];
let filtered = [];

const poolSize = el('#poolSize'); const poolVal = el('#poolVal'); if(poolVal) poolVal.textContent = poolSize.value;
poolSize && (poolSize.oninput = ()=> poolVal.textContent = poolSize.value);

el('#initBtn') && el('#initBtn').addEventListener('click', async ()=>{
  const raw = el('#topicsInput').value.trim(); if(!raw){alert('Please enter topics');return}
  const topics = raw.split('\n').map(s=>s.trim()).filter(Boolean);
  await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topics})});
  el('#topicsList').innerHTML = topics.map(t=>`<div class="chip">${htmlEscape(t)}</div>`).join('');
  el('#topicsCount').textContent = topics.length;
  await refreshRecommendations();
});

el('#refreshBtn') && el('#refreshBtn').addEventListener('click', async ()=>{ await refreshRecommendations(true); });
el('#reloadCourses') && el('#reloadCourses').addEventListener('click', async ()=>{ const r=await fetch('/api/reload-courses',{method:'POST'}); alert('Reloaded courses'); });
el('#clearPrefs') && el('#clearPrefs').addEventListener('click', ()=>{ el('#topicsInput').value=''; el('#topicsList').innerHTML=''; el('#topicsCount').textContent='0'; });
el('#openFetchBtn') && el('#openFetchBtn').addEventListener('click', ()=> refreshRecommendations(true));
el('#shuffleBtn') && el('#shuffleBtn').addEventListener('click', ()=>{ filtered = shuffleArray(filtered); renderRecommendations(); });

el('#searchInput') && el('#searchInput').addEventListener('input', (e)=>{
  const q = e.target.value.toLowerCase();
  filtered = recommendations.filter(r=> (r.title||'').toLowerCase().includes(q) || (r.summary||'').toLowerCase().includes(q) || (r.keywords||[]).join(' ').toLowerCase().includes(q));
  renderRecommendations();
});

el('#modalClose') && el('#modalClose').addEventListener('click', ()=> el('#modal').classList.remove('open'));

async function refreshRecommendations(force=false){
  try{
    if(force) await fetch('/api/refresh-papers',{method:'POST'});
    const res = await fetch('/api/get-recommendations');
    const data = await res.json();
    recommendations = (data.recommendations || []).map(r=>({...r}));
    filtered = [...recommendations];
    el('#shownCount').textContent = filtered.length;
    renderRecommendations();
    updateChart();
    const st = await fetch('/api/status'); const sdata = await st.json(); el('#ratedCount').textContent = sdata.items_rated||0;
  }catch(err){console.error(err);alert('Failed to fetch recommendations')}
}

function renderRecommendations(){
  const box = el('#recommendations'); if(!box) return; box.innerHTML='';
  filtered.forEach(rec=>{
    const div = document.createElement('div'); div.className='rec';
    const kw = (rec.keywords||[]).map(k=>`<span class="badge">${htmlEscape(k)}</span>`).join(' ');
    div.innerHTML = `
      <div class="title">${htmlEscape(rec.title)}</div>
      <div class="meta">${htmlEscape((rec.type||'').toUpperCase())} • ${htmlEscape(rec.url||'')}</div>
      <div class="summary">${htmlEscape(rec.summary||'')}</div>
      <div class="actions">
        <div class="badges">${kw}</div>
        <a class="link" href="#" data-id="${htmlEscape(rec.id)}">Open</a>
      </div>
    `;
    div.querySelector('.link').addEventListener('click',(e)=>{e.preventDefault(); openModal(rec)});
    box.appendChild(div);
  });
  el('#shownCount').textContent = filtered.length;
}

function openModal(rec){
  el('#modalTitle').textContent = rec.title||'';
  el('#modalMeta').textContent = (rec.type||'') + ' • ' + (rec.url||'');
  el('#modalSummary').textContent = rec.summary||'';
  el('#modalKeywords').innerHTML = (rec.keywords||[]).map(k=>`<span class="chip">${htmlEscape(k)}</span>`).join(' ');
  el('#modalLink').href = rec.url || '#';
  el('#modal').classList.add('open');
}

function shuffleArray(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}

let topicChart=null;
function updateChart(){
  try{
    const counts = {};
    recommendations.forEach(r=>{(r.keywords||[]).slice(0,3).forEach(k=>{counts[k]=(counts[k]||0)+1})});
    const labels = Object.keys(counts).slice(0,6);
    const data = labels.map(l=>counts[l]);
    const ctx = document.getElementById('topicChart').getContext('2d');
    if(topicChart) topicChart.destroy();
    topicChart = new Chart(ctx, {
      type: 'bar',
      data: { labels: labels, datasets: [{ label: 'Keyword hits', data: data, backgroundColor: 'rgba(102,126,234,0.7)' }] },
      options: { plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#aab9d9' } }, y: { display: false } } }
    });
  }catch(e){console.warn('chart',e)}
}

(async ()=>{
  try{
    const st = await fetch('/api/status'); const sdata = await st.json();
    if(sdata.topics && sdata.topics.length){ el('#topicsList').innerHTML = sdata.topics.map(t=>`<div class="chip">${htmlEscape(t)}</div>`).join(''); el('#topicsCount').textContent = sdata.topics.length; await refreshRecommendations(); }
  }catch(e){console.log('status check failed')}
})();
