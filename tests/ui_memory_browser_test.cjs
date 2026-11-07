// Real Chromium test with a synthetic localhost server; no user DB or external API.
// node tests/ui_memory_browser_test.cjs [--live] [path-to-chrome-or-edge.exe]
// --live checks the real server at port 8502; all POST requests are blocked.
// --live-search loads that same server's HTML and fulfills POSTs with fixtures in CDP.
// --joint-db uses JOINT_TEST_BASE from tests/ui_joint_test_server.py (temporary SQLite, fake providers).
// Run the live modes sequentially: the application uses a single-threaded HTTPServer.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const liveSearch=process.argv.includes('--live-search');
const live=process.argv.includes('--live')||liveSearch;
const jointDb=process.argv.includes('--joint-db');
const executable=process.argv.slice(2).find(arg=>!arg.startsWith('--'))||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const output=path.resolve(liveSearch?'data/search-suggestion/browser-live':live?'data/ui-readability/live-server/browser':'data/ui-readability/browser');fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,'profile-'));
const updated=fs.readFileSync('app.py','utf8').match(/^APP_UPDATED='([^']+)'/m)[1];
const html=fs.readFileSync('memory.html','utf8').replaceAll('__TOKEN__','browser-fixture-token').replaceAll('__BASE_VERSION__','0.3.1').replaceAll('__APP_UPDATED__',updated);
const legacyText='Alkuperäinen pitkä ratkaisurivi.\n'.repeat(180)+'LOPPU – sisältö säilyy kokonaan.';
const fixture={id:'SOL-browser',title:'Vanha ratkaisu',problem:'Kuvitteellinen ongelma.',environment:'Harjoitusympäristö.',solution:legacyText,status:'verified',revision:1,updated_at:'2026-10-24T10:00:00Z'};
const proposal={title:'Kuvitteellinen <img src=x onerror="window.proposalExecuted=true">',
 solution:'1. Tarkista harjoitussivun zoomaus.\n2. Palauta näkymä normaaliksi.\n<script>window.proposalExecuted=true</script>',
 limitations:'Ei testattu.\nPuuttuva tieto: selaimen versio.\n<a href="javascript:alert(1)">Näytä tämä tekstinä.</a>'};
let records=[{...fixture}],browser,cdp,blocked=0;const calls=[],checks=[],confirmations=[],liveRequests=[],pageErrors=[],jointRequests=[];
let socSearch=null;const syntheticAcceptedUrl='https://support.example.com/help';
let suggestFault=null,holdSuggest=false,releaseSuggest=null,proposalOverride=null;
async function mockedAction(action,body){
 calls.push({action,body});
 if(action==='api-status')return {configured:false,source:'none',model:'gpt-4.1-mini',persistence:'process_memory',last_result:'not_tested'};
 if(action==='list')return {records};
 if(action==='search')return socSearch||{state:'empty',hits:[],compatible_hits:[],review_hits:[]};
 if(action==='suggest'){if(holdSuggest)await new Promise(resolve=>{releaseSuggest=resolve;});if(suggestFault)return {error:'Korvattu API-virhe',code:suggestFault,help:'Tarkista kuvitteellinen API-asetus.'};if(body.web_stage==='search')return {state:'web_sources_ready',source_request_id:'f'.repeat(32),web_diagnostics:{source_search:{accepted_source_count:1,accepted_sources:[{url:syntheticAcceptedUrl,basis:'allowed hostname: exact vendor domain'}]}}};const suggestion=proposalOverride||proposal;if(body.web_stage==='compose')suggestion.web_diagnostics={statuses:['completed'],api_source_items:1,api_citation_items:0,source_count:1,proposed_count:suggestion.links?.length||0,accepted_count:suggestion.links?.length||0,rejected:{domain:0,missing_source:0,insufficient_details:0},text_urls:{found:0,domain:0,missing_source:0,unsafe:0,blocked_commands:0}};return {state:'unverified',suggestion};}
 if(action==='save'){const old=records.find(row=>row.id===body.id);const record={...fixture,...body,id:old?.id||'SOL-browser-new',revision:(old?.revision||0)+1,status:'draft'};records=records.filter(row=>row.id!==record.id);records.push(record);return {record};}
 throw Error('Unexpected mocked action: '+action);
}
const server=http.createServer(async(req,res)=>{
 if(req.method==='GET'&&['/soc-theme.css','/soc-banner.jpg'].includes(req.url)){res.writeHead(200,{'Content-Type':req.url.endsWith('.css')?'text/css':'image/jpeg'});return res.end(fs.readFileSync(path.resolve('.'+req.url)));}
 if(req.method==='GET'&&req.url==='/pikaohje'){res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8'});return res.end(fs.readFileSync('docs/13_ratkaisumuistin_pikaohje.md'));}
 if(req.method==='GET'&&req.url==='/memory'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});return res.end(html);}
 if(req.method!=='POST'||!req.url.startsWith('/api/memory/')){res.writeHead(404);return res.end('{}');}
 const parts=[];for await(const chunk of req)parts.push(chunk);const body=JSON.parse(Buffer.concat(parts).toString()),action=req.url.split('/').pop();const result=await mockedAction(action,body);
 res.writeHead(result.error?502:200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(result));
});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(work,label){for(let attempt=0;attempt<100;attempt++){const value=await work();if(value)return value;await pause(50);}throw Error('Timeout: '+label);}
async function connect(url){const socket=new WebSocket(url),pending=new Map(),handlers=new Map();let serial=0;
 await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
 socket.addEventListener('message',event=>{const message=JSON.parse(event.data);if(message.id){const task=pending.get(message.id);pending.delete(message.id);if(message.error)task?.reject(Error(JSON.stringify(message.error)));else task?.resolve(message.result);}else for(const handle of handlers.get(message.method)||[])Promise.resolve(handle(message.params)).catch(error=>{process.stderr.write(error.message+'\n');});});
 return {send(method,params={}){return new Promise((resolve,reject)=>{const id=++serial;const timer=setTimeout(()=>{pending.delete(id);reject(Error('DevTools timeout: '+method));},15000);pending.set(id,{resolve(value){clearTimeout(timer);resolve(value);},reject(error){clearTimeout(timer);reject(error);}});socket.send(JSON.stringify({id,method,params}));});},on(method,handle){if(!handlers.has(method))handlers.set(method,[]);handlers.get(method).push(handle);},close(){socket.close();}};
}
async function evaluate(fn,...args){const result=await cdp.send('Runtime.evaluate',{expression:`(${fn})(...${JSON.stringify(args)})`,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);return result.result.value;}
async function key(name,modifiers=0){const code={Enter:13,Tab:9,Escape:27}[name];await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code:name,windowsVirtualKeyCode:code,modifiers,...(name==='Enter'?{text:'\r',unmodifiedText:'\r'}:{})});await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code:name,windowsVirtualKeyCode:code,modifiers});}
async function screenshot(name){const result=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(output,name+'.png'),Buffer.from(result.data,'base64'));}
async function loaded(){await until(()=>evaluate(()=>document.readyState==='complete'&&typeof editorSnapshot==='function'),'page loaded');}
async function ready(){await until(()=>evaluate(()=>!busy),'UI ready');}
function check(name,details={}){checks.push({name,passed:true,...details});}

