// DOM substitute: workflow, no automatic API call/save, safe text rendering, stale search.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements={};
function element(tag='div') {return {tag,value:'',textContent:'',children:[],disabled:false,checked:false,handlers:{},
 append(...items){this.children.push(...items)},replaceChildren(...items){this.children=items},focus(){},
 addEventListener(name,handler){this.handlers[name]=handler},reset(){for(const key of ['title','problem','environment','solution'])elements[key].value=''}};}
const html=fs.readFileSync('memory.html','utf8');
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g))elements[id]=element();
elements.backend.value='keyword';
const calls=[];let rows=[],pendingSearch=null,holdSearch=false;
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
  if(action==='search'){if(holdSearch)return new Promise(resolve=>pendingSearch=resolve);return response({state:'candidates',hits:rows.filter(r=>r.status==='verified').map(record=>({record,score:1}))});}
  if(action==='suggest')return response({state:'unverified',suggestion:{title:'API-luonnos',solution:'Kokeile tätä.',limitations:'Ei testattu.'}});
  throw Error(action);
 }};
vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
function all(e){return [e,...e.children.flatMap(all)]}
function findAction(label){return all(elements.records).find(e=>e.tag==='button'&&e.textContent===label);}
(async()=>{
 await settle();assert.deepEqual(calls.map(c=>c.action),['list']);
 elements.problem.value='VPN E42';elements.environment.value='Harjoitusympäristö';
 await elements.suggest.onclick();assert.equal(calls.length,1,'API requires explicit send checkbox');
 elements.consent.checked=true;await elements.suggest.onclick();
 assert.equal(elements.title.value,'API-luonnos');assert(elements.solution.value.includes('Ei testattu.'));
 assert(!calls.some(c=>c.action==='save'),'API response must not auto-save');
 elements.title.value=row.title;
 elements.editor.onsubmit({preventDefault(){}});await settle();
 assert(calls.some(c=>c.action==='save'));assert.equal(rows[0].status,'draft');
 assert(all(elements.records).some(e=>e.tag==='h3'&&e.textContent===row.title));
 assert(!all(elements.records).some(e=>e.tag==='img'),'saved HTML must render as text');
 elements.reviewer.value='Testaaja';await findAction('Vahvista toimivaksi').onclick();
 assert.equal(rows[0].status,'verified');
 elements.query.value='VPN E42';await elements.search.onclick();assert(all(elements.hits).some(e=>e.textContent===row.title));
 elements.query.handlers.input();assert(!all(elements.hits).some(e=>e.textContent===row.title));
 holdSearch=true;const pending=elements.search.onclick();await settle();
 assert(elements.query.disabled,'inputs locked while request is pending');
 elements.query.handlers.input();pendingSearch(response({state:'candidates',hits:[{record:rows[0],score:1}]}));await pending;
 assert(!all(elements.hits).some(e=>e.textContent===row.title),'outdated response must be ignored');
 holdSearch=false;await findAction('Poista käytöstä').onclick();assert.equal(rows[0].status,'retired');
 assert(!findAction('Vahvista toimivaksi'));assert(!findAction('Muokkaa'));assert(!findAction('Poista käytöstä'));
 console.log('Ratkaisumuistin UI: API-lupa, luonnos, vahvistus, haku, poisto, tekstinä renderöinti ja vanhentuneet vastaukset OK (DOM-korvike).');
})().catch(error=>{console.error(error);process.exitCode=1});
