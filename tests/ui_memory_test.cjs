// Local DOM contract/workflow tests. No browser, network or external API is used.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {test}=require('node:test');
const html=fs.readFileSync('memory.html','utf8');
const fields=['title','problem','environment','solution','operating_system','product','product_version'];
const env={operating_system:'Windows 11',product:'AuroraVPN',product_version:'5.2'};
const sample={id:'SOL-fixture',title:'VPN E42',problem:'Kuvitteellinen VPN E42 -ongelma.',environment:'Harjoitusympäristö.',solution:'Kuvitteellinen korjaus.',...env,status:'draft',revision:1,updated_at:'2026-10-24T10:00:00Z'};
const compatibleLabel='Ilmoitettujen ympäristötietojen perusteella yhteensopivat ehdokkaat';
const reviewLabel='Puuttuvien tietojen vuoksi tarkistettavat ehdokkaat';
const clone=value=>JSON.parse(JSON.stringify(value));
function all(node){return [node,...node.children.flatMap(all)];}
function createHarness(initial=[]){
 const elements={},nodes=[],calls=[],confirmations=[],prompts=[],confirmText=[],promptDefaults=[],faults=new Map(),overrides=new Map();let serial=0,held=null,heldAction='search',searchResult=null;
 const document={activeElement:null,getElementById:id=>elements[id],createElement:tag=>element(tag),querySelectorAll:()=>nodes.filter(e=>e.isConnected&&['button','input','textarea','select'].includes(e.tag))};
 function connected(e,value){e.isConnected=value;for(const child of e.children)connected(child,value);}
 function element(tag){const e={tag,children:[],parent:null,attributes:{},style:{},_text:'',value:'',checked:false,disabled:false,hidden:false,open:false,tabIndex:-1,isConnected:false,handlers:{},selectionStart:0,selectionEnd:0,scrollTop:0,
  append(...items){for(const child of items){if(child.parent)child.parent.children=child.parent.children.filter(item=>item!==child);child.parent=this;this.children.push(child);connected(child,this.isConnected);}},
  replaceChildren(...items){for(const child of this.children){child.parent=null;connected(child,false);}this.children=[];this._text='';this.append(...items);},
  addEventListener(name,handler){const previous=this.handlers[name];this.handlers[name]=event=>{previous?.(event);return handler(event);};},setAttribute(name,value){this.attributes[name]=String(value);},getAttribute(name){return this.attributes[name]??null;},
  focus(){if(!this.isConnected||this.disabled||!visible(this))return;document.activeElement=this;},
  reset(){for(const key of fields)elements[key].value='';elements.consent.checked=false;},
  getClientRects(){return visible(this)?[{}]:[];},getBoundingClientRect(){return {height:parseFloat(this.style.height)||310};},
  setSelectionRange(start,end){this.selectionStart=start;this.selectionEnd=end;},showModal(){this.open=true;},close(){this.open=false;this.handlers.close?.();}
 };Object.defineProperty(e,'scrollHeight',{get(){return Math.max(288,e.value.split('\n').length*24)+20;}});Object.defineProperty(e,'textContent',{get(){return this._text;},set(value){this.replaceChildren();this._text=String(value);}});nodes.push(e);return e;}
 const root=element('root');root.isConnected=true;const stack=[root];
 const markup=html.replace(/<style>[\s\S]*?<\/style>/,'').replace(/<script>[\s\S]*?<\/script>/,'');
 const voids=new Set(['meta','input','br','hr','option','link']);
 for(const token of markup.match(/<[^>]+>|[^<]+/g)||[]){
  if(token.startsWith('</')){const tag=token.match(/^<\/([\w-]+)/)?.[1];let at=stack.length-1;while(at>0&&stack[at].tag!==tag)at--;if(at>0)stack.length=at;continue;}
  if(token.startsWith('<')){const match=token.match(/^<([a-z][\w-]*)([\s\S]*?)>$/i);if(!match)continue;const e=element(match[1]);
   for(const [,key,value] of match[2].matchAll(/([:\w-]+)(?:="([^"]*)")?/g))e.attributes[key]=value??'';
   e.id=e.attributes.id||'';if(e.id){assert(!elements[e.id],'duplicate HTML id '+e.id);elements[e.id]=e;}
   e.hidden='hidden' in e.attributes;e.checked='checked' in e.attributes;e.tabIndex=Number(e.attributes.tabindex??-1);e.type=e.attributes.type||'';e.className=e.attributes.class||'';
   if(e.tag==='select')e.value='keyword';stack.at(-1).append(e);if(!voids.has(e.tag))stack.push(e);continue;
  }if(token.trim())stack.at(-1)._text+=token.trim();
 }
 let rows=clone(initial);const response=(value,ok=true)=>({ok,json:async()=>clone(value)});
 const context={document,navigator:{},getComputedStyle:()=>({borderTopWidth:'1',borderBottomWidth:'1',paddingTop:'10',paddingBottom:'10',lineHeight:'24',minHeight:'310'}),window:{addEventListener(){},confirm:text=>{confirmText.push(text);return confirmations.length?confirmations.shift():true;},prompt:(message,initial='')=>{promptDefaults.push(initial);return prompts.length?prompts.shift():(initial||'Kuvitteellinen poistamisen syy');}},fetch:async(url,options)=>{
  assert(url.startsWith('/api/memory/'),'Only mocked local memory actions allowed');const action=url.split('/').pop(),body=JSON.parse(options.body);calls.push({action,body});
  const pending=faults.get(action);if(pending?.length){const fault=pending.shift();if(fault instanceof Error)throw fault;return response(fault,false);}
  const override=overrides.get(action);if(override?.length)return response(override.shift());
  if(held&&action===heldAction)return new Promise(resolve=>held.resolve=resolve);
  if(action==='api-status'||action==='api-settings')return response({configured:body.clear!==true,source:body.clear?'none':'local',model:body.model||'gpt-4.1-mini',persistence:'process_memory',last_result:'not_tested'});
  if(action==='list')return response({records:rows});
  if(action==='save'){const old=rows.find(row=>row.id===body.id);const row={...sample,...body,id:old?old.id:'SOL-new-'+(++serial),revision:old?old.revision+1:1,status:'draft',verified_at:null,verified_by:null};rows=rows.filter(r=>r.id!==row.id);rows.push(row);return response({record:row});}
  if(action==='verify'||action==='retire'){const row=rows.find(r=>r.id===body.id);assert(row);Object.assign(row,action==='verify'?{status:'verified',verified_by:body.verified_by,verified_at:sample.updated_at}:{status:'retired',retirement_reason:body.reason},{revision:row.revision+1});return response({record:row});}
  if(action==='delete'){const row=rows.find(r=>r.id===body.id);assert(row&&row.revision===body.revision&&row.title===body.confirmation_title);rows=rows.filter(r=>r.id!==body.id);return response({deleted_id:body.id});}
  if(action==='search'){if(searchResult)return response(searchResult);return response({state:'empty',hits:[],compatible_hits:[],review_hits:[]});}
  if(action==='suggest'&&body.web_stage==='search')return response({state:'web_sources_ready',source_request_id:'f'.repeat(32),web_diagnostics:{source_search:{accepted_source_count:1}}});
  if(action==='suggest')return response({state:'unverified',suggestion:{title:'API-luonnos',solution:'Kuvitteellinen kokeilematon ehdotus.',limitations:'Ei kokeiltu oikeassa ympäristössä.'}});
  throw Error(action);
 }};
 vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
 function visible(e){for(let p=e;p;p=p.parent)if(p.hidden||(p.tag==='dialog'&&!p.open))return false;return true;}
 async function click(id){const e=typeof id==='string'?elements[id]:id;assert(e&&visible(e)&&!e.disabled,'control unavailable '+(e?.id||e?.textContent||id));e.focus();return e.onclick?.();}
 async function submit(id){assert(visible(elements[id]));return elements[id].onsubmit({preventDefault(){}});}
 function input(id,value){elements[id].value=value;elements[id].handlers.input?.({target:elements[id]});}
 function snapshot(){return fields.map(key=>elements[key].value);}
 const harness={elements,document,navigator:context.navigator,window:context.window,calls,confirmations,prompts,confirmText,promptDefaults,get rows(){return rows;},click,submit,input,snapshot,visible,
  fill(data=sample){for(const key of fields)elements[key].value=data[key]??'';},
  fail(action,error={error:'Kuvitteellinen palvelinvirhe',help:'Yritä uudelleen.'}){if(!faults.has(action))faults.set(action,[]);faults.get(action).push(error);},
  respond(action,value){if(!overrides.has(action))overrides.set(action,[]);overrides.get(action).push(value);},
  setSearch(value){searchResult=value;},count(action){return calls.filter(call=>call.action===action).length;},
  action(label){const e=all(elements.records).find(e=>e.tag==='button'&&e.textContent===label);if(e&&!visible(e)){let p=e.parent;while(p&&p.className!=='library-body')p=p.parent;if(p?.hidden){const toggle=p.parent.children[0].children.find(x=>x.className==='library-toggle');toggle.onclick();}}return e;},
  group(label){return elements.hits.children.find(e=>e.children.some(child=>child.tag==='h3'&&child.textContent===label));},
  async key(id,key){let prevented=false;const e=elements[id];e.focus();await e.onkeydown?.({key,preventDefault(){prevented=true;}});return prevented;},
  hold(action='search'){held={};heldAction=action;return held;},release(value){const item=held;held=null;item.resolve(response(value));}
 };return harness;
}
function hit(record,status='declared_match'){return {record,score:.8,environment_check:{status,missing_record_fields:status==='needs_review'?['product_version']:[],missing_query_fields:[]}};}
function result(hits){return {state:'candidates',hits,compatible_hits:hits.filter(h=>h.environment_check.status==='declared_match'),review_hits:hits.filter(h=>h.environment_check.status==='needs_review')};}
test('Oirehaku näyttää palvelimen tarkennuspyynnön ja tavallinen tyhjä tulos pysyy erillisenä',async()=>{
 const h=createHarness();h.setSearch({state:'clarification',message:'Mikä laite, ohjelma tai toiminto ei toimi?',hits:[],compatible_hits:[],review_hits:[]});await search(h);
 assert(all(h.elements.hits).some(e=>e.textContent==='Mikä laite, ohjelma tai toiminto ei toimi?'));
 h.setSearch({state:'insufficient',hits:[],compatible_hits:[],review_hits:[]});await search(h);
 assert(all(h.elements.hits).some(e=>e.textContent.includes('Hakuehdokkaita ei löytynyt.')));
 assert(!all(h.elements.hits).some(e=>e.textContent==='Mikä laite, ohjelma tai toiminto ei toimi?'));
});
test('Yhteishaku näyttää sanahaun varatulokset ja kertoo mallivirheestä vain virhetilassa',async()=>{
 const h=createHarness(),row={...sample,status:'verified'};
 assert.equal(h.elements.backend.value,'keyword');assert(html.includes('value="joint">Yhteishaku (kokeilu)'));
 h.elements.backend.value='joint';h.input('query','VPN ei toimi');
 h.setSearch({...result([hit(row)]),semantic_status:'error',keyword_fallback:true});await h.submit('search-form');
 assert.equal(h.calls.find(c=>c.action==='search').body.backend,'joint');
 assert(h.elements.notice.textContent.includes('Merkityshaku ei ole käytettävissä. Näytetään sanahaun tulokset.'));
 assert(all(h.elements.hits).some(e=>e.textContent===row.title));
 h.setSearch({state:'insufficient',hits:[],semantic_status:'ok',keyword_fallback:false});await h.submit('search-form');
 assert(!h.elements.notice.textContent.includes('Merkityshaku ei ole käytettävissä.'));
 assert(all(h.elements.hits).some(e=>e.textContent.includes('Hakuehdokkaita ei löytynyt.')));
});
async function beginEditor(h){await h.click('tab-editor');h.fill();}
async function beginSearchSuggestion(h){await search(h);await h.click('start-suggestion');h.elements['search-consent'].checked=true;return h.click('search-suggest');}
async function search(h){h.input('query','Kuvitteellinen VPN E42 -ongelma.');for(const key in env)h.elements['filter-'+key].value=env[key];return h.submit('search-form');}

 test('Hakunäkymän esikatselu ja lupa edeltävät lähetystä, kaikki ilmoitetut tiedot välitetään',async()=>{
 const h=createHarness();h.fill();const before=h.snapshot();h.input('search-environment','Kuvitteellinen toimistolaite.');await search(h);assert.equal(h.count('suggest'),0);await h.click('start-suggestion');assert(!h.elements['panel-search'].hidden);assert.equal(h.count('suggest'),0);const preview=h.elements['search-send-preview'].textContent;for(const value of [h.elements.query.value,...Object.values(env),'Kuvitteellinen toimistolaite.'])assert(preview.includes(value));await h.click('search-suggest');assert.equal(h.count('suggest'),0);assert.equal(h.document.activeElement.id,'search-consent');h.elements['search-consent'].checked=true;await h.click('search-suggest');assert.deepEqual(h.calls.find(c=>c.action==='suggest').body,{problem:h.elements.query.value,environment:'Kuvitteellinen toimistolaite.',...env,send_to_api:true});assert.deepEqual(h.snapshot(),before);assert(!h.elements['panel-search'].hidden);assert.equal(h.elements['suggestion-preview'].parent.id,'search-proposal-home');assert(!h.elements['suggestion-preview'].hidden);assert.equal(h.count('save'),0);assert(!h.elements['search-consent'].checked);
 });
 test('Hakunäkymän ehdotus ei vaadi valinnaisia ympäristötietoja ja siirtyy uudeksi luonnokseksi',async()=>{
 const h=createHarness();h.input('query','Kuvitteellinen VPN-ongelma.');await h.submit('search-form');await h.click('start-suggestion');assert(h.elements['search-send-preview'].textContent.includes('Ei ilmoitettu'));h.elements['search-consent'].checked=true;await h.click('search-suggest');assert.deepEqual(h.calls.find(c=>c.action==='suggest').body,{problem:h.elements.query.value,environment:'',send_to_api:true});await h.click('edit-suggestion');assert(!h.elements['panel-editor'].hidden);assert.equal(h.elements.environment.value,'Vapaata ympäristökuvausta ei ilmoitettu.');assert.equal(h.count('save'),0);await h.submit('editor');assert.equal(h.count('save'),1);assert.equal(h.rows[0].status,'draft');
 });
 test('Haun ehdotuksen siirron peruminen säilyttää keskeneräisen lomakkeen ja hyväksyminen tekee uuden luonnoksen',async()=>{
 const h=createHarness([{...sample,status:'verified'}]);await h.click('tab-library');await h.click(h.action('Muokkaa'));h.input('solution','Keskeneräinen oma ratkaisu.');const before=h.snapshot();await h.click('tab-search');h.input('search-environment','Haun vapaa ympäristö.');await beginSearchSuggestion(h);h.confirmations.push(false);await h.click('edit-suggestion');assert.deepEqual(h.snapshot(),before);assert(!h.elements['panel-search'].hidden);assert(!h.elements['suggestion-preview'].hidden);assert.equal(h.count('save'),0);await h.click('edit-suggestion');assert.equal(h.elements.problem.value,h.elements.query.value);assert.equal(h.elements.environment.value,'Haun vapaa ympäristö.');for(const key in env)assert.equal(h.elements[key].value,env[key]);await h.submit('editor');const saved=h.calls.find(c=>c.action==='save').body;assert(!('id' in saved));assert.equal(h.rows.find(r=>r.id===sample.id).status,'verified');assert.equal(h.rows.length,2);
 });
 test('Haun kaikkien lähetettävien kenttien muutos poistaa luvan ja estää vanhan ehdotuksen siirron',async()=>{
 for(const id of ['query','search-environment',...Object.keys(env).map(key=>'filter-'+key)]){const h=createHarness();await beginSearchSuggestion(h);h.elements['search-consent'].checked=true;h.input(id,h.elements[id].value+' Muutos');assert(!h.elements['search-consent'].checked,id);const before=h.snapshot();await h.click('edit-suggestion');assert.deepEqual(h.snapshot(),before);assert(h.elements.notice.textContent.includes('muuttunut'));assert.equal(h.count('save'),0);}
 });
 test('Haun ja kirjoituslomakkeen omat ehdotukset säilyvät välilehden vaihtuessa',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;h.respond('suggest',{suggestion:{title:'Lomakkeen ehdotus',solution:'Lomake',limitations:'Rajat'}});await h.click('suggest');await h.click('tab-search');await beginSearchSuggestion(h);assert.equal(h.elements['suggestion-heading'].textContent,'API-luonnos');await h.click('tab-editor');assert.equal(h.elements['suggestion-heading'].textContent,'Lomakkeen ehdotus');await h.click('tab-search');assert.equal(h.elements['suggestion-heading'].textContent,'API-luonnos');
 });
 test('Haun odotustila estää kaksoislähetyksen ja tarkat virheet säilyttävät molemmat lomakkeet',async()=>{
 const h=createHarness();h.fill();const before=h.snapshot();await search(h);await h.click('start-suggestion');h.elements['search-consent'].checked=true;h.hold('suggest');const pending=h.click('search-suggest');assert(h.elements['search-suggest'].disabled);assert(h.elements['search-suggest'].textContent.includes('Odotetaan'));assert.equal(h.elements['search-api-options'].getAttribute('aria-busy'),'true');await h.elements['search-suggest'].onclick();assert.equal(h.count('suggest'),1);h.release({state:'unverified',suggestion:{title:'Haun ehdotus',solution:'Ohje',limitations:'Rajat'}});await pending;
 for(const code of ['missing_api_key','invalid_api_key','api_authentication','api_forbidden','api_billing','api_model_access','api_rate_limit','api_timeout','api_connection','api_format']){h.elements['search-consent'].checked=true;h.fail('suggest',{error:'Virhe',help:'Täsmäohje '+code,code});await h.click('search-suggest');assert(h.elements.notice.textContent.includes('Täsmäohje '+code));assert(h.elements.notice.textContent.includes('Virhekoodi: '+code));assert.deepEqual(h.snapshot(),before);assert(!h.elements['search-suggest'].disabled);assert.equal(h.elements['search-api-options'].getAttribute('aria-busy'),'false');assert.equal(h.elements.query.value,'Kuvitteellinen VPN E42 -ongelma.');}assert.equal(h.count('save'),0);
 });
 test('Haun turvapysäytys ja virheellinen API-vastaus eivät korvaa tekstejä tai tallenna',async()=>{
 const h=createHarness();h.fill();const before=h.snapshot();await search(h);await h.click('start-suggestion');for(const response of [{state:'safety_stop',message:'Pysähdy turvallisuussyystä.'},{suggestion:{title:'Vajaa'}}]){h.elements['search-consent'].checked=true;h.respond('suggest',response);await h.click('search-suggest');assert.deepEqual(h.snapshot(),before);assert(h.elements['suggestion-preview'].hidden);assert.equal(h.count('save'),0);assert.equal(h.document.activeElement.id,'notice');}
 });
 test('Haku on oletus, muut paneelit piilossa, sivu ei lataa hallintaa automaattisesti',()=>{
 const h=createHarness();assert.equal(h.elements['tab-search'].getAttribute('aria-selected'),'true');assert(!h.elements['panel-search'].hidden);assert(!h.elements['initial-results'].hidden);assert(h.elements['results-section'].hidden);assert(h.elements['panel-editor'].hidden);assert(h.elements['panel-library'].hidden);assert(h.elements['next-steps'].hidden);assert.equal(h.calls.length,0);
 });
 test('Tietoa toimii kaikilta välilehdiltä ja säilyttää lomakkeen ja kohdistuksen',async()=>{
 const h=createHarness();await beginEditor(h);h.input('solution','Keskeneräinen ratkaisu');const before=h.snapshot();
 for(const tab of ['tab-search','tab-editor','tab-library']){await h.click(tab);await h.click('open-about');assert(h.elements['about-dialog'].open);assert.equal(h.document.activeElement.id,'about-heading');let prevented=false;h.elements['about-dialog'].handlers.keydown({key:'Tab',shiftKey:true,preventDefault(){prevented=true;}});assert(prevented);assert.equal(h.document.activeElement.id,'close-about');prevented=false;h.elements['about-dialog'].handlers.keydown({key:'Tab',shiftKey:false,preventDefault(){prevented=true;}});assert(prevented);assert.equal(h.document.activeElement.id,'about-github');await h.click('close-about');assert.equal(h.document.activeElement.id,'open-about');assert.deepEqual(h.snapshot(),before);}
 await h.click('open-about');let prevented=false;h.elements['about-dialog'].handlers.cancel({preventDefault(){prevented=true;}});assert(prevented);assert(!h.elements['about-dialog'].open);assert.equal(h.document.activeElement.id,'open-about');assert.deepEqual(h.snapshot(),before);
 assert.equal(h.elements['about-guide'].getAttribute('href'),'/pikaohje');assert.equal(h.elements['about-github'].getAttribute('href'),'https://github.com/kauppinen1977-spec/ai-service-desk-assistant');assert.equal(h.elements['about-github'].getAttribute('rel'),'noopener noreferrer');
 });
 test('Tyhjät työkalukortit ohitetaan, eikä uudessa lomakkeessa ole komentokorttia',async()=>{
 const h=createHarness();await beginEditor(h);assert.equal(h.elements['command-editor-list'].children.length,0);await h.click('add-command');await h.click('add-link');const before=h.snapshot();await h.submit('editor');const body=h.calls.find(call=>call.action==='save').body;assert.equal(body.tools.commands.length,0);assert.equal(body.tools.links.length,0);assert.deepEqual(h.snapshot(),before);
 });
 test('Osittain täytetty kortti näyttää kenttävirheet ja säilyttää lomakkeen',async()=>{
 const h=createHarness();await beginEditor(h);await h.click('add-command');const box=h.elements['command-editor-list'].children[0],fields=all(box).filter(e=>e.tag==='textarea');fields[0].value='ver';fields[0].handlers.input();const before=h.snapshot();await h.submit('editor');assert.equal(h.count('save'),0);assert.deepEqual(h.snapshot(),before);const name=all(box).find(e=>e.tag==='input');assert.equal(name.getAttribute('aria-invalid'),'true');assert(all(box).some(e=>e.className==='field-error'&&!e.hidden&&e.textContent.includes('Nimi on pakollinen')));assert.equal(h.document.activeElement,name);
 });
 test('Osittainen linkki näyttää puuttuvan osoitteen ja säilyttää lomakkeen',async()=>{
 const h=createHarness();await beginEditor(h);await h.click('add-link');const box=h.elements['link-editor-list'].children[0],inputs=all(box).filter(e=>e.tag==='input');inputs[0].value='Ohje';inputs[0].handlers.input();const before=h.snapshot();await h.submit('editor');assert.equal(h.count('save'),0);assert.deepEqual(h.snapshot(),before);assert.equal(inputs[1].getAttribute('aria-invalid'),'true');assert(all(box).some(e=>e.className==='field-error'&&!e.hidden&&e.textContent.includes('Osoite on pakollinen')));
 });
 test('Välilehdet: nuolinäppäimet, Home ja End siirtävät fokusta; Enter ja välilyönti avaavat näkymän',async()=>{
 const h=createHarness();assert(await h.key('tab-search','ArrowRight'));assert.equal(h.document.activeElement.id,'tab-editor');assert(!h.elements['panel-search'].hidden);assert.equal(h.calls.length,0);
 await h.key('tab-editor','Enter');assert(!h.elements['panel-editor'].hidden);assert.equal(h.elements['tab-editor'].tabIndex,0);
 await h.key('tab-editor','End');assert.equal(h.document.activeElement.id,'tab-library');assert(h.elements['panel-library'].hidden);
 await h.key('tab-library',' ');assert(!h.elements['panel-library'].hidden);assert.equal(h.count('list'),1);
 await h.key('tab-library','Home');assert.equal(h.document.activeElement.id,'tab-search');await h.key('tab-search','ArrowLeft');assert.equal(h.document.activeElement.id,'tab-library');assert.equal(await h.key('tab-library','Tab'),false);
 });
 test('Haku näyttää erilliset ehdokasryhmät, varoitukset ja haun jälkeiset siirtymät',async()=>{
 const h=createHarness(),known={...sample,status:'verified'},review={...sample,id:'SOL-review',title:'Puutteellinen tapaus',status:'verified'};h.setSearch(result([hit(known),hit(review,'needs_review')]));await search(h);
 assert(!h.elements['results-section'].hidden);assert(h.elements['initial-results'].hidden);assert(!h.elements['next-steps'].hidden);assert.equal(h.document.activeElement.id,'results-heading');assert(all(h.group(compatibleLabel)).some(e=>e.textContent===known.title));assert(!all(h.group(compatibleLabel)).some(e=>e.textContent===review.title));assert(all(h.group(reviewLabel)).some(e=>e.textContent===review.title));assert(all(h.elements.hits).some(e=>e.textContent==='Ratkaisusta puuttuu: tuotteen versio'));assert(all(h.elements.hits).some(e=>e.className==='hit-tag'&&e.textContent===known.product));
 assert(html.includes('ei takaa ratkaisun toimivuutta'));assert(all(h.elements.hits).some(e=>e.textContent.includes('Vahvistettu aiemmassa tapauksessa')));
 await h.click('copy-query');assert(!h.elements['panel-editor'].hidden);assert.equal(h.elements.problem.value,h.elements.query.value);for(const key in env)assert.equal(h.elements[key].value,env[key]);assert.equal(h.document.activeElement.id,'environment');assert.equal(h.count('suggest'),0);assert.equal(h.count('save'),0);
 });
 test('Tyhjä ja pelkästään tarkistettavia sisältävä haku kertoo yhteensopivien puuttumisesta',async()=>{
 const h=createHarness();await search(h);assert(all(h.elements.hits).some(e=>e.textContent.includes('yhteensopivia ehdokkaita ei löytynyt')));assert(!h.elements['next-steps'].hidden);
 h.setSearch(result([hit({...sample,status:'verified'},'needs_review')]));await search(h);assert(all(h.group(compatibleLabel)).some(e=>e.textContent.includes('yhteensopivia ehdokkaita ei löytynyt')));assert(all(h.group(reviewLabel)).some(e=>e.tag==='article'));
 });
 test('API-siirtymä ei lähetä mitään ja tallentamatonta tekstiä ei korvata ilman hyväksyntää',async()=>{
 const h=createHarness();await search(h);await h.click('start-suggestion');assert(!h.elements['panel-search'].hidden);assert(!h.elements['search-api-options'].hidden);assert.equal(h.document.activeElement.id,'search-api-heading');assert.equal(h.count('suggest'),0);h.fill();const before=h.snapshot();h.confirmations.push(false);await h.click('copy-query');assert.deepEqual(h.snapshot(),before);assert(!h.elements['panel-search'].hidden);
 await h.click('tab-editor');await h.click('tab-library');await h.click('tab-editor');assert.deepEqual(h.snapshot(),before);
 });
 test('API-ehdotus vaatii erillisen luvan ja avautuu ensin luettavaksi muuttamatta lomaketta',async()=>{
 const h=createHarness();await h.click('tab-editor');h.elements['api-options'].open=true;await h.click('suggest');assert.equal(h.count('suggest'),0);assert.equal(h.document.activeElement.id,'problem');h.fill();await h.click('suggest');assert.equal(h.count('suggest'),0);assert.equal(h.document.activeElement.id,'consent');
 const before=h.snapshot();h.elements.consent.checked=true;await h.click('suggest');assert.equal(h.count('suggest'),1);assert.equal(h.count('save'),0);assert.deepEqual(h.snapshot(),before);assert(!h.elements['suggestion-preview'].hidden);assert.equal(h.elements['suggestion-heading'].textContent,'API-luonnos');assert(h.elements['proposal-solution'].textContent.includes('Kuvitteellinen'));assert(h.elements.limitations.textContent.includes('Ei kokeiltu'));assert(!h.elements.consent.checked);assert.equal(h.document.activeElement.id,'suggestion-heading');assert.equal(h.confirmText.length,0);
 const request=h.calls.find(call=>call.action==='suggest').body;assert.deepEqual(Object.keys(request).sort(),['environment','problem','send_to_api']);h.elements.consent.checked=true;h.input('environment','Uusi kuvitteellinen ympäristö');assert(!h.elements.consent.checked);
 });
 test('API-virhe ja virheellinen vastaus säilyttävät lomaketekstin',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const before=h.snapshot();
 h.fail('suggest',new Error('Kuvitteellinen yhteysvirhe'));await h.click('suggest');assert.deepEqual(h.snapshot(),before);assert.equal(h.document.activeElement.id,'notice');assert.equal(h.elements.notice.getAttribute('role'),'alert');assert(!h.elements.suggest.disabled);
 h.respond('suggest',{state:'unverified',suggestion:{title:'Ei saa korvata'}});await h.click('suggest');assert.deepEqual(h.snapshot(),before);assert(h.elements.notice.textContent.includes('ei voitu lukea'));
 });
 test('Ehdotuksen siirto kysyy ennen korvaamista ja tallennus tehdään erikseen',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const before=h.snapshot();await h.click('suggest');
 h.confirmations.push(false);await h.click('edit-suggestion');assert.deepEqual(h.snapshot(),before);assert.equal(h.count('save'),0);assert(!h.elements['suggestion-preview'].hidden);
 await h.click('edit-suggestion');assert.equal(h.elements.title.value,'API-luonnos');assert(h.elements.solution.value.includes('Soveltuvuuden rajat ja puuttuvat tiedot:\nEi kokeiltu'));assert.equal(h.document.activeElement.id,'solution');assert.equal(h.count('save'),0);assert.equal(h.elements.problem.value,sample.problem);assert.equal(h.elements.environment.value,sample.environment);
 const combined=h.elements.solution.value;await h.submit('editor');assert.equal(h.count('save'),1);assert.equal(h.rows[0].solution,combined);assert.equal(h.rows[0].status,'draft');
 });
 test('Muuttuneen ongelman ehdotusta ei siirretä vahingossa uuteen kuvaukseen',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;await h.click('suggest');h.input('problem','Toinen kuvitteellinen ongelma.');const before=h.snapshot();await h.click('edit-suggestion');assert.deepEqual(h.snapshot(),before);assert.equal(h.count('save'),0);assert(h.elements.notice.textContent.includes('muuttunut'));assert(!h.elements['suggestion-preview'].hidden);
 });
 test('Ehdotuksen HTML ja komentosarjat näytetään vain tekstinä',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const proposal={title:'<img src=x onerror=alert(1)>',solution:'<script>bad()</script>\n1. Säilytä rivit.',limitations:'<a href="javascript:bad()">Älä suorita</a>'};h.respond('suggest',{state:'unverified',suggestion:proposal});await h.click('suggest');
 assert.equal(h.elements['suggestion-heading'].textContent,proposal.title);assert.equal(h.elements['proposal-solution'].textContent,proposal.solution);assert.equal(h.elements.limitations.textContent,proposal.limitations);assert.equal(h.elements['proposal-solution'].children.length,0);assert(!all(h.elements['suggestion-preview']).some(e=>['script','img','a'].includes(e.tag)));assert.equal(h.count('save'),0);
 });
 test('Suuri muokkain käyttää samaa kenttää ja palauttaa tekstin sekä fokuksen painikkeella ja Escillä',async()=>{
 const h=createHarness();await beginEditor(h);const field=h.elements.solution;field.selectionStart=3;field.selectionEnd=8;field.scrollTop=42;await h.click('expand-solution');assert(h.elements['solution-dialog'].open);assert.equal(h.elements['solution-control'].parent,h.elements['solution-dialog-content']);assert.equal(h.document.activeElement,field);assert.equal(field.selectionStart,3);assert.equal(field.scrollTop,42);
 h.input('solution','Ensimmäinen rivi.\nToinen rivi.\n<vanha teksti>');await h.click('close-solution');assert(!h.elements['solution-dialog'].open);assert.equal(h.elements['solution-control'].parent,h.elements['solution-home']);assert.equal(h.elements.solution,field);assert.equal(h.elements.solution.value,'Ensimmäinen rivi.\nToinen rivi.\n<vanha teksti>');assert.equal(h.document.activeElement.id,'expand-solution');
 await h.click('expand-solution');let tabPrevented=false;h.elements['solution-dialog'].handlers.keydown({key:'Tab',shiftKey:true,preventDefault(){tabPrevented=true;}});assert(tabPrevented);assert.equal(h.document.activeElement.id,'close-solution');h.elements['solution-dialog'].handlers.keydown({key:'Tab',shiftKey:false,preventDefault(){}});assert.equal(h.document.activeElement.id,'solution');await h.click('close-solution');
 await h.click('expand-solution');h.elements['solution-dialog'].handlers.close();assert.equal(h.elements['solution-control'].parent,h.elements['solution-dialog-content']);await h.click('close-solution');
 await h.click('expand-solution');h.input('solution',field.value+'\nEscillä säilyvä lisäys.');let prevented=false;h.elements['solution-dialog'].handlers.cancel({preventDefault(){prevented=true;}});assert(prevented);assert(!h.elements['solution-dialog'].open);assert(h.elements.solution.value.endsWith('Escillä säilyvä lisäys.'));assert.equal(h.document.activeElement.id,'expand-solution');assert.equal(h.count('save'),0);assert.equal(field.getAttribute('form'),'editor');
 });
 test('Ratkaisukenttä kasvaa noin 20 riviin, vierii ja säilyttää käsin suurennetun koon',async()=>{
 const h=createHarness();await beginEditor(h);h.input('solution','Lyhyt.');assert.equal(h.elements.solution.style.height,'310px');h.input('solution','Rivi\n'.repeat(30));assert.equal(h.elements.solution.style.height,'502px');h.input('solution','Lyhyt taas.');assert.equal(h.elements.solution.style.height,'310px');h.elements.solution.style.height='720px';await h.click('expand-solution');await h.click('close-solution');assert.equal(h.elements.solution.style.height,'720px');h.input('solution','Käsin suurennettu.');assert.equal(h.elements.solution.style.height,'720px');assert(html.includes('overflow-y:auto'));assert(html.includes('resize:vertical'));
 });
 test('Vanha pitkä ratkaisu säilyy kokonaan avaamisessa, suuressa muokkaimessa ja tallennuksessa',async()=>{
 const text='Vanha alkuperäinen rivi.\n'.repeat(220)+'Lopputunniste';const h=createHarness([{...sample,solution:text,status:'verified'}]);await h.click('tab-library');await h.click(h.action('Muokkaa'));assert.equal(h.elements.solution.value,text);await h.click('expand-solution');await h.click('close-solution');assert.equal(h.elements.solution.value,text);await h.submit('editor');assert.equal(h.calls.find(c=>c.action==='save').body.solution,text);assert.equal(h.rows[0].status,'draft');
 });
 test('Ylipitkää yhdistettyä ehdotusta ei katkaista ja tallennus ohjaa lyhentämään sitä itse',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const proposal={title:'Pitkä ehdotus',solution:'s'.repeat(7900),limitations:'r'.repeat(500)};h.respond('suggest',{state:'unverified',suggestion:proposal});await h.click('suggest');await h.click('edit-suggestion');const combined=proposal.solution+'\n\nSoveltuvuuden rajat ja puuttuvat tiedot:\n'+proposal.limitations;assert.equal(h.elements.solution.value,combined);assert(h.elements['solution-length'].textContent.includes('mitään ei katkaistu'));await h.submit('editor');assert.equal(h.count('save'),0);assert.equal(h.elements.solution.value,combined);assert(h.elements.notice.textContent.includes('8000'));
 });
 test('Tallennusvirhe säilyttää kaikki kentät ja epäonnistuneen muokkauksen tietue-ID:n',async()=>{
 const h=createHarness([{...sample,status:'verified'}]);await h.click('tab-library');await h.click(h.action('Muokkaa'));h.input('solution','Tallentamaton tarkennus');const before=h.snapshot();h.fail('save',{error:'Versioristiriita',help:'Päivitä lista.'});await h.submit('editor');assert.deepEqual(h.snapshot(),before);assert.equal(h.document.activeElement.id,'notice');assert(!h.elements['save-draft'].disabled);assert(h.elements['saved-next'].hidden);
 await h.submit('editor');const saves=h.calls.filter(call=>call.action==='save');assert.equal(saves.length,2);assert.equal(saves[0].body.id,sample.id);assert.equal(saves[1].body.id,sample.id);assert.equal(saves[1].body.revision,sample.revision);
 });
 test('Hallinnan muokkauksen peruminen säilyttää tallennetun tietueen ja hylkäyksen peruminen lomakkeen',async()=>{
 const h=createHarness([{...sample,status:'verified'}]);await h.click('tab-library');await h.click(h.action('Muokkaa'));h.input('solution','Keskeneräinen teksti');h.confirmations.push(false);await h.click('cancel-library-edit');assert.equal(h.elements.solution.value,'Keskeneräinen teksti');assert(!h.elements['panel-editor'].hidden);h.confirmations.push(true);await h.click('cancel-library-edit');assert(!h.elements['panel-library'].hidden);assert.equal(h.rows[0].solution,sample.solution);assert.equal(h.rows[0].status,'verified');assert.equal(h.count('save'),0);
 });
 test('Pysyvä poisto vaatii täsmällisen otsikon, ja peruminen säilyttää tietueen',async()=>{
 for(const status of ['verified','retired']){const h=createHarness([{...sample,status}]);await h.click('tab-library');const remove=h.action('Poista pysyvästi');await h.click(remove);assert(h.elements['delete-dialog'].open);assert(h.elements['delete-target'].textContent.includes(sample.title));assert(h.elements['delete-target'].textContent.includes(sample.id));assert(h.elements['confirm-delete'].disabled);assert.equal(h.document.activeElement.id,'delete-title');await h.click('cancel-delete');assert(!h.elements['delete-dialog'].open);assert.equal(h.document.activeElement,remove);assert.equal(h.count('delete'),0);assert.equal(h.rows.length,1);await h.click(remove);h.input('delete-title',sample.title+' ');assert(h.elements['confirm-delete'].disabled);assert.equal(h.count('delete'),0);h.input('delete-title',sample.title);assert(!h.elements['confirm-delete'].disabled);await h.click('confirm-delete');assert.equal(h.count('delete'),1);assert.equal(h.calls.find(c=>c.action==='delete').body.revision,sample.revision);assert.equal(h.rows.length,0);assert(!h.elements['delete-dialog'].open);assert.equal(h.document.activeElement.id,'library-heading');}
 });
 test('Onnistunut tallennus on luonnos ja suora siirtymä avaa juuri sen tarkistukseen',async()=>{
 const h=createHarness();await beginEditor(h);const before=h.snapshot();await h.submit('editor');assert.equal(h.rows[0].status,'draft');assert.deepEqual(h.snapshot(),before);assert(!h.elements['saved-next'].hidden);assert(h.elements['saved-message'].textContent.includes('ei vielä näy haussa'));assert.equal(h.document.activeElement.id,'saved-heading');assert.equal(h.count('list'),0);
 await h.click('review-saved');assert(!h.elements['panel-library'].hidden);assert.equal(h.count('list'),1);const card=all(h.elements.records).find(e=>e.id==='record-'+h.rows[0].id);assert.equal(h.document.activeElement,card);assert(card.getAttribute('aria-label').includes(h.rows[0].title));assert(all(card).filter(e=>e.tag==='button').every(e=>e.getAttribute('aria-label').includes(h.rows[0].title)));assert(all(card).find(e=>e.tag==='details').open);assert(h.action('Vahvista aiempi tapaus'));
 });
 test('Listan latausvirhe tallennuksen jälkeen ei hävitä tekstiä tai esitä tallennusta epäonnistuneena',async()=>{
 const h=createHarness();await beginEditor(h);await h.submit('editor');const before=h.snapshot();h.fail('list');await h.click('review-saved');assert.equal(h.rows.length,1);assert.equal(h.rows[0].status,'draft');assert.deepEqual(h.snapshot(),before);await h.click('refresh');assert(h.action('Vahvista aiempi tapaus'));assert.equal(h.elements.notice.getAttribute('role'),'status');
 });
 test('Vahvistus vaatii nimen ja aiemman tapauksen kokeilun hyväksynnän',async()=>{
 const h=createHarness([sample]);await h.click('tab-library');await h.click(h.action('Vahvista aiempi tapaus'));assert.equal(h.count('verify'),0);assert.equal(h.document.activeElement.id,'reviewer');h.elements.reviewer.value='Harjoitustestaaja';h.confirmations.push(false);await h.click(h.action('Vahvista aiempi tapaus'));assert.equal(h.count('verify'),0);
 await h.click(h.action('Vahvista aiempi tapaus'));assert.equal(h.rows[0].status,'verified');assert(h.confirmText.at(-1).includes('aiemmassa tapauksessa'));assert(h.confirmText.at(-1).includes('ei takaa'));assert.equal(h.calls.find(c=>c.action==='verify').body.confirmed,true);assert(!h.action('Vahvista aiempi tapaus'));
 });
 test('Vahvistuksen jälkeinen listavirhe kertoo tallennetusta vahvistuksesta ja säilyttää piilotetun lomakkeen',async()=>{
 const h=createHarness([sample]);await h.click('tab-library');await h.click(h.action('Muokkaa'));h.input('solution','Kesken oleva muokkaus');const before=h.snapshot();await h.click('tab-library');h.elements.reviewer.value='Testaaja';h.fail('list');await h.click(h.action('Vahvista aiempi tapaus'));assert.equal(h.rows[0].status,'verified');assert(h.elements.notice.textContent.includes('Vahvistus tallennettiin'));assert(h.elements.notice.textContent.includes('Listan päivitys epäonnistui'));assert.deepEqual(h.snapshot(),before);assert.equal(h.document.activeElement.id,'notice');
 });
 test('Muokkaus on luonnos, käytöstä poisto säilyttää historian ja tilat näkyvät tekstinä',async()=>{
 const h=createHarness([{...sample,status:'verified',verified_by:'Testi',verified_at:sample.updated_at}]);await h.click('tab-library');assert(all(h.elements.records).some(e=>e.textContent.includes('Vahvistetut – aiemmassa tapauksessa kokeillut')));await h.click(h.action('Muokkaa'));assert(h.elements.editing.textContent.includes('poistaa aiemman vahvistuksen'));h.input('solution','Päivitetty ohje');await h.submit('editor');assert.equal(h.rows[0].status,'draft');assert.equal(h.rows[0].verified_by,null);assert(!h.elements['panel-library'].hidden);const before=h.snapshot();h.prompts.push(null);await h.click(h.action('Poista käytöstä'));assert.equal(h.count('retire'),0);h.prompts.push('Harjoituksen ohje vanheni');await h.click(h.action('Poista käytöstä'));assert.equal(h.rows[0].status,'retired');assert(all(h.elements.records).some(e=>e.textContent.includes('Poistetut käytöstä – historia')));assert(all(h.elements.records).some(e=>e.textContent.includes('Harjoituksen ohje vanheni')));assert(!h.action('Muokkaa'));assert(!h.action('Vahvista aiempi tapaus'));assert(!h.action('Poista käytöstä'));assert.deepEqual(h.snapshot(),before);
 await h.click('tab-editor');const count=h.count('save');await h.submit('editor');assert.equal(h.count('save'),count);assert.deepEqual(h.snapshot(),before);assert(h.elements.notice.textContent.includes('poistettu käytöstä'));
 });
 test('Poistamisen syy säilyy seuraavassa yrityksessä, jos palvelin hylkää käytöstä poiston',async()=>{
 const h=createHarness([sample]);await h.click('tab-library');h.prompts.push('Kuvitteellinen vanhentunut ohje');h.fail('retire',{error:'Tilapäinen virhe'});await h.click(h.action('Poista käytöstä'));assert.equal(h.rows[0].status,'draft');assert.equal(h.document.activeElement.id,'notice');await h.click(h.action('Poista käytöstä'));assert.equal(h.promptDefaults.at(-1),'Kuvitteellinen vanhentunut ohje');assert.equal(h.rows[0].retirement_reason,'Kuvitteellinen vanhentunut ohje');
 });
 test('Tallentamaton uusi muutos piilottaa vanhan luonnoksen tarkistuspolun kunnes se tallennetaan',async()=>{
 const h=createHarness();await beginEditor(h);await h.submit('editor');assert(!h.elements['saved-next'].hidden);h.input('solution','Uusi tallentamaton muutos');assert(h.elements['saved-next'].hidden);assert(h.elements.editing.textContent.includes('tallentamattomia muutoksia'));await h.click('tab-library');await h.click('tab-editor');assert.equal(h.elements.solution.value,'Uusi tallentamaton muutos');await h.submit('editor');assert(!h.elements['saved-next'].hidden);assert.equal(h.rows.length,1);await h.click('review-saved');assert(all(h.elements.records).some(e=>e.textContent==='Uusi tallentamaton muutos'));
 });
 test('Hakupyyntövirhe säilyttää kuvauksen ja rajaukset, vapauttaa kentät ja piilottaa vanhan tuloksen',async()=>{
 const h=createHarness();h.fail('search',{error:'Kuvitteellinen hakuvirhe'});await search(h);assert.equal(h.elements.query.value,'Kuvitteellinen VPN E42 -ongelma.');for(const key in env)assert.equal(h.elements['filter-'+key].value,env[key]);assert(!h.elements.query.disabled);assert.equal(h.document.activeElement.id,'notice');assert(h.elements['results-section'].hidden);assert(h.elements['next-steps'].hidden);await h.submit('search-form');assert(!h.elements['results-section'].hidden);assert.equal(h.elements.notice.getAttribute('role'),'status');
 });
 test('Vanhentunut hakuvastaus sivuutetaan ja kesken olevan pyynnön kentät lukitaan',async()=>{
 const h=createHarness();const held=h.hold();const pending=search(h);await new Promise(resolve=>setImmediate(resolve));assert(held.resolve);assert(h.elements.query.disabled);h.input('filter-product_version','6.1');h.release(result([hit({...sample,status:'verified'})]));await pending;assert(!h.elements.query.disabled);assert(h.elements['results-section'].hidden);assert(h.elements['next-steps'].hidden);
 });
 test('Tekstit renderöidään tekstinä, eivät HTML:nä',async()=>{
 const malicious={...sample,title:'<img src=x onerror=alert(1)>',solution:'<script>bad()</script>'};const h=createHarness([malicious]);await h.click('tab-library');assert(all(h.elements.records).some(e=>e.textContent===malicious.title));assert(!all(h.elements.records).some(e=>e.tag==='img'||e.tag==='script'));h.setSearch(result([hit({...malicious,status:'verified'})]));await h.click('tab-search');await search(h);assert(all(h.elements.hits).some(e=>e.textContent===malicious.title));
 });
 test('API-asetus käyttää peitettyä kenttää, tyhjentää sen ja säilyttää ratkaisulomakkeen',async()=>{
 const h=createHarness();await beginEditor(h);const before=h.snapshot();h.elements['api-settings-panel'].open=true;
 assert.equal(h.elements['api-key'].type,'password');assert.equal(h.elements['api-key'].getAttribute('autocomplete'),'off');
 h.elements['api-key'].value='fixture-secret-not-a-real-key';h.elements['api-model'].value='gpt-4.1-mini';await h.click('apply-api');
 assert.equal(h.elements['api-key'].value,'');assert.deepEqual(h.snapshot(),before);assert(h.elements['api-setting-status'].textContent.includes('Avain asetettu'));assert(h.elements['api-setting-status'].textContent.includes('ei ole testattu'));
 assert(!h.elements['api-setting-status'].textContent.includes('fixture-secret'));assert.equal(h.count('suggest'),0);assert.equal(h.count('save'),0);
 await h.click('clear-api');assert(h.elements['api-setting-status'].textContent.includes('Avain puuttuu'));assert.deepEqual(h.snapshot(),before);
 h.elements['api-key'].value='fixture-secret-not-a-real-key';h.fail('api-settings',{error:'Syöttövirhe',help:'Liitä pelkkä avain.',code:'invalid_key_format'});await h.click('apply-api');assert.equal(h.elements['api-key'].value,'');assert.deepEqual(h.snapshot(),before);assert(h.elements.notice.textContent.includes('Liitä pelkkä avain.'));
 });
 test('Tekoälypyynnön eteneminen näkyy ja kaksoispainallus tekee vain yhden pyynnön',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const before=h.snapshot();h.hold('suggest');const pending=h.click('suggest');
 assert(h.elements.suggest.disabled);assert.equal(h.elements['api-options'].getAttribute('aria-busy'),'true');assert(h.elements.suggest.textContent.includes('Odotetaan'));assert(h.elements.notice.textContent.includes('yksi API-pyyntö'));assert.deepEqual(h.snapshot(),before);
 await h.elements.suggest.onclick();assert.equal(h.count('suggest'),1);
 h.release({state:'unverified',suggestion:{title:'Testiehdotus',solution:'Kokeilematon.',limitations:'Testi.'}});await pending;
 assert(!h.elements.suggest.disabled);assert.equal(h.elements.suggest.textContent,'Pyydä tekoälyehdotus');assert.equal(h.elements['api-options'].getAttribute('aria-busy'),'false');assert.equal(h.count('save'),0);
 });
 test('API-virheiden täsmälliset toimintaohjeet näkyvät ja kaikki tekstit säilyvät',async()=>{
 const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements.consent.checked=true;const before=h.snapshot();
 for(const code of ['missing_api_key','invalid_api_key','api_authentication','api_forbidden','api_billing','api_model_access','api_rate_limit','api_timeout','api_connection','api_bad_request','api_format']){
 h.fail('suggest',{error:'Kuvitteellinen virhe',help:'Täsmäohje: '+code,code});await h.click('suggest');assert.deepEqual(h.snapshot(),before);assert(h.elements.notice.textContent.includes('Täsmäohje: '+code));assert(h.elements.notice.textContent.includes('Virhekoodi: '+code));assert(!h.elements.suggest.disabled);assert.equal(h.elements['api-options'].getAttribute('aria-busy'),'false');
 }assert.equal(h.count('save'),0);
 });
 test('Palvelun turvalliset virhetiedot näkyvät kummassakin ehdotuspolussa ja lomakkeet säilyvät',async()=>{
 for(const source of ['editor','search'])for(const web of [false,true]){
  const h=createHarness();await beginEditor(h);const before=h.snapshot();
  if(source==='search'){await h.click('tab-search');await search(h);await h.click('start-suggestion');}else h.elements['api-options'].open=true;
  h.elements[source+'-web'].checked=web;h.elements[source==='search'?'search-consent':'consent'].checked=true;
  h.fail('suggest',{error:'Hylätty',help:'Tarkista parametri.',code:'api_bad_request',upstream_status:400,provider_code:'invalid_json_schema',provider_param:'text.format.schema',provider_description:'Palvelu ilmoitti vastausskeeman virheelliseksi.',provider_terms:['web_search','json_schema']});
  await h.click(source==='search'?'search-suggest':'suggest');
  for(const value of ['400','invalid_json_schema','text.format.schema','vastausskeeman','web_search','json_schema'])assert(h.elements.notice.textContent.includes(value));
  assert.deepEqual(h.snapshot(),before);assert.equal(h.calls.filter(c=>c.action==='suggest').at(-1).body.web_search===true,web);assert.equal(h.count('save'),0);
 }
 });
 test('Verkkohaku tekee näkyvästi kaksi peräkkäistä pyyntöä kun lähde hyväksytään',async()=>{
  const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements['editor-web'].checked=true;h.input('editor-vendor','example.com');h.elements.consent.checked=true;
  h.hold('suggest');const pending=h.click('suggest');await new Promise(resolve=>setImmediate(resolve));assert.equal(h.elements['editor-suggest-progress'].textContent,'1/2 Haetaan lähteitä');
  h.release({state:'web_sources_ready',source_request_id:'f'.repeat(32),web_diagnostics:{source_search:{accepted_source_count:1}}});await pending;
  const requests=h.calls.filter(c=>c.action==='suggest');assert.equal(requests.length,2);assert.equal(requests[0].body.web_stage,'search');assert.equal(requests[1].body.web_stage,'compose');assert.equal(requests[1].body.source_request_id,'f'.repeat(32));assert.equal(h.elements['editor-suggest-progress'].textContent,'2/2 Muodostetaan ratkaisuehdotus');
 });
 test('Lähteiden puuttuessa toinen pyyntö jää pois ja tavallinen ehdotus vaatii uuden luvan',async()=>{
  const h=createHarness();await beginEditor(h);h.elements['api-options'].open=true;h.elements['editor-web'].checked=true;h.input('editor-vendor','example.com');h.elements.consent.checked=true;const before=h.snapshot();
  h.respond('suggest',{state:'no_web_sources',message:'Verkkohaku ei tuottanut sovelluksen käytettävissä olevia lähdeosoitteita. Päivityslinkkiä ei voitu varmistaa. Toista API-kutsua ei tehty.',web_diagnostics:{source_search:{accepted_source_count:0},proposal:{status:'not_sent'}}});
  await h.click('suggest');assert.equal(h.count('suggest'),1);assert(h.elements['editor-web-fallback'].hidden===false);assert.equal(h.elements['editor-suggest-progress'].textContent,'Lähteitä ei saatu; vaihetta 2/2 ei lähetetty.');assert.deepEqual(h.snapshot(),before);
  await h.click('editor-web-fallback-button');assert.equal(h.elements['editor-web'].checked,false);assert.equal(h.elements.consent.checked,false);assert(h.elements['editor-send-preview'].textContent.includes('Verkkohaku: Ei'));
  h.elements.consent.checked=true;await h.click('suggest');assert.equal(h.count('suggest'),2);assert.equal(h.calls.filter(c=>c.action==='suggest').at(-1).body.web_search,undefined);
 });
 test('Molemmissa esikatseluissa kerrotaan yleisestä verkkohausta ja puuttuvasta lähteestä',async()=>{
 for(const source of ['editor','search']){
  const h=createHarness();await beginEditor(h);const before=h.snapshot();
  if(source==='search'){await h.click('tab-search');await search(h);await h.click('start-suggestion');}else h.elements['api-options'].open=true;
  const web=h.elements[source+'-web'];web.checked=true;web.handlers.change({target:web});h.input(source+'-vendor','nvidia.com');
  const preview=h.elements[source+'-send-preview'].textContent;assert(preview.includes('yleinen haku'));assert(preview.includes('sovellus tarkistaa'));assert(preview.includes('nvidia.com'));
  assert(preview.includes('kaksi peräkkäistä API-pyyntöä'));
  h.elements[source==='search'?'search-consent':'consent'].checked=true;
  h.respond('suggest',{state:'web_sources_ready',source_request_id:'f'.repeat(32),web_diagnostics:{source_search:{accepted_source_count:1}}});
  h.respond('suggest',{suggestion:{title:'Ehdotus',solution:'Tarkistus',limitations:'Ei testattu',commands:[],links:[],web_search:true,web_diagnostics:{statuses:['completed'],source_count:0,api_source_items:0,api_citation_items:0,proposed_count:1,accepted_count:0,rejected:{domain:0,missing_source:1,insufficient_details:0}}}});
  await h.click(source==='search'?'search-suggest':'suggest');
  assert(all(h.elements['proposal-tools']).some(e=>e.textContent.includes('Hyväksyttävää lähdelinkkiä ei löytynyt')));
  assert(all(h.elements['proposal-tools']).some(e=>e.textContent.includes('Päivityslinkkiä ei voitu varmistaa')));
  assert.deepEqual(h.snapshot(),before);assert.equal(h.count('save'),0);
 }
 });
 test('Ehdotuksen muotoilu käyttää turvallisia elementtejä ja säilyttää siirrettävän alkuperäistekstin',async()=>{
 for(const source of ['editor','search']){
  const h=createHarness();await beginEditor(h);
  if(source==='search'){await h.click('tab-search');await search(h);await h.click('start-suggestion');}else h.elements['api-options'].open=true;
  const solution='## Tarkistus\n1. **Tärkeä** vaihe <img src=x onerror=bad()>',limitations='**Rajat**';
  h.respond('suggest',{suggestion:{title:'Otsikko',solution,limitations,commands:[],links:[]}});
  h.elements[source==='search'?'search-consent':'consent'].checked=true;await h.click(source==='search'?'search-suggest':'suggest');
  const nodes=all(h.elements['proposal-solution']);assert(nodes.some(e=>e.tag==='h5'));assert(nodes.some(e=>e.tag==='strong'&&e.textContent==='Tärkeä'));assert(!nodes.some(e=>e.tag==='img'||e.tag==='script'));assert(nodes.some(e=>e.textContent.includes('<img')));
  let copied;h.navigator.clipboard={writeText:async value=>{copied=value}};await h.click('copy-proposal-solution');assert.equal(copied,solution);await h.click('copy-proposal-limitations');assert.equal(copied,limitations);
  h.confirmations.push(true);await h.click('edit-suggestion');assert(h.elements.solution.value.includes(solution));assert(h.elements.solution.value.includes(limitations));
 }
 });
 test('Erillinen uusi ohje näkyy avattavana ja säilyy kopiossa ja luonnoksessa',async()=>{
 for(const source of ['editor','search']){
  const h=createHarness();await beginEditor(h);if(source==='search'){await h.click('tab-search');await search(h);await h.click('start-suggestion');}else h.elements['api-options'].open=true;
  h.respond('suggest',{suggestion:{title:'Ehdotus',solution:'1. Tarkista laite.',limitations:'Vain testi.',additional_instructions:'Tarkista laitteen malli.',commands:[],links:[]}});
  h.elements[source==='search'?'search-consent':'consent'].checked=true;await h.click(source==='search'?'search-suggest':'suggest');
  assert(!h.elements['proposal-additional'].hidden);assert.equal(h.elements['proposal-additional-text'].textContent,'Tarkista laitteen malli.');
  let copied;h.navigator.clipboard={writeText:async v=>{copied=v}};await h.click('copy-proposal-solution');assert(copied.includes('Tarkista laitteen malli.'));
  h.confirmations.push(true);await h.click('edit-suggestion');assert(h.elements.solution.value.includes(copied));
 }
 });
 test('Semanttinen välilehtirakenne, kenttien nimet, fokus ja kapean näkymän CSS-sopimus',()=>{
 const h=createHarness();for(const name of ['search','editor','library']){const tab=h.elements['tab-'+name],panel=h.elements['panel-'+name];assert.equal(tab.getAttribute('role'),'tab');assert.equal(tab.getAttribute('aria-controls'),panel.id);assert.equal(panel.getAttribute('role'),'tabpanel');assert.equal(panel.getAttribute('aria-labelledby'),tab.id);}
 for(const e of Object.values(h.elements).filter(e=>['input','textarea','select'].includes(e.tag)))assert(html.includes('for="'+e.id+'"')||e.id==='consent','missing visible label '+e.id);
 for(const e of Object.values(h.elements))for(const id of (e.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean))assert(h.elements[id],'missing description '+id);
 assert(html.includes('[hidden]{display:none!important}'));assert(html.includes(':focus-visible'));assert(html.includes('@media(max-width:760px)'));assert(html.includes('.environment-fields{grid-template-columns:1fr}'));assert(html.includes('repeat(3,minmax(0,1fr))'));assert(html.includes('flex-wrap:wrap'));assert(html.includes('min-width:0'));assert.equal(h.elements['search-form'].tag,'form');assert.equal(h.elements.search.type,'submit');
 });