async function aiToolsWorkflow(base){
 const code='ver\necho ä & <test>';
 proposalOverride={title:'Testiehdotus',solution:'1. Tarkista tila.\nOhje: [Tarkistamaton osoite poistettu]',limitations:'Kokeilematon.',commands:[{id:'ai-test',name:'Testikomento',type:'cmd',content:code,description:'Tarkistaa version.',environment:'Testiympäristö',admin:false,effect:'check',impact:'',rollback:'',test_status:'untested',tested_by:'',tested_at:'',test_environment:''},{id:'ai-blocked',name:'Estetty komento',type:'powershell',content:'Invoke-WebRequest [Tarkistamaton osoite poistettu]',description:'Testi',environment:'Windows',admin:false,effect:'check',impact:'',rollback:'',test_status:'untested',tested_by:'',tested_at:'',test_environment:'',blocked:true}],links:[{name:'Ajurihaku',url:'https://support.example.com/help',purpose:'Valitse laite ja käyttöjärjestelmä. Yhteensopivuutta ei ole varmistettu.',kind:'driver_search',applicability:'Ilmoitettu testiympäristö',provenance:'Verkkohaun lähde: https://support.example.com/help',source_url:'https://support.example.com/help'}]};
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 const formatting=await evaluate(()=>{const target=document.createElement('div');renderProposalText(target,'## Otsikko\n1. **Tärkeä** <img src=x>');return {heading:target.querySelector('h5')?.textContent,strong:target.querySelector('strong')?.textContent,text:target.textContent,unsafe:target.querySelectorAll('img,script').length};});
 assert.equal(formatting.heading,'Otsikko');assert.equal(formatting.strong,'Tärkeä');assert(formatting.text.includes('1. Tärkeä <img src=x>'));assert.equal(formatting.unsafe,0);check('Markdown headings and emphasis render as safe DOM elements');
 await evaluate(()=>{document.getElementById('tab-editor').click();for(const [id,value] of Object.entries({title:'Oma teksti',problem:'Kuvitteellinen ongelma',environment:'Testiympäristö',solution:'Säilytettävä teksti'})){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input'));}document.getElementById('api-options').open=true;});
 await pause(100);
 await evaluate(()=>{const web=document.getElementById('editor-web');web.checked=true;web.dispatchEvent(new Event('change'));const vendor=document.getElementById('editor-vendor');vendor.value='example.com';vendor.dispatchEvent(new Event('input'));document.getElementById('consent').checked=true;document.getElementById('suggest').click();});await ready();
 assert.equal(calls.filter(x=>x.action==='suggest').at(-1).body.web_search,true);
 const previewState=await evaluate(()=>({text:document.getElementById('proposal-tools').textContent,notice:document.getElementById('notice').textContent}));assert(previewState.text.includes('Kokeilematon'),JSON.stringify(previewState));assert(previewState.text.includes('Ajurihakusivu'));assert(previewState.text.includes('Valitse laite ja käyttöjärjestelmä. Yhteensopivuutta ei ole varmistettu.'));
 assert(previewState.text.includes(syntheticAcceptedUrl),previewState.text);
 assert.equal(await evaluate(()=>document.querySelectorAll('#proposal-tools h3').length),0);
 assert.equal(await evaluate(()=>{const card=[...document.querySelectorAll('#proposal-tools .tool-card')].find(x=>x.textContent.includes('Estetty komento'));return card.querySelectorAll('button').length;}),0);
 assert.equal(await evaluate(()=>document.querySelectorAll('#proposal-tools input[type=checkbox]').length),2);
 await evaluate(()=>{document.getElementById('proposal-tools').scrollIntoView({block:'start'});Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async x=>window.testCopy=x}});URL.createObjectURL=blob=>{blob.text().then(t=>window.testDownload=t);return 'blob:test'};HTMLAnchorElement.prototype.click=function(){window.testFilename=this.download};});
 await screenshot('ai-tools-preview');
 await evaluate(()=>[...document.querySelectorAll('#proposal-tools button')].find(b=>b.textContent==='Kopioi komento').click());await until(()=>evaluate(()=>window.testCopy!==undefined),'AI copy');assert.equal(await evaluate(()=>window.testCopy),code);
 await evaluate(()=>[...document.querySelectorAll('#proposal-tools button')].find(b=>b.textContent==='Lataa .bat').click());await until(()=>evaluate(()=>window.testDownload!==undefined),'bat');assert.equal(await evaluate(()=>window.testDownload),code);assert.equal(await evaluate(()=>window.testFilename),'ratkaisumuisti.bat');
 await evaluate(()=>{for(const e of document.querySelectorAll('#proposal-tools input[type=checkbox]')){e.checked=true;e.dispatchEvent(new Event('change'));}});
 confirmations.push(false);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();assert.equal(await evaluate(()=>document.getElementById('solution').value),'Säilytettävä teksti');
 confirmations.push(true);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();
 assert.equal(await evaluate(()=>editorTools.commands[0].test_status),'untested');assert.equal(await evaluate(()=>editorTools.links[0].url),'https://support.example.com/help');assert(await evaluate(()=>editorTools.links[0].purpose.includes('Ajurihakusivu')&&editorTools.links[0].purpose.includes('Valitse laite ja käyttöjärjestelmä. Yhteensopivuutta ei ole varmistettu.')));assert(await evaluate(()=>recordCard({id:'SOL-synthetic',title:'Testi',problem:'',environment:'',solution:'Testi',status:'draft',revision:1,updated_at:'2026-10-30T00:00:00Z',tools:editorTools}).card.textContent.includes('Ajurihakusivu')));
 await evaluate(()=>document.getElementById('save-draft').click());await ready();const saved=calls.filter(x=>x.action==='save').at(-1).body;assert.equal(saved.tools.commands.length,1);assert.equal(saved.tools.commands[0].content,code);assert(!JSON.stringify(saved).includes('ai-blocked'));
 const share=await evaluate(record=>recordShareText({...record,title:document.getElementById('title').value,solution:document.getElementById('solution').value,tools:editorTools},false),fixture);assert(share.includes(code));assert(!share.includes('Invoke-WebRequest'));
 check('Saved and shared synthetic proposal exclude the blocked script');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:false});assert(await evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await evaluate(()=>document.getElementById('tab-editor').focus());await key('Tab');assert(await evaluate(()=>document.activeElement!==document.body));
 check('AI preview: opted-in mocked web search, exact copy and .bat, selection, cancellation, untested transfer and 320px');
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 await evaluate(()=>{const q=document.getElementById('query');q.value='Kuvitteellinen hakutilanne';q.dispatchEvent(new Event('input'));document.getElementById('start-suggestion').click();document.getElementById('search-consent').checked=true;document.getElementById('search-suggest').click();});await ready();
 assert.equal(calls.filter(x=>x.action==='suggest').at(-1).body.web_search,undefined);
 await evaluate(()=>{const boxes=document.querySelectorAll('#proposal-tools input[type=checkbox]');boxes[1].checked=true;boxes[1].dispatchEvent(new Event('change'));document.getElementById('edit-suggestion').click();});await ready();
 assert.equal(await evaluate(()=>editorTools.commands.length),0);assert.equal(await evaluate(()=>editorTools.links.length),1);
 check('Search suggestion without web transfers only the selected link');proposalOverride=null;
}
async function socWorkflow(base){
 const row={...fixture,problem:'VPN-yhteys ei muodostu. Tarkka virhe E42.',operating_system:'Windows 11',product:'AuroraVPN',product_version:'5.2',verified_by:'Selaintestaaja',verified_at:fixture.updated_at,solution:'1. Tarkista hyväksytty profiili.\n'+('Pitkä ratkaisuvaihe ja tarkistustieto.\n'.repeat(110))+'Soveltuvuuden rajat: vain ilmoitettu testiympäristö.\n<img src=x onerror="window.injected=true">'};
 const other={...row,id:'SOL-other',title:'Toinen aiempi tapaus'};
 const hit=(record,status)=>({record,score:0.81,environment_check:{status,missing_record_fields:status==='needs_review'?['product_version']:[],missing_query_fields:[]}});
 socSearch={state:'candidates',hits:[hit(row,'declared_match'),hit(other,'needs_review')],compatible_hits:[hit(row,'declared_match')],review_hits:[hit(other,'needs_review')],environment_filter:{excluded_count:1}};
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:375,height:800,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 await evaluate(()=>{const q=document.getElementById('query');q.value='Microsoftin tilille kirjautuminen ei onnistu';q.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('search').click();});await ready();
 const loginHint=await evaluate(()=>{const e=document.getElementById('login-refinement-hint'),s=getComputedStyle(e),r=e.getBoundingClientRect();return {text:e.textContent,hidden:e.hidden,hiddenAttribute:e.hasAttribute('hidden'),display:s.display,position:s.position,width:s.width,height:s.height,overflow:s.overflow,clipPath:s.clipPath,whiteSpace:s.whiteSpace,rect:[r.x,r.y,r.width,r.height],visibleResults:document.querySelectorAll('.hit-card').length,viewport:innerWidth};});
 assert(!loginHint.hidden&&!loginHint.hiddenAttribute);assert(loginHint.text.startsWith('Tarkenna hakua:'));assert(loginHint.visibleResults>0);assert(loginHint.display!=='none'&&loginHint.position!=='absolute'&&loginHint.height!=='1px'&&loginHint.width!=='1px'&&loginHint.clipPath==='none'&&loginHint.rect[2]>100&&loginHint.rect[3]>1);check('SOC login refinement hint appears with results at 375px',loginHint);
 await evaluate(()=>{const q=document.getElementById('query');q.value='Authenticator-ilmoitus ei saavu';q.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.equal(await evaluate(()=>document.getElementById('login-refinement-hint').hidden),true);
 await evaluate(()=>document.getElementById('search').click());await ready();
 assert.equal(await evaluate(()=>{const e=document.getElementById('login-refinement-hint');return {hidden:e.hidden,text:e.textContent};}),{hidden:true,text:''});check('Editing hides the hint and a precise Authenticator search does not restore it');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1536,height:1000,deviceScaleFactor:1,mobile:false});
 await evaluate(()=>{const q=document.getElementById('query');q.value='VPN-yhteys ei muodostu E42';q.dispatchEvent(new Event('input'));document.getElementById('search').click();});await ready();
 assert.equal(await evaluate(()=>document.querySelectorAll('.select-hit').length),2);assert.equal(await evaluate(()=>document.getElementById('selected-content').children.length),0);
 const layout=await evaluate(()=>{const b=s=>document.querySelector(s).getBoundingClientRect();return {filter:b('.soc-filters').x,results:b('.soc-middle').x,detail:b('.soc-detail').x,background:getComputedStyle(document.body).backgroundColor,banner:getComputedStyle(document.querySelector('.hero')).backgroundImage};});
 assert(layout.filter<layout.results&&layout.results<layout.detail);assert(layout.banner.includes('soc-banner.jpg'));assert.equal(layout.background,'rgb(8, 15, 25)');check('SOC desktop has the banner and three real content columns',layout);
 await evaluate(()=>document.getElementById('search').focus());await key('Tab');
 assert(await evaluate(()=>document.activeElement.classList.contains('select-hit')));await key('Enter');
 assert.equal(await evaluate(()=>document.activeElement.id),'selected-heading');assert.equal(await evaluate(()=>document.querySelector('.select-hit').getAttribute('aria-pressed')),'true');
 assert((await evaluate(()=>document.getElementById('selected-content').textContent)).includes(row.solution));assert.equal(await evaluate(()=>document.querySelectorAll('#selected-content img,#selected-content script').length),0);assert.equal(await evaluate(()=>window.injected===true),false);check('Keyboard selection preserves complete text and renders hostile HTML literally');
 await evaluate(()=>document.getElementById('open-about').click());await key('Escape');assert.equal(await evaluate(()=>document.querySelector('.select-hit').getAttribute('aria-pressed')),'true');assert((await evaluate(()=>document.getElementById('selected-content').textContent)).includes(row.solution));check('About dialog preserves the selected record');
 await evaluate(()=>window.scrollTo(0,0));await screenshot('soc-desktop-selected');
 const ax=await cdp.send('Accessibility.getFullAXTree');assert(ax.nodes.some(n=>n.role?.value==='heading'&&n.name?.value===row.title));assert(ax.nodes.some(n=>n.role?.value==='button'&&n.name?.value==='Näytä ratkaisu – '+row.title));assert(ax.nodes.some(n=>n.role?.value==='tab'&&n.name?.value==='Haku'));check('Accessibility tree exposes named tabs, result buttons and selected heading');
 const contrast=await evaluate(()=>{
  const rgb=s=>(s.match(/[\d.]+/g)||[]).map(Number),lum=c=>{const a=c.slice(0,3).map(n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;});return .2126*a[0]+.7152*a[1]+.0722*a[2];};
  return ['#selected-heading','.soc-detail .muted','.soc-detail .detail-note','.select-hit','#search','.state-verified','.tabs [aria-selected=true]','label[for="filter-product"]'].map(selector=>{const e=document.querySelector(selector),style=getComputedStyle(e);let parent=e,bg;while(parent){bg=rgb(getComputedStyle(parent).backgroundColor);if(bg.length===3||bg[3]>0.99)break;parent=parent.parentElement;}const f=lum(rgb(style.color)),b=lum(bg);return {selector,ratio:(Math.max(f,b)+.05)/(Math.min(f,b)+.05)};});
 });for(const value of contrast)assert(value.ratio>=4.5,JSON.stringify(value));check('Representative normal text, controls, badges and warning pass 4.5:1 contrast',{contrast});
 await evaluate(()=>[...document.querySelectorAll('#selected-content button')].find(e=>e.textContent==='Avaa isona').click());assert.equal(await evaluate(()=>document.getElementById('record-dialog').open),true);
 await evaluate(()=>{window.sharedData=null;window.copiedData=null;window.printCount=0;Object.defineProperty(navigator,'share',{configurable:true,writable:true,value:async data=>{window.sharedData=data;}});Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedData=text;}}});window.print=()=>window.printCount++;});
 await evaluate(()=>document.getElementById('share-record').click());await until(()=>evaluate(()=>window.sharedData!==null),'share');const shared=await evaluate(()=>window.sharedData);for(const value of [row.title,row.problem,row.environment,row.solution,row.operating_system,row.product,row.product_version,row.id,row.verified_by])assert(shared.text.includes(value));assert(!shared.text.includes('browser-fixture-token'));await evaluate(()=>document.getElementById('copy-record').click());await until(()=>evaluate(()=>window.copiedData!==null),'clipboard');assert.equal(await evaluate(()=>window.copiedData),shared.text);check('Share and clipboard receive the complete selected record without session token');
 await evaluate(()=>{navigator.share=async()=>{throw new DOMException('cancel','AbortError')};document.getElementById('share-record').click();});await until(()=>evaluate(()=>document.getElementById('share-status').textContent.includes('peruttiin')),'share cancellation');await evaluate(()=>{navigator.share=async()=>{throw Error('failed')};document.getElementById('share-record').click();});await until(()=>evaluate(()=>document.getElementById('share-status').textContent.includes('ei onnistunut')),'share error');await evaluate(()=>{navigator.clipboard.writeText=async()=>{throw Error('failed')};document.getElementById('copy-record').click();});await until(()=>evaluate(()=>document.getElementById('share-status').textContent.includes('leikepöytälupa')),'clipboard error');check('Share cancellation and share/clipboard failures remain in the dialog');
 await evaluate(()=>{document.querySelector('#record-dialog details').open=false;document.getElementById('print-record').click();});assert.equal(await evaluate(()=>document.querySelector('#record-dialog details').open),true);assert.equal(await evaluate(()=>window.printCount),1);await cdp.send('Emulation.setEmulatedMedia',{media:'print'});const printed=await evaluate(()=>{const d=document.getElementById('record-dialog'),p=d.querySelector('details p');return {height:d.getBoundingClientRect().height,body:getComputedStyle(document.body).backgroundColor,hero:getComputedStyle(document.querySelector('.hero')).display,actions:getComputedStyle(document.querySelector('.dialog-actions')).display,solution:p.textContent,whiteSpace:getComputedStyle(p).whiteSpace,overflow:getComputedStyle(d).overflow};});assert.equal(printed.hero,'none');assert.equal(printed.actions,'none');assert.equal(printed.body,'rgb(255, 255, 255)');assert.equal(printed.solution,row.solution);assert.equal(printed.whiteSpace,'pre-wrap');assert.equal(printed.overflow,'visible');assert(printed.height>1500);const pdf=await cdp.send('Page.printToPDF',{preferCSSPageSize:true,printBackground:true});const pdfBytes=Buffer.from(pdf.data,'base64');fs.writeFileSync(path.join(output,'soc-print.pdf'),pdfBytes);const pages=(pdfBytes.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length;assert(pages>=2,'long document spans printed pages');await cdp.send('Emulation.setEmulatedMedia',{media:''});check('A4 print hides navigation and actions and preserves long text across pages',{pages,height:printed.height});
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:false});const mobileDialog=await evaluate(()=>{const d=document.getElementById('record-dialog');return {width:d.scrollWidth,client:d.clientWidth,buttons:[...d.querySelectorAll('.dialog-actions button')].map(x=>({name:x.textContent,width:x.getBoundingClientRect().width}))};});assert(mobileDialog.width<=mobileDialog.client+1);assert.equal(mobileDialog.buttons.length,3);assert(mobileDialog.buttons.every(x=>x.width>0));check('Share and print controls remain reachable at mobile width',mobileDialog);await cdp.send('Emulation.setDeviceMetricsOverride',{width:1536,height:1000,deviceScaleFactor:1,mobile:false});
 await key('Tab');assert(await evaluate(()=>document.getElementById('record-dialog').contains(document.activeElement)));await key('Tab',8);assert(await evaluate(()=>document.getElementById('record-dialog').contains(document.activeElement)));await key('Escape');await until(()=>evaluate(()=>!document.getElementById('record-dialog').open),'read dialog Escape');await until(()=>evaluate(()=>document.activeElement.textContent==='Avaa isona'),'read dialog focus return');check('Read dialog traps native keyboard focus, closes with Escape and restores focus');
 await evaluate(()=>{const f=document.getElementById('filter-product_version');f.value='6.0';f.dispatchEvent(new Event('input'));});assert.equal(await evaluate(()=>document.getElementById('selected-content').children.length),0);check('Changing an environment field removes the selected stale solution');
 await evaluate(()=>document.getElementById('search').click());await ready();await evaluate(()=>document.querySelector('.select-hit').click());
 for(const width of [320,375,768]){
  await cdp.send('Emulation.setDeviceMetricsOverride',{width,height:800,deviceScaleFactor:1,mobile:false});
  if(width<=760)await until(()=>evaluate(()=>!document.getElementById('filter-disclosure').open),'mobile filters collapsed');
  const state=await evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,open:document.getElementById('filter-disclosure').open,columns:getComputedStyle(document.querySelector('.workspace')).gridTemplateColumns}));assert(state.scrollWidth<=width+1,JSON.stringify(state));if(width<=760)assert(!state.open);await screenshot('soc-width-'+width);check('SOC reflows without horizontal scrolling at '+width+'px',state);
 }
 // Browser zoom reduces CSS viewport size; emulate that 200% viewport at desktop width.
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:768,height:500,deviceScaleFactor:2,mobile:false});assert(await evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await screenshot('soc-200-percent-reflow');check('200 percent equivalent desktop reflow retains all controls without horizontal overflow');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1536,height:1000,deviceScaleFactor:1,mobile:false});
 await evaluate(()=>[...document.querySelectorAll('#selected-content button')].find(e=>e.textContent==='Muokkaa').click());assert.equal(await evaluate(()=>document.getElementById('solution').value),row.solution);check('Selected real-record fields transfer intact into the existing editor');
 socSearch=null;
}

