// DOM substitute: workflow, no automatic API call/save, safe text rendering, stale search.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements={};
function element(tag='div') {return {tag,value:'',textContent:'',children:[],disabled:false,checked:false,handlers:{},
 append(...items){this.children.push(...items)},replaceChildren(...items){this.children=items},focus(){},
 addEventListener(name,handler){this.handlers[name]=handler},reset(){for(const key of ['title','problem','environment','solution','operating_system','product','product_version'])elements[key].value=''}};}
const html=fs.readFileSync('memory.html','utf8');
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g))elements[id]=element();
elements.backend.value='keyword';
const calls=[];let rows=[],pendingSearch=null,holdSearch=false,environmentStatus='needs_review',emptySearch=false,mixedSearch=false;
const row={id:'SOL-test',title:'<img src=x onerror=alert(1)>',problem:'VPN E42',environment:'Harjoitusympäristö 5.2',solution:'Testikorjaus',
 status:'draft',revision:1,updated_at:'2026-10-24T10:00:00Z'};
const response=data=>({ok:true,json:async()=>data});
const context={document:{getElementById:id=>elements[id],createElement:element,querySelectorAll:()=>Object.values(elements)},
 window:{confirm:()=>true,prompt:()=> 'Vanhentunut'},fetch:async(url,options)=>{
  const action=url.split('/').pop(),body=JSON.parse(options.body);calls.push({action,body});
  if(action==='list')return response({records:rows});
  if(action==='save'){rows=[{...row,...body}];return response({record:rows[0]});}
  if(action==='verify'){rows=[{...rows[0],status:'verified',revision:2,verified_by:body.verified_by,verified_at:row.updated_at}];return response({record:rows[0]});}
  if(action==='retire'){rows=[{...rows[0],status:'retired',revision:3,retirement_reason:body.reason}];return response({record:rows[0]});}
  if(action==='search'){
   if(holdSearch)return new Promise(resolve=>pendingSearch=resolve);
   const hits=(emptySearch?[]:rows.filter(r=>r.status==='verified')).map(record=>({record,score:1,environment_check:{status:environmentStatus,missing_record_fields:environmentStatus==='needs_review'?['product_version']:[],missing_query_fields:[]}}));
   if(mixedSearch)hits.push({record:{...rows[0],id:'SOL-review',title:'Puutteellinen testiehdokas'},score:.5,environment_check:{status:'needs_review',missing_record_fields:['operating_system'],missing_query_fields:[]}});
   return response({state:'candidates',hits,compatible_hits:hits.filter(hit=>hit.environment_check.status==='declared_match'),review_hits:hits.filter(hit=>hit.environment_check.status==='needs_review')});
  }
  if(action==='suggest')return response({state:'unverified',suggestion:{title:'API-luonnos',solution:'Kokeile tätä.',limitations:'Ei testattu.'}});
  throw Error(action);
 }};
vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
function all(e){return [e,...e.children.flatMap(all)]}
function findAction(label){return all(elements.records).find(e=>e.tag==='button'&&e.textContent===label);}
function candidateGroup(label){return elements.hits.children.find(e=>e.children.some(child=>child.tag==='h3'&&child.textContent===label));}
const compatibleLabel='Ilmoitettujen ympäristötietojen perusteella yhteensopivat ehdokkaat';
const reviewLabel='Puuttuvien tietojen vuoksi tarkistettavat ehdokkaat';

