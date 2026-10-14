(function(){
// ---- search over /search-index.json
var idx=null, loading=null;
function load(){ if(idx) return Promise.resolve(idx); if(!loading) loading=fetch('/search-index.json').then(function(r){return r.json()}).then(function(d){idx=d;return d}); return loading; }
function norm(s){ return (s||'').toLowerCase().replace(/[^a-z0-9.x]+/g,' ').trim(); }
function score(item, terms){ var h=norm(item.t+' '+(item.k||'')); var s=0; for(var i=0;i<terms.length;i++){ if(h.indexOf(terms[i])<0) return 0; s+= (' '+h+' ').indexOf(' '+terms[i]+' ')>=0?2:1; } return s - item.t.length/1000; }
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]}); }
document.querySelectorAll('.search-input').forEach(function(inp){
  var box=inp.parentNode.querySelector('.search-results'); var sel=-1;
  function render(list){ sel=-1; if(!list.length){ box.innerHTML='<div class="sr-empty">No matches</div>'; box.hidden=false; return; }
    box.innerHTML=list.map(function(r){ return '<a href="'+r.u+'">'+esc(r.t)+(r.d?'<span>'+esc(r.d)+'</span>':'')+'</a>'; }).join(''); box.hidden=false; }
  inp.addEventListener('input', function(){ var q=norm(inp.value); if(q.length<2){ box.hidden=true; return; }
    load().then(function(d){ var terms=q.split(' '); var out=[]; for(var i=0;i<d.length;i++){ var s=score(d[i],terms); if(s>0) out.push([s,d[i]]); }
      out.sort(function(a,b){return b[0]-a[0]}); render(out.slice(0,10).map(function(x){return x[1]})); }); });
  inp.addEventListener('keydown', function(e){ var links=box.querySelectorAll('a'); if(!links.length) return;
    if(e.key==='ArrowDown'){ sel=Math.min(sel+1,links.length-1); e.preventDefault(); }
    else if(e.key==='ArrowUp'){ sel=Math.max(sel-1,0); e.preventDefault(); }
    else if(e.key==='Enter'){ location.href=(links[sel>=0?sel:0]).getAttribute('href'); e.preventDefault(); return; }
    else if(e.key==='Escape'){ box.hidden=true; return; } else return;
    links.forEach(function(a,i){ a.classList.toggle('active', i===sel); }); });
  document.addEventListener('click', function(e){ if(!inp.parentNode.contains(e.target)) box.hidden=true; });
  var q=new URLSearchParams(location.search).get('q'); if(q && inp.closest('.hero-search')){ inp.value=q; inp.dispatchEvent(new Event('input')); }
});
// ---- sortable tables
document.querySelectorAll('table.sortable').forEach(function(t){
  var ths=t.querySelectorAll('thead th');
  ths.forEach(function(th,col){ th.tabIndex=0; th.setAttribute('role','button'); th.setAttribute('aria-sort','none');
    function go(){ var asc=th.getAttribute('aria-sort')!=='ascending'; ths.forEach(function(o){o.setAttribute('aria-sort','none')}); th.setAttribute('aria-sort', asc?'ascending':'descending');
      var num=th.dataset.sort==='num'; var body=t.tBodies[0]; var rows=Array.prototype.slice.call(body.rows);
      rows.sort(function(a,b){ var x=a.cells[col], y=b.cells[col]; var vx=x.dataset.v!==undefined?x.dataset.v:x.textContent.trim(), vy=y.dataset.v!==undefined?y.dataset.v:y.textContent.trim();
        if(num){ vx=parseFloat(String(vx).replace(/[^0-9.\-]/g,''))||0; vy=parseFloat(String(vy).replace(/[^0-9.\-]/g,''))||0; return asc?vx-vy:vy-vx; }
        return asc?String(vx).localeCompare(vy,undefined,{numeric:true}):String(vy).localeCompare(vx,undefined,{numeric:true}); });
      rows.forEach(function(r){ body.appendChild(r); }); }
    th.addEventListener('click',go); th.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go(); } }); });
});
})();
