// Real Chromium test with a synthetic localhost server; no user DB or external API.
// node tests/ui_memory_browser_test.cjs [--live] [path-to-chrome-or-edge.exe]
// --live checks the real server at port 8502; all POST requests are blocked.
// --live-search loads that same server's HTML and fulfills POSTs with fixtures in CDP.
// Run the live modes sequentially: the application uses a single-threaded HTTPServer.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const liveSearch=process.argv.includes('--live-search');
const live=process.argv.includes('--live')||liveSearch;
const executable=process.argv.slice(2).find(arg=>!arg.startsWith('--'))||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const output=path.resolve(liveSearch?'data/search-suggestion/browser-live':live?'data/ui-readability/live-server/browser':'data/ui-readability/browser');fs.mkdirSync(output,{recursive:true});
const profile=fs.mkdtempSync(path.join(output,'profile-'));
const html=fs.readFileSync('memory.html','utf8').replaceAll('__TOKEN__','browser-fixture-token');
const legacyText='Alkuperäinen pitkä ratkaisurivi.\n'.repeat(180)+'LOPPU – sisältö säilyy kokonaan.';
const fixture={id:'SOL-browser',title:'Vanha ratkaisu',problem:'Kuvitteellinen ongelma.',environment:'Harjoitusympäristö.',solution:legacyText,status:'verified',revision:1,updated_at:'2026-10-24T10:00:00Z'};
const proposal={title:'Kuvitteellinen <img src=x onerror="window.proposalExecuted=true">',
 solution:'1. Tarkista harjoitussivun zoomaus.\n2. Palauta näkymä normaaliksi.\n<script>window.proposalExecuted=true</script>',
 limitations:'Ei testattu.\nPuuttuva tieto: selaimen versio.\n<a href="javascript:alert(1)">Näytä tämä tekstinä.</a>'};
let records=[{...fixture}],browser,cdp,blocked=0;const calls=[],checks=[],confirmations=[],liveRequests=[],pageErrors=[];
let suggestFault=null,holdSuggest=false,releaseSuggest=null;
async function mockedAction(action,body){
 calls.push({action,body});
 if(action==='api-status')return {configured:false,source:'none',model:'gpt-4.1-mini',persistence:'process_memory',last_result:'not_tested'};
 if(action==='list')return {records};
 if(action==='search')return {state:'empty',hits:[],compatible_hits:[],review_hits:[]};
 if(action==='suggest'){if(holdSuggest)await new Promise(resolve=>{releaseSuggest=resolve;});if(suggestFault)return {error:'Korvattu API-virhe',code:suggestFault,help:'Tarkista kuvitteellinen API-asetus.'};return {state:'unverified',suggestion:proposal};}
 if(action==='save'){const old=records.find(row=>row.id===body.id);const record={...fixture,...body,id:old?.id||'SOL-browser-new',revision:(old?.revision||0)+1,status:'draft'};records=records.filter(row=>row.id!==record.id);records.push(record);return {record};}
 throw Error('Unexpected mocked action: '+action);
}
const server=http.createServer(async(req,res)=>{
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

(async()=>{
 if(!live)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base=live?'http://127.0.0.1:8502':'http://127.0.0.1:'+server.address().port;
 browser=spawn(executable,['--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--disable-extensions','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,'--window-size=1280,900','about:blank'],{windowsHide:true,stdio:'ignore'});
 browser.on('error',error=>{throw error;});
 const portFile=path.join(profile,'DevToolsActivePort');await until(()=>fs.existsSync(portFile),'Chromium DevTools');const port=fs.readFileSync(portFile,'utf8').split('\n')[0];
 const target=await(await fetch('http://127.0.0.1:'+port+'/json/new?about:blank',{method:'PUT'})).json();cdp=await connect(target.webSocketDebuggerUrl);
 await cdp.send('Page.enable');await cdp.send('Runtime.enable');
 cdp.on('Runtime.exceptionThrown',event=>pageErrors.push(event.exceptionDetails.text));
 cdp.on('Page.javascriptDialogOpening',()=>cdp.send('Page.handleJavaScriptDialog',{accept:confirmations.length?confirmations.shift():true}));
 cdp.on('Fetch.requestPaused',async event=>{const action=event.request.url.startsWith(base+'/api/memory/')?event.request.url.split('/').pop():'';if(liveSearch&&event.request.method==='POST'&&['search','suggest','api-status'].includes(action)){liveRequests.push({url:event.request.url,method:'POST',mocked:true,allowed:false});const result=await mockedAction(action,JSON.parse(event.request.postData));return cdp.send('Fetch.fulfillRequest',{requestId:event.requestId,responseCode:result.error?502:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(result)).toString('base64')});}const local=live?event.request.url===base+'/memory'&&event.request.method==='GET':event.request.url.startsWith(base+'/');if(live)liveRequests.push({url:event.request.url,method:event.request.method,allowed:local});if(!local)blocked++;return cdp.send(local?'Fetch.continueRequest':'Fetch.failRequest',{requestId:event.requestId,...(local?{}:{errorReason:'BlockedByClient'})});});
 await cdp.send('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
 await cdp.send('Page.navigate',{url:base+'/memory'});await loaded();
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
 const result={browser:'Chromium headless',version:(await cdp.send('Browser.getVersion')).product,checks,external_api_calls:0,unexpected_page_requests_blocked:blocked,user_database_used:false,api_key_handling_used:false};
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(async error=>{if(cdp){await screenshot('failure').catch(()=>{});const state=await evaluate(()=>({active:document.activeElement?.id,notice:document.getElementById('notice')?.textContent,dialog:document.getElementById('solution-dialog')?.open,busy:typeof busy==='boolean'?busy:null})).catch(()=>null);fs.writeFileSync(path.join(output,'failure-state.json'),JSON.stringify(state));}fs.writeFileSync(path.join(output,'failure.txt'),error.stack);console.error(error);process.exitCode=1;}).finally(async()=>{
 if(cdp){await cdp.send('Browser.close').catch(()=>{});cdp.close();}else if(browser)browser.kill();if(server.listening)server.close();
});