async function blankToolsWorkflow(base){
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 await evaluate(()=>{document.getElementById('tab-editor').click();document.getElementById('tools-editor').open=true;});
 assert.equal(await evaluate(()=>document.querySelectorAll('#command-editor-list .tool-edit-card').length),0);
 await evaluate(()=>{for(const [id,value] of Object.entries({title:'Tyhjän kortin testi',problem:'Kuvitteellinen ongelma',environment:'Testiympäristö',solution:'Tarkista tila.'})){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}));}document.getElementById('add-command').click();document.getElementById('add-link').click();document.getElementById('save-draft').click();});await ready();
 const saved=calls.filter(call=>call.action==='save').at(-1);assert(saved);assert.deepEqual(saved.body.tools,{commands:[],links:[]});assert.equal(await evaluate(()=>document.getElementById('title').value),'Tyhjän kortin testi');
 await evaluate(()=>{document.getElementById('add-command').click();const box=document.querySelector('#command-editor-list .tool-edit-card'),l=[...box.querySelectorAll('label')].find(x=>x.textContent==='Suoritettava sisältö'),f=document.getElementById(l.htmlFor);f.value='ver';f.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('save-draft').click();});
 const state=await evaluate(()=>{const box=document.querySelector('#command-editor-list .tool-edit-card'),label=[...box.querySelectorAll('label')].find(x=>x.textContent==='Nimi'),field=document.getElementById(label.htmlFor),error=document.getElementById(field.getAttribute('aria-describedby'));return {invalid:field.getAttribute('aria-invalid'),focus:document.activeElement===field,error:error.textContent,visible:!error.hidden,content:[...box.querySelectorAll('textarea')][0].value,title:document.getElementById('title').value};});assert.equal(state.invalid,'true');assert(state.visible&&state.focus&&state.error.includes('pakollinen'));assert.equal(state.content,'ver');assert.equal(state.title,'Tyhjän kortin testi');assert.equal(calls.filter(call=>call.action==='save').at(-1),saved);check('Blank tool cards are omitted; incomplete cards show adjacent errors and preserve text');
}