(async()=>{
 await settle();assert.deepEqual(calls.map(c=>c.action),['list']);
 elements['filter-operating_system'].value='Windows 11';elements['filter-product'].value='HarjoitusVPN';elements['filter-product_version'].value='5.2';
 elements.query.value='VPN E42';elements['copy-query'].onclick();
 for(const key of ['operating_system','product','product_version'])assert.equal(elements[key].value,elements['filter-'+key].value,'explicit filters copied to editor');
 elements.problem.value='VPN E42';elements.environment.value='Harjoitusympäristö';
 await elements.suggest.onclick();assert.equal(calls.length,1,'API requires explicit send checkbox');
 elements.consent.checked=true;await elements.suggest.onclick();
 assert.equal(elements.title.value,'API-luonnos');assert(elements.solution.value.includes('Ei testattu.'));
 assert(!calls.some(c=>c.action==='save'),'API response must not auto-save');
 elements.title.value=row.title;
 elements.editor.onsubmit({preventDefault(){}});await settle();
 assert(calls.some(c=>c.action==='save'));assert.equal(rows[0].status,'draft');
 assert.equal(rows[0].operating_system,'Windows 11');assert.equal(rows[0].product,'HarjoitusVPN');assert.equal(rows[0].product_version,'5.2');
 for(const key of ['operating_system','product','product_version'])assert.equal(elements[key].value,'','saved editor reset');
 findAction('Muokkaa').onclick();assert.equal(elements.product_version.value,'5.2');elements.new.onclick();
 assert(all(elements.records).some(e=>e.tag==='h3'&&e.textContent===row.title));
 assert(!all(elements.records).some(e=>e.tag==='img'),'saved HTML must render as text');
 elements.reviewer.value='Testaaja';await findAction('Vahvista toimivaksi').onclick();
 assert.equal(rows[0].status,'verified');
 elements.query.value='VPN E42';await elements.search.onclick();assert(all(elements.hits).some(e=>e.textContent===row.title));
 assert.equal(calls.filter(c=>c.action==='search').at(-1).body.filters.product_version,'5.2');
 assert(all(elements.hits).some(e=>e.textContent.includes('Ympäristö tarkistettava')));
 assert(all(elements.hits).some(e=>e.textContent==='Ratkaisusta puuttuu: tuotteen versio'));
 assert(all(candidateGroup(compatibleLabel)).some(e=>e.textContent.includes('yhteensopivia ehdokkaita ei löytynyt')));
 assert(all(candidateGroup(reviewLabel)).some(e=>e.textContent===row.title));
 assert(all(elements.hits).some(e=>e.textContent.includes('ei takaa ratkaisun toimivuutta')));

 environmentStatus='declared_match';await elements.search.onclick();
 assert(all(elements.hits).some(e=>e.textContent.includes('Käyttöjärjestelmä, tuote ja versio täsmäävät. Tarkista silti')));
 assert(all(candidateGroup(compatibleLabel)).some(e=>e.textContent===row.title));
 assert(!all(candidateGroup(reviewLabel)).some(e=>e.textContent===row.title));
 mixedSearch=true;await elements.search.onclick();
 assert(all(candidateGroup(compatibleLabel)).some(e=>e.textContent===row.title));
 assert(all(candidateGroup(reviewLabel)).some(e=>e.textContent==='Puutteellinen testiehdokas'));
 assert(!all(candidateGroup(compatibleLabel)).some(e=>e.textContent==='Puutteellinen testiehdokas'));mixedSearch=false;

 for(const key of ['operating_system','product','product_version']){
  elements['filter-'+key].handlers.input();assert(!all(elements.hits).some(e=>e.textContent===row.title),'filter changes invalidate results');
  await elements.search.onclick();
 }
 emptySearch=true;await elements.search.onclick();
 assert(all(elements.hits).some(e=>e.textContent.includes('Hakuehdokkaita ei löytynyt')));emptySearch=false;
 elements.query.handlers.input();assert(!all(elements.hits).some(e=>e.textContent===row.title));
 holdSearch=true;const pending=elements.search.onclick();await settle();
 assert(elements.query.disabled,'inputs locked while request is pending');
 elements.query.handlers.input();pendingSearch(response({state:'candidates',hits:[{record:rows[0],score:1}]}));await pending;
 assert(!all(elements.hits).some(e=>e.textContent===row.title),'outdated response must be ignored');
 holdSearch=false;await findAction('Poista käytöstä').onclick();assert.equal(rows[0].status,'retired');
 assert(!findAction('Vahvista toimivaksi'));assert(!findAction('Muokkaa'));assert(!findAction('Poista käytöstä'));
 console.log('Ratkaisumuistin UI: API-lupa, luonnos, vahvistus, haku, poisto, tekstinä renderöinti ja vanhentuneet vastaukset OK (DOM-korvike).');
})().catch(error=>{console.error(error);process.exitCode=1});