// SOC selection contracts use the same isolated workflow harness as the existing UI tests.
const selectionButtons=h=>all(h.elements.hits).filter(e=>e.className==='secondary select-hit');
const detailAction=(h,label)=>all(h.elements['selected-content']).find(e=>e.tag==='button'&&e.textContent===label);
test('SOC: ei automaattista valintaa, palvelimen järjestys ja ehdokasryhmät säilyvät',async()=>{
 const a={...sample,status:'verified',id:'SOL-z',title:'Z-tapaus'},b={...a,id:'SOL-a',title:'A-tapaus'};
 const h=createHarness();h.setSearch(result([hit(a),hit(b)]));await search(h);
 assert.equal(h.elements['selected-content'].children.length,0);assert(!h.elements['selection-empty'].hidden);
 assert.deepEqual(selectionButtons(h).map(b=>b.getAttribute('aria-label')),['Näytä ratkaisu – Z-tapaus','Näytä ratkaisu – A-tapaus']);
});
test('SOC: valinta näyttää alkuperäiset kentät, varoituksen ja siirtää fokuksen',async()=>{
 const row={...sample,status:'verified',verified_by:'Vahvistaja',verified_at:sample.updated_at};const h=createHarness();h.setSearch(result([hit(row)]));await search(h);const b=selectionButtons(h)[0];await h.click(b);
 assert.equal(h.elements['selected-heading'].textContent,row.title);assert.equal(b.getAttribute('aria-pressed'),'true');assert.equal(h.document.activeElement.id,'selected-heading');
 for(const value of [row.solution,'Ongelma: '+row.problem,'Ympäristö: '+row.environment,'tuote: '+row.product,'tuotteen versio: '+row.product_version])assert(all(h.elements['selected-content']).some(e=>e.textContent===value),value);
 assert(h.elements.notice.textContent.includes('Tarkista soveltuvuus'));assert.equal(h.count('save'),0);assert.equal(h.count('suggest'),0);
});
test('SOC: toinen valinta poistaa edellisen valinnan ja näyttää puuttuvien tietojen varoituksen',async()=>{
 const h=createHarness();h.setSearch(result([hit({...sample,status:'verified'}),hit({...sample,id:'SOL-review',title:'Tarkistettava tapaus',status:'verified'},'needs_review')]));await search(h);const [a,b]=selectionButtons(h);await h.click(a);await h.click(b);
 assert.equal(a.getAttribute('aria-pressed'),'false');assert.equal(b.getAttribute('aria-pressed'),'true');assert(!a._card.className.includes('selected-record'));assert(all(h.elements['selected-content']).some(e=>e.textContent.includes('Ympäristötiedoissa on puutteita')));
});
test('SOC: jokainen hakuun vaikuttava kenttä tyhjentää valitun ratkaisun',async()=>{
 for(const id of ['query','filter-operating_system','filter-product','filter-product_version','backend']){
 const h=createHarness();h.setSearch(result([hit({...sample,status:'verified'})]));await search(h);await h.click(selectionButtons(h)[0]);
 if(id==='backend')h.elements.backend.handlers.change();else h.input(id,'Muuttunut');assert.equal(h.elements['selected-content'].children.length,0,id);assert(!h.elements['selection-empty'].hidden,id);
 }
});
test('SOC: uusi haku, virhe, tyhjä tulos ja turvapysäytys eivät jätä vanhaa ratkaisua näkyviin',async()=>{
 for(const mode of ['error','empty','safety']){const h=createHarness();h.setSearch(result([hit({...sample,status:'verified'})]));await search(h);await h.click(selectionButtons(h)[0]);
 if(mode==='error')h.fail('search');else h.setSearch(mode==='empty'?result([]):{state:'safety_stop',message:'Turvallisuuskeskeytys'});await h.submit('search-form');assert.equal(h.elements['selected-content'].children.length,0);assert(!h.elements['selection-empty'].hidden);}
});
test('SOC: lukutilan dialogi säilyttää tekstin ja palauttaa fokuksen',async()=>{
 const h=createHarness();h.setSearch(result([hit({...sample,status:'verified'})]));await search(h);await h.click(selectionButtons(h)[0]);const expand=detailAction(h,'Avaa isona');await h.click(expand);
 assert(h.elements['record-dialog'].open);assert(all(h.elements['record-dialog-content']).some(e=>e.textContent===sample.solution));await h.click('close-record');assert(!h.elements['record-dialog'].open);assert.equal(h.document.activeElement,expand);
});
test('SOC: muokkaus säilyttää tunnisteen, revision ja kaikki ympäristökentät',async()=>{
 const row={...sample,status:'verified',revision:7};const h=createHarness([row]);h.setSearch(result([hit(row)]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Muokkaa'));
 assert(!h.elements['panel-editor'].hidden);for(const key of fields)assert.equal(h.elements[key].value,row[key]);await h.submit('editor');const call=h.calls.find(c=>c.action==='save');assert.equal(call.body.id,row.id);assert.equal(call.body.revision,7);assert.equal(h.rows[0].status,'draft');assert.equal(h.elements['selected-content'].children.length,0);
});
test('SOC: hallintasiirtymä avaa oikean tietueen muuttamatta keskeneräistä tekstiä',async()=>{
 const row={...sample,status:'verified'};const h=createHarness([row]);await beginEditor(h);h.input('solution','Oma keskeneräinen teksti');const before=h.snapshot();await h.click('tab-search');h.setSearch(result([hit(row)]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Hallinta ja vahvistustiedot'));
 assert(!h.elements['panel-library'].hidden);assert.deepEqual(h.snapshot(),before);assert.equal(h.count('save'),0);assert(all(h.elements.records).some(e=>(e.className||'').includes('selected-record')));
});
test('SOC: valittu ratkaisu ja lukutila esittävät HTML:n kirjaimellisena tekstinä',async()=>{
 const row={...sample,status:'verified',title:'<img src=x onerror=bad()>',solution:'<script>bad()</script>\nKoko teksti'};const h=createHarness();h.setSearch(result([hit(row)]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Avaa isona'));
 for(const id of ['selected-content','record-dialog-content']){assert(all(h.elements[id]).some(e=>e.textContent===row.solution));assert(!all(h.elements[id]).some(e=>e.tag==='img'||e.tag==='script'));}
});
test('SOC: API-valikon avaus ei lähetä ehdotuspyyntöä tai muuta lomaketta',async()=>{
 const h=createHarness();await beginEditor(h);const before=h.snapshot();await h.click('open-api');assert(h.elements['api-settings-panel'].open);assert.equal(h.document.activeElement.id,'api-key');assert.deepEqual(h.snapshot(),before);assert.equal(h.count('suggest'),0);assert.equal(h.count('save'),0);
});

test('SOC jakoteksti sisältää kaikki todelliset kentät eikä istuntotunnistetta',async()=>{const row={...sample,status:'verified',verified_by:'Tarkistaja',verified_at:sample.updated_at,solution:'Vaihe 1\nRajat: vain testissä\nLOPPU'};const h=createHarness();h.setSearch(result([hit(row)]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Avaa isona'));await h.click('share-record');assert(!h.elements['share-options'].hidden);assert(h.elements['share-status'].textContent.includes('ei ole käytettävissä'));});

test('SOC jako käyttää Web Share -rajapintaa ja kopioi vain valitun tietueen kentät',async()=>{const row={...sample,status:'verified',verified_by:'Tarkistaja',verified_at:sample.updated_at,solution:'Vaihe 1\nSoveltuvuuden rajat\nLOPPU'};const h=createHarness();let shared,copied;h.navigator.share=async value=>{shared=value};h.navigator.clipboard={writeText:async value=>{copied=value}};h.setSearch(result([hit(row)]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Avaa isona'));await h.click('share-record');assert.equal(shared.title,row.title);for(const value of [row.title,row.problem,row.environment,row.operating_system,row.product,row.product_version,row.solution,row.id,row.verified_by])assert(shared.text.includes(value));assert(!shared.text.includes('__TOKEN__'));await h.click('copy-record');assert.equal(copied,shared.text);assert(h.elements['share-status'].textContent.includes('kopioitiin'));});
test('SOC jako käsittelee peruutuksen, jakovirheen ja kopiointivirheen',async()=>{const h=createHarness();h.setSearch(result([hit({...sample,status:'verified'})]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Avaa isona'));h.navigator.share=async()=>{const e=Error();e.name='AbortError';throw e};await h.click('share-record');assert(h.elements['share-status'].textContent.includes('peruttiin'));h.navigator.share=async()=>{throw Error()};await h.click('share-record');assert(h.elements['share-status'].textContent.includes('ei onnistunut'));h.navigator.clipboard={writeText:async()=>{throw Error()}};await h.click('copy-record');assert(h.elements['share-status'].textContent.includes('leikepöytälupa'));assert(h.elements['record-dialog'].open);});
test('SOC tulostus kutsuu selaimen tulostusta käyttäjän toiminnolla',async()=>{const h=createHarness();let count=0;h.window.print=()=>count++;h.setSearch(result([hit({...sample,status:'verified'})]));await search(h);await h.click(selectionButtons(h)[0]);await h.click(detailAction(h,'Avaa isona'));assert.equal(count,0);await h.click('print-record');assert.equal(count,1);assert(h.elements['record-dialog'].open);});