async function aboutWorkflow(base){
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();await evaluate(()=>{document.getElementById('tab-editor').click();document.getElementById('solution').value='Tallentamaton testiteksti';document.getElementById('solution').dispatchEvent(new Event('input'));});const before=await evaluate(()=>editorSnapshot());
 for(const tab of ['tab-search','tab-editor','tab-library']){await evaluate(id=>document.getElementById(id).click(),tab);await ready();await evaluate(()=>document.getElementById('open-about').focus());await key('Enter');assert(await evaluate(()=>document.getElementById('about-dialog').open));assert.equal(await evaluate(()=>document.activeElement.id),'about-heading');await key('Tab');assert.equal(await evaluate(()=>document.activeElement.id),'about-github');await key('Tab',8);assert.equal(await evaluate(()=>document.activeElement.id),'close-about');await key('Escape');await until(()=>evaluate(()=>!document.getElementById('about-dialog').open),'about Escape');assert.equal(await evaluate(()=>document.activeElement.id),'open-about');assert.equal(await evaluate(()=>editorSnapshot()),before);}
 await evaluate(()=>document.getElementById('open-about').click());await screenshot('about-desktop');const values=await evaluate(async()=>({about:document.getElementById('about-dialog').textContent,github:document.getElementById('about-github').href,rel:document.getElementById('about-github').rel,target:document.getElementById('about-github').target,guide:document.getElementById('about-guide').getAttribute('href'),guideText:await(await fetch('/pikaohje')).text()}));assert(values.about.includes('Sovellus päivitetty: '+updated));assert.equal(values.github,'https://github.com/kauppinen1977-spec/ai-service-desk-assistant');assert.equal(values.rel,'noopener noreferrer');assert.equal(values.target,'_blank');assert.equal(values.guide,'/pikaohje');assert(values.guideText.includes('Ratkaisumuistin pikaohje'));await evaluate(()=>document.getElementById('close-about').click());assert.equal(await evaluate(()=>document.activeElement.id),'open-about');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:false});await evaluate(()=>document.getElementById('open-about').click());const mobile=await evaluate(()=>{const d=document.getElementById('about-dialog');return {width:d.getBoundingClientRect().width,height:d.getBoundingClientRect().height,viewport:innerWidth,scrollWidth:d.scrollWidth,clientWidth:d.clientWidth,pageWidth:document.documentElement.scrollWidth};});assert(mobile.width<=320&&mobile.height<=700&&mobile.scrollWidth<=mobile.clientWidth+1&&mobile.pageWidth<=320);await screenshot('about-mobile');await key('Escape');assert.equal(await evaluate(()=>document.activeElement.id),'open-about');assert.equal(await evaluate(()=>editorSnapshot()),before);check('About dialog: all tabs, focus trap, Escape, local guide and mobile',mobile);
}

