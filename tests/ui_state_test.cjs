// Node.js DOM-korvike: syötteen muutokset, virhe ja myöhäisen vastauksen sivuutus.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const elements={};
function el(){return {value:'',textContent:'',children:[],dataset:{},handlers:{},setAttribute(){},appendChild(e){this.children.push(e)},replaceChildren(){this.children=[]},addEventListener(k,f){this.handlers[k]=f}};}
for(const id of ['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'])elements[id]=el();
elements.mode.value='demo';elements.backend.value='keyword';
const script=fs.readFileSync('index.html','utf8').split('<script>')[1].split('</script>')[0];
let resolveFetch;
const context={document:{getElementById:id=>elements[id],createElement:el},fetch:url=>url==='/health'?Promise.resolve({json:async()=>({api_key_available:false})}):new Promise(resolve=>resolveFetch=resolve)};
vm.runInNewContext(script,context);
(async()=>{
 elements.out.children=[{}];elements.vpn.onclick();assert.equal(elements.out.children.length,0);
 elements.out.children=[{}];elements.ticket.handlers.input();assert.equal(elements.out.children.length,0);
 elements.out.children=[{}];elements.mode.handlers.change();assert.equal(elements.out.children.length,0);
 let pending=elements.send.onclick();elements.unknown.onclick();resolveFetch({ok:true,json:async()=>({})});await pending;
 assert.equal(elements.out.children.length,0);assert(elements.status.textContent.includes('muuttui'));assert.equal(elements.send.disabled,false);
 pending=elements.send.onclick();resolveFetch({ok:false,json:async()=>({error:'API-avain ei kelpaa.',code:'invalid_api_key',help:'Aseta avain uudelleen.'})});await pending;
 assert.equal(elements.status.dataset.state,'error');assert(elements.error.children.some(e=>e.textContent.includes('API-avain')));
 const fixture=JSON.parse(fs.readFileSync('tests/fixtures/v03_vpn_response.json','utf8'));
 pending=elements.send.onclick();resolveFetch({ok:true,json:async()=>fixture});await pending;
 function all(e){return [e,...e.children.flatMap(all)]}
 const nodes=all(elements.out);
 assert(nodes.some(e=>e.textContent.includes('Ratkaisuehdotus')));
 assert(nodes.some(e=>e.textContent.includes('VPN-001 · alkuperäinen vaihe 2')));
 assert(!nodes.some(e=>e.textContent.includes('VPN-001 · alkuperäinen vaihe 1')));
 assert(nodes.some(e=>e.href==='#source-VPN-001'));
 assert(nodes.some(e=>e.textContent.includes('Ei hyväksytä vastauksen lähteeksi')));
 assert(!nodes.some(e=>e.textContent==='Toimiiko tavallinen internetyhteys ilman VPN-yhteyttä?'));
 console.log('UI state/render tests passed: stale output, error, cited steps, excluded candidate and known facts.');
})().catch(e=>{console.error(e);process.exitCode=1});