async function searchWorkflow(base){
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 await evaluate(()=>{document.getElementById('tab-editor').click();for(const [id,value] of Object.entries({title:'Oma keskeneräinen otsikko',problem:'Oma ongelma.',environment:'Oma ympäristö.',solution:'Oma keskeneräinen teksti.'})){const f=document.getElementById(id);f.value=value;f.dispatchEvent(new Event('input'));}document.getElementById('tab-search').click();for(const [id,value] of Object.entries({query:'Kuvitteellinen VPN-yhteysvirhe.','filter-operating_system':'Windows 11','filter-product':'AuroraVPN','filter-product_version':'5.2','search-environment':'Kuvitteellinen toimistolaite.'})){const f=document.getElementById(id);f.value=value;f.dispatchEvent(new Event('input'));}});
 const before=await evaluate(()=>editorSnapshot()),sends=calls.filter(call=>call.action==='suggest').length,saves=calls.filter(call=>call.action==='save').length;
 await evaluate(()=>document.getElementById('search').click());await ready();assert.equal(calls.filter(call=>call.action==='suggest').length,sends);
 await evaluate(()=>document.getElementById('start-suggestion').click());assert.equal(await evaluate(()=>document.getElementById('panel-search').hidden),false);
 const preview=await evaluate(()=>document.getElementById('search-send-preview').textContent);for(const value of ['Kuvitteellinen VPN-yhteysvirhe.','Windows 11','AuroraVPN','5.2','Kuvitteellinen toimistolaite.'])assert(preview.includes(value));await evaluate(()=>document.getElementById('search-api-options').scrollIntoView({block:'start'}));await screenshot('search-consent');
 await evaluate(()=>document.getElementById('search-suggest').click());await ready();assert.equal(calls.filter(call=>call.action==='suggest').length,sends);check('Search preview shows exact input and requires consent without sending on search or opening');
 holdSuggest=true;await evaluate(()=>{document.getElementById('search-consent').checked=true;document.getElementById('search-suggest').click();});await until(()=>releaseSuggest,'held suggestion');
 assert.equal(await evaluate(()=>document.getElementById('search-suggest').disabled),true);assert.equal(await evaluate(()=>document.getElementById('search-api-options').getAttribute('aria-busy')),'true');await evaluate(()=>requestSuggestion('search'));assert.equal(calls.filter(call=>call.action==='suggest').length,sends+1);
 holdSuggest=false;releaseSuggest();releaseSuggest=null;await ready();
 const request=calls.filter(call=>call.action==='suggest').at(-1).body;assert.deepEqual(request,{problem:'Kuvitteellinen VPN-yhteysvirhe.',environment:'Kuvitteellinen toimistolaite.',operating_system:'Windows 11',product:'AuroraVPN',product_version:'5.2',send_to_api:true});
 assert.equal(await evaluate(()=>editorSnapshot()),before);assert.equal(await evaluate(()=>document.getElementById('suggestion-preview').parentElement.id),'search-proposal-home');assert.equal(await evaluate(()=>document.getElementById('panel-search').hidden),false);assert.equal(await evaluate(()=>document.getElementById('proposal-solution').textContent),proposal.solution);assert.equal(await evaluate(()=>document.querySelectorAll('#suggestion-preview img,#suggestion-preview script,#suggestion-preview a').length),0);check('Search request sends all declared fields once, preserves unfinished editor, and shows a literal two-section preview');
 await evaluate(()=>document.getElementById('suggestion-preview').scrollIntoView({block:'start'}));await screenshot('search-preview');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:false});assert(await evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await evaluate(()=>document.getElementById('suggestion-preview').scrollIntoView({block:'start'}));await screenshot('search-preview-narrow');await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 confirmations.push(false);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();assert.equal(await evaluate(()=>editorSnapshot()),before);assert.equal(await evaluate(()=>document.getElementById('panel-search').hidden),false);
 confirmations.push(true);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();assert.equal(await evaluate(()=>document.getElementById('panel-editor').hidden),false);assert.equal(await evaluate(()=>document.getElementById('problem').value),request.problem);assert.equal(await evaluate(()=>document.getElementById('environment').value),request.environment);assert.equal(await evaluate(()=>document.getElementById('product_version').value),'5.2');assert.equal(calls.filter(call=>call.action==='save').length,saves);check('Search transfer cancellation preserves text; explicit transfer opens editor with all fields and never saves');
 await evaluate(()=>{document.getElementById('tab-search').click();for(const id of ['filter-operating_system','filter-product','filter-product_version','search-environment']){const f=document.getElementById(id);f.value='';f.dispatchEvent(new Event('input'));}document.getElementById('search').click();});await ready();await evaluate(()=>{document.getElementById('start-suggestion').click();document.getElementById('search-consent').checked=true;document.getElementById('search-suggest').click();});await ready();assert.deepEqual(calls.filter(call=>call.action==='suggest').at(-1).body,{problem:request.problem,environment:'',send_to_api:true});check('Search suggestion works with every optional field empty');
 const unchanged=await evaluate(()=>editorSnapshot());suggestFault='api_billing';await evaluate(()=>{document.getElementById('search-consent').checked=true;document.getElementById('search-suggest').click();});await ready();assert((await evaluate(()=>document.getElementById('notice').textContent)).includes('api_billing'));assert((await evaluate(()=>document.getElementById('notice').textContent)).includes('Tarkista kuvitteellinen API-asetus.'));assert.equal(await evaluate(()=>editorSnapshot()),unchanged);suggestFault=null;check('Search provider error retains input and editor and shows the specific code and help');
}

// The supplied localhost server must use a synthetic SQLite DB, a simulated
// embedding failure and a fake suggestion provider. No real API is contacted.
async function jointDbWorkflow(base){
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:375,height:800,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 assert.equal(await evaluate(()=>document.getElementById('backend').value),'keyword');
 await evaluate(()=>{const b=document.getElementById('backend');b.value='joint';b.dispatchEvent(new Event('change'));const q=document.getElementById('query');q.value='Näyttö jumittaa';q.dispatchEvent(new Event('input'));document.getElementById('search').focus();});
 await key('Enter');await ready();
 const first=await evaluate(()=>{const n=document.getElementById('fallback-notice'),card=document.querySelector('.hit-card'),details=card?.querySelector('details'),r=card?.getBoundingClientRect();return {notice:n.textContent,visible:!n.hidden,card:card?.innerText,detailsOpen:details?.open,scoreInDetails:details?.textContent.includes('Hakupisteet:'),width:innerWidth,scrollWidth:document.documentElement.scrollWidth,cardLeft:r?.left,cardRight:r?.right};});
 assert(first.visible&&first.notice==='Merkityshaku ei ole käytettävissä. Näytetään sanahaun tulokset.');
 assert(first.card.includes('Ratkaisusta puuttuu: tuote, tuotteen versio'));assert.equal(first.detailsOpen,false);assert(first.scoreInDetails);
 assert(first.scrollWidth<=375&&first.cardLeft>=0&&first.cardRight<=375);await screenshot('joint-synthetic-375');
 await evaluate(()=>document.querySelector('.select-hit').focus());await key('Enter');
 assert.equal(await evaluate(()=>document.querySelector('.select-hit').getAttribute('aria-pressed')),'true');
 assert.equal(await evaluate(()=>document.getElementById('fallback-notice').hidden),false);
 assert.equal(await evaluate(()=>document.activeElement.id),'selected-heading');
 check('375px fallback notice and visible missing fields survive keyboard result selection',first);
 await evaluate(()=>{const b=document.getElementById('backend');b.value='keyword';b.dispatchEvent(new Event('change'));const q=document.getElementById('query');q.value='Tulostin paperitukos';q.dispatchEvent(new Event('input'));document.getElementById('search').focus();});
 await key('Enter');await ready();
 assert.equal(await evaluate(()=>document.getElementById('fallback-notice').hidden),true);
 assert((await evaluate(()=>document.getElementById('hits').innerText)).includes('Hakuehdokkaita ei löytynyt.'));
 assert(!(await evaluate(()=>document.getElementById('notice').textContent)).includes('Merkityshaku ei ole käytettävissä.'));
 check('New ordinary empty search clears the model-failure notice');
 const count=async()=>await(await fetch(base+'/test/count')).json();const before=await count();
 await evaluate(()=>document.getElementById('start-suggestion').focus());await key('Enter');
 await evaluate(()=>{document.getElementById('search-consent').checked=true;document.getElementById('search-suggest').focus();});await key('Enter');await ready();
 assert.equal(await evaluate(()=>document.getElementById('edit-suggestion').textContent),'Siirrä muokattavaksi');
 assert.deepEqual(await count(),before);
 for(let i=0;i<20&&!(await evaluate(()=>document.activeElement.id==='edit-suggestion'));i++)await key('Tab');
 assert.equal(await evaluate(()=>document.activeElement.id),'edit-suggestion');await key('Enter');await ready();
 assert.equal(await evaluate(()=>document.getElementById('panel-editor').hidden),false);assert.deepEqual(await count(),before);
 for(let i=0;i<30&&!(await evaluate(()=>document.activeElement.id==='save-draft'));i++)await key('Tab');
 assert.equal(await evaluate(()=>document.activeElement.id),'save-draft');await key('Enter');await ready();
 const after=await count();assert.equal(after.total,before.total+1);assert.equal(after.drafts,before.drafts+1);
 check('Keyboard transfer does not save; separate save creates one synthetic SQLite draft',{before,after});
}

async function vendorToggleWorkflow(base){
 for(const source of ['search','editor']){
  await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
  if(source==='search'){
   await evaluate(()=>{const q=document.getElementById('query');q.value='Tulostin ei vedä paperia sisään';q.dispatchEvent(new Event('input'));document.getElementById('search').click();});await ready();
   await evaluate(()=>document.getElementById('start-suggestion').click());
  }else{
   await evaluate(()=>{document.getElementById('tab-editor').click();for(const [id,value] of Object.entries({problem:'Tulostin ei vedä paperia sisään',environment:'Synteettinen testiympäristö'})){const f=document.getElementById(id);f.value=value;f.dispatchEvent(new Event('input'));}document.getElementById('api-options').open=true;});
  }
  assert(await evaluate(s=>document.getElementById(s+'-vendor-field').hidden,source));
  await evaluate(s=>{const web=document.getElementById(s+'-web');web.checked=true;web.dispatchEvent(new Event('change'));const f=document.getElementById(s+'-vendor');f.value='Brother';f.dispatchEvent(new Event('input'));},source);
  assert(!(await evaluate(s=>document.getElementById(s+'-vendor-field').hidden,source)));
  const before=jointRequests.length;await evaluate(s=>{document.getElementById(s==='search'?'search-consent':'consent').checked=true;document.getElementById(s==='search'?'search-suggest':'suggest').click();},source);await ready();
  const invalid=await evaluate(s=>({error:document.getElementById(s+'-vendor-error').innerText,hidden:document.getElementById(s+'-vendor-error').hidden,invalid:document.getElementById(s+'-vendor').getAttribute('aria-invalid'),focus:document.activeElement.id}),source);
  assert(!invalid.hidden&&invalid.error.includes('example.com'));assert.equal(invalid.invalid,'true');assert.equal(invalid.focus,source+'-vendor');assert.equal(jointRequests.length,before);
  await evaluate(s=>{const web=document.getElementById(s+'-web');web.checked=false;web.dispatchEvent(new Event('change'));},source);
  const off=await evaluate(s=>({hidden:document.getElementById(s+'-vendor-field').hidden,errorHidden:document.getElementById(s+'-vendor-error').hidden,value:document.getElementById(s+'-vendor').value,preview:document.getElementById(s+'-send-preview').innerText,consent:document.getElementById(s==='search'?'search-consent':'consent').checked}),source);
  assert(off.hidden&&off.errorHidden&&!off.consent);assert.equal(off.value,'Brother');assert(!off.preview.includes('Brother'));assert(off.preview.includes('Verkkohaku: Ei'));
  await evaluate(s=>{document.getElementById(s==='search'?'search-consent':'consent').checked=true;document.getElementById(s==='search'?'search-suggest':'suggest').click();},source);await ready();
  assert.equal(jointRequests.length,before+1);const sent=jointRequests.at(-1);assert(!('vendor_domain' in sent));assert(!('web_search' in sent));assert(sent.send_to_api);assert(!(await evaluate(()=>document.getElementById('suggestion-preview').hidden)));
  check('Invalid Brother is explained beside '+source+' field and omitted after web search is disabled');
 }
}

(async()=>{
 if(!live&&!jointDb)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base=jointDb?process.env.JOINT_TEST_BASE:live?'http://127.0.0.1:8502':'http://127.0.0.1:'+server.address().port;
 if(jointDb&&!/^http:\/\/127\.0\.0\.1:\d+$/.test(base||''))throw Error('JOINT_TEST_BASE must identify the isolated localhost test server');
 browser=spawn(executable,['--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--disable-extensions','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,'--window-size=1280,900','about:blank'],{windowsHide:true,stdio:'ignore'});
 browser.on('error',error=>{throw error;});
 const portFile=path.join(profile,'DevToolsActivePort');await until(()=>fs.existsSync(portFile),'Chromium DevTools');const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
 const target=await(await fetch('http://127.0.0.1:'+port+'/json/new?about:blank',{method:'PUT'})).json();cdp=await connect(target.webSocketDebuggerUrl);
 await cdp.send('Page.enable');await cdp.send('Runtime.enable');
 cdp.on('Runtime.exceptionThrown',event=>pageErrors.push(event.exceptionDetails.text));
 cdp.on('Page.javascriptDialogOpening',()=>cdp.send('Page.handleJavaScriptDialog',{accept:confirmations.length?confirmations.shift():true}));
 cdp.on('Fetch.requestPaused',async event=>{const action=event.request.url.startsWith(base+'/api/memory/')?event.request.url.split('/').pop():'';if(jointDb&&action==='suggest'&&event.request.method==='POST')jointRequests.push(JSON.parse(event.request.postData||'{}'));if(liveSearch&&event.request.method==='POST'&&['search','suggest','api-status'].includes(action)){liveRequests.push({url:event.request.url,method:'POST',mocked:true,allowed:false});const result=await mockedAction(action,JSON.parse(event.request.postData));return cdp.send('Fetch.fulfillRequest',{requestId:event.requestId,responseCode:result.error?502:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(result)).toString('base64')});}const local=live?['/memory','/soc-theme.css','/soc-banner.jpg'].some(route=>event.request.url===base+route)&&event.request.method==='GET':event.request.url.startsWith(base+'/');if(live)liveRequests.push({url:event.request.url,method:event.request.method,allowed:local});if(!local)blocked++;return cdp.send(local?'Fetch.continueRequest':'Fetch.failRequest',{requestId:event.requestId,...(local?{}:{errorReason:'BlockedByClient'})});});
 await cdp.send('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 if(jointDb){await jointDbWorkflow(base);await vendorToggleWorkflow(base);assert.equal(pageErrors.length,0);const result={browser:(await cdp.send('Browser.getVersion')).product,checks,page_errors:pageErrors,external_api_calls:0,synthetic_sqlite:true};console.log(JSON.stringify(result,null,2));return;}
 if(liveSearch){await searchWorkflow(base);const result={url:base+'/memory',browser:(await cdp.send('Browser.getVersion')).product,checks,page_errors:pageErrors,requests:liveRequests,external_api_calls:0,database_actions:0};assert.equal(pageErrors.length,0);assert(!liveRequests.some(request=>request.method==='POST'&&request.allowed));fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));return;}
 if(live){
  assert.equal(await evaluate(()=>location.href),base+'/memory');
  assert.equal(await evaluate(()=>document.documentElement.outerHTML.includes('id="expand-solution"')),true);
  await evaluate(()=>document.getElementById('tab-editor').click());
  const initial=await evaluate(()=>{const f=document.getElementById('solution'),b=document.getElementById('expand-solution');f.focus();return {height:f.getBoundingClientRect().height,buttonVisible:b.getClientRects().length>0,buttonLabel:b.textContent};});
  assert(initial.buttonVisible);assert.equal(initial.buttonLabel,'Avaa isona');check('Live server shows the expand button',initial);
  const text=Array.from({length:40},(_,i)=>(i+1)+'. Kuvitteellinen selaintarkistuksen ratkaisurivi.').join('\n');
  await cdp.send('Input.insertText',{text});
  const grown=await evaluate(()=>{const f=document.getElementById('solution');return {height:f.getBoundingClientRect().height,scrollHeight:f.scrollHeight,clientHeight:f.clientHeight};});
  assert(grown.height>initial.height+100);assert(grown.scrollHeight>grown.clientHeight);check('Live solution field grows when long text is typed',grown);
  await evaluate(()=>document.getElementById('expand-solution').scrollIntoView({block:'center'}));await screenshot('live-editor');
  await evaluate(()=>document.getElementById('expand-solution').focus());await key('Enter');
  assert.equal(await evaluate(()=>document.getElementById('solution-dialog').open),true);assert.equal(await evaluate(()=>document.activeElement.id),'solution');
  await evaluate(()=>{const f=document.getElementById('solution');f.setSelectionRange(f.value.length,f.value.length);});
  const addition='\nIsossa muokkaimessa lisätty tallentamaton tarkennus.';await cdp.send('Input.insertText',{text:addition});await screenshot('live-expanded');
  await key('Tab');await key('Enter');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'live close button');
  assert.equal(await evaluate(()=>document.getElementById('solution').value),text+addition);assert.equal(await evaluate(()=>document.activeElement.id),'expand-solution');check('Live expanded editor opens and retains edits after the close button');
  await key('Enter');await key('Escape');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'live Escape');
  assert.equal(await evaluate(()=>document.getElementById('solution').value),text+addition);check('Live Escape close retains edits');await screenshot('live-returned');
  assert.equal(pageErrors.length,0);assert.equal(liveRequests.filter(request=>request.allowed&&request.method==='POST').length,0);
  const result={url:base+'/memory',browser:(await cdp.send('Browser.getVersion')).product,checks,page_errors:pageErrors,requests:liveRequests,external_api_calls:0,database_actions:0};
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));return;
 }
 await evaluate(()=>document.getElementById('tab-library').click());await ready();
 await evaluate(()=>[...document.querySelectorAll('#records button')].find(button=>button.textContent==='Muokkaa').click());
 assert.equal(await evaluate(()=>document.getElementById('solution').value),legacyText);check('Legacy text is preserved when opened');
 const initial=await evaluate(()=>{const f=document.getElementById('solution'),s=getComputedStyle(f);return {height:f.getBoundingClientRect().height,scrollHeight:f.scrollHeight,clientHeight:f.clientHeight,overflow:s.overflowY,line:parseFloat(s.lineHeight)};});
 assert(initial.height>300&&initial.height<530);assert(initial.scrollHeight>initial.clientHeight);assert.equal(initial.overflow,'auto');check('Long text grows to approximately 20 lines and scrolls internally',initial);
 await evaluate(()=>document.getElementById('solution').scrollIntoView({block:'center'}));await screenshot('desktop-long');
 // Use the actual native resize handle, then type to verify automatic sizing respects it.
 const rect=await evaluate(()=>{const r=document.getElementById('solution').getBoundingClientRect();return {x:r.right-4,y:r.bottom-4};});
 await cdp.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x,y:rect.y});await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',x:rect.x,y:rect.y,button:'left',clickCount:1});
 await cdp.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:rect.x,y:rect.y+95,button:'left',buttons:1});await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:rect.x,y:rect.y+95,button:'left',clickCount:1});
 const manual=await evaluate(()=>document.getElementById('solution').getBoundingClientRect().height);assert(manual>initial.height+40);
 await evaluate(()=>{const f=document.getElementById('solution');f.focus();f.setSelectionRange(f.value.length,f.value.length);});await cdp.send('Input.insertText',{text:'\nKäsin suurennetun kentän lisäys.'});
 assert((await evaluate(()=>document.getElementById('solution').getBoundingClientRect().height))>=manual-2);check('Native manual resize survives later typing',{height:manual});
 const beforeModal=await evaluate(()=>document.getElementById('solution').value);
 await evaluate(()=>document.getElementById('expand-solution').focus());await key('Enter');
 await until(()=>evaluate(()=>document.getElementById('solution-dialog').open),'modal open');
 assert.equal(await evaluate(()=>document.activeElement.id),'solution');assert.equal(await evaluate(()=>document.getElementById('solution').form.id),'editor');
 await key('Tab');assert.equal(await evaluate(()=>document.activeElement.id),'close-solution');await key('Tab');assert.equal(await evaluate(()=>document.activeElement.id),'solution');await key('Tab',8);assert.equal(await evaluate(()=>document.activeElement.id),'close-solution');
 await key('Tab');await cdp.send('Input.insertText',{text:'\nIsossa muokkaimessa tehty lisäys.'});const expanded=await evaluate(()=>document.getElementById('solution').value);assert(expanded.startsWith(beforeModal));
 await screenshot('desktop-modal');await key('Escape');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'Escape close');
 assert.equal(await evaluate(()=>document.activeElement.id),'expand-solution');assert.equal(await evaluate(()=>document.getElementById('solution').value),expanded);check('Keyboard activation, modal focus trap, Shift+Tab, Escape, focus return and text retention');
 await evaluate(()=>document.getElementById('expand-solution').focus());await key('Enter');await key('Tab');await key('Enter');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'button close');assert.equal(await evaluate(()=>document.getElementById('solution').value),expanded);check('Close button retains all text');
 await evaluate(()=>document.getElementById('save-draft').click());await ready();assert.equal(calls.find(call=>call.action==='save').body.solution,expanded);assert.equal(records[0].status,'draft');check('Legacy text and modal changes save as a draft in the in-memory fixture only');
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
 await evaluate(()=>{document.getElementById('tab-editor').click();for(const [id,value] of Object.entries({title:'Keskeneräinen otsikko',problem:'Kuvitteellinen zoomausongelma.',environment:'Harjoitusselain.',solution:'Oma keskeneräinen ratkaisu.'})){const f=document.getElementById(id);f.value=value;f.dispatchEvent(new Event('input'));}document.getElementById('api-options').open=true;document.getElementById('consent').checked=true;});
 const before=await evaluate(()=>editorSnapshot()),savedBefore=calls.filter(call=>call.action==='save').length;
 await evaluate(()=>document.getElementById('suggest').click());await ready();
 assert.equal(await evaluate(()=>editorSnapshot()),before);assert.equal(await evaluate(()=>document.activeElement.id),'suggestion-heading');
 assert.equal(await evaluate(()=>document.querySelectorAll('#suggestion-preview img,#suggestion-preview script,#suggestion-preview a').length),0);assert.equal(await evaluate(()=>window.proposalExecuted===true),false);
 assert.equal(await evaluate(()=>document.getElementById('proposal-solution').textContent),proposal.solution);assert.equal(await evaluate(()=>document.getElementById('limitations').textContent),proposal.limitations);check('Suggestion is a readable untested preview; HTML stays literal; editor is unchanged');
 confirmations.push(false);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();assert.equal(await evaluate(()=>editorSnapshot()),before);check('Cancelled replacement preserves unfinished text');
 confirmations.push(true);await evaluate(()=>document.getElementById('edit-suggestion').click());await ready();
 const combined=proposal.solution+'\n\nSoveltuvuuden rajat ja puuttuvat tiedot:\n'+proposal.limitations;assert.equal(await evaluate(()=>document.getElementById('solution').value),combined);assert.equal(calls.filter(call=>call.action==='save').length,savedBefore);check('Explicit transfer includes both sections and does not save');
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:320,height:700,deviceScaleFactor:1,mobile:false});
 await evaluate(()=>document.getElementById('suggestion-heading').scrollIntoView({block:'start'}));await screenshot('narrow-preview');
 assert(await evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await evaluate(()=>document.getElementById('expand-solution').focus());await key('Enter');await screenshot('narrow-modal');
 const narrow=await evaluate(()=>{const d=document.getElementById('solution-dialog'),f=document.getElementById('solution'),b=document.getElementById('close-solution'),r=d.getBoundingClientRect();return {width:r.width,height:r.height,viewportWidth:innerWidth,viewportHeight:innerHeight,dialogScrollWidth:d.scrollWidth,dialogClientWidth:d.clientWidth,fieldHeight:f.getBoundingClientRect().height,closeBottom:b.getBoundingClientRect().bottom};});
 assert(narrow.width<=320&&narrow.height<=700);assert(narrow.dialogScrollWidth<=narrow.dialogClientWidth+1);assert(narrow.fieldHeight>=100);assert(narrow.closeBottom<=700);check('320px viewport has no horizontal overflow and the modal close control is reachable',narrow);
 await key('Tab');assert.equal(await evaluate(()=>document.activeElement.id),'close-solution');await key('Escape');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'narrow Escape');assert.equal(await evaluate(()=>document.getElementById('solution').value),combined);check('Keyboard close retains text at 320px');
 for(const [width,height] of [[320,480],[760,600]]){
  await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await evaluate(()=>document.getElementById('expand-solution').focus());await key('Enter');
  await evaluate(()=>document.getElementById('close-solution').scrollIntoView({block:'nearest'}));
  const compact=await evaluate(()=>{const d=document.getElementById('solution-dialog'),f=document.getElementById('solution'),b=document.getElementById('close-solution').getBoundingClientRect(),r=f.getBoundingClientRect();return {width:innerWidth,height:innerHeight,dialogWidth:d.getBoundingClientRect().width,scrollWidth:d.scrollWidth,clientWidth:d.clientWidth,closeTop:b.top,closeBottom:b.bottom,fieldInModal:d.contains(f),fieldTop:r.top,fieldBottom:r.bottom};});
  assert(compact.scrollWidth<=compact.clientWidth+1);assert(compact.closeTop>=0&&compact.closeBottom<=height);assert(compact.fieldInModal);assert(compact.fieldTop>=0&&compact.fieldBottom<=height);await screenshot('modal-'+width+'x'+height);await key('Escape');await until(()=>evaluate(()=>!document.getElementById('solution-dialog').open),'compact Escape');assert.equal(await evaluate(()=>document.getElementById('solution').value),combined);check('Compact modal retains text and provides an accessible close control',compact);
 }
 assert.equal(calls.filter(call=>call.action==='suggest').length,1);assert.equal(calls.filter(call=>call.action==='api-settings').length,0);
 await searchWorkflow(base);
 await socWorkflow(base);
 await blankToolsWorkflow(base);
 await aboutWorkflow(base);
 await aiToolsWorkflow(base);
 const result={browser:'Chromium headless',version:(await cdp.send('Browser.getVersion')).product,checks,external_api_calls:0,unexpected_page_requests_blocked:blocked,user_database_used:false,api_key_handling_used:false};
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(async error=>{if(cdp){await screenshot('failure').catch(()=>{});const state=await evaluate(()=>({active:document.activeElement?.id,notice:document.getElementById('notice')?.textContent,dialog:document.getElementById('solution-dialog')?.open,busy:typeof busy==='boolean'?busy:null})).catch(()=>null);fs.writeFileSync(path.join(output,'failure-state.json'),JSON.stringify(state));}fs.writeFileSync(path.join(output,'failure.txt'),error.stack);console.error(error);process.exitCode=1;}).finally(async()=>{
 if(cdp){await cdp.send('Browser.close').catch(()=>{});cdp.close();}else if(browser)browser.kill();if(server.listening)server.close();
});
