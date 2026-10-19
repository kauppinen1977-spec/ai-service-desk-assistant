const vm=require('node:vm'),assert=require('node:assert/strict');
module.exports=async function(html){
  assert.equal(html.match(/<textarea\b[^>]*id="ticket"[^>]*>([\s\S]*?)<\/textarea>/)[1],'');
  function el(){return {children:[],handlers:{},dataset:{},value:'',textContent:'',
    appendChild(c){this.children.push(c)},replaceChildren(){this.children=[]},
    addEventListener(k,f){this.handlers[k]=f},setAttribute(){}}}
  function setup(){
    const e=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
    e.mode.value='demo';e.backend.value='keyword';let resolve,reject;
    vm.runInNewContext(html.split('<script>')[1].split('</script>')[0],{
      document:{getElementById:id=>e[id],createElement:el},
      fetch:(url)=>url==='/health'?Promise.resolve({json:async()=>({api_key_available:false})}):
        new Promise((yes,no)=>{resolve=yes;reject=no})});
    return {e,reply:r=>resolve(r),fail:()=>reject(Error('Test connection failure'))};
  }
  const payload={mode:'demo',model_used:false,known_facts:[],sources:[],candidates:[],search:{category:'muu'},
    result:{state:'insufficient',summary:'TEST_RESPONSE',steps:[],source_ids:[],questions:[],needs_human:true}};
  for(const state of ['candidates','ambiguous','insufficient','needs_details','suggestion','safety_stop']){
    const h=setup();h.e.ticket.value='Käsiteltävä tiketti';
    const p=h.e.send.onclick();h.reply({ok:true,json:async()=>({...payload,result:{...payload.result,state}})});await p;
    assert.equal(h.e.ticket.value,'',state);
    assert(h.e.out.children.length>0,state);
    assert.equal(h.e.error.children.length,0,state);
    function all(n){return [n,...n.children.flatMap(all)]}
    assert(all(h.e.out).some(n=>n.textContent==='Käsitelty tiketti: Käsiteltävä tiketti'),state);
  }
  const edit=setup();edit.e.ticket.value='Täydennettävä alkuperäinen tiketti';
  const editPending=edit.e.send.onclick();edit.reply({ok:true,json:async()=>payload});await editPending;
  function all(n){return [n,...n.children.flatMap(all)]}
  const button=all(edit.e.out).find(n=>n.textContent==='Täydennä tätä pyyntöä');
  assert(button);button.onclick();
  assert.equal(edit.e.ticket.value,'Täydennettävä alkuperäinen tiketti');
  for(const failure of ['http','network','json','render']){
    const h=setup();h.e.ticket.value='Säilytettävä tiketti';const p=h.e.send.onclick();
    if(failure==='network')h.fail();
    else if(failure==='json')h.reply({ok:true,json:async()=>{throw Error('Malformed JSON')}});
    else h.reply({ok:failure!=='http',json:async()=>failure==='http'?{error:'Test error'}:{}});
    await p;assert.equal(h.e.ticket.value,'Säilytettävä tiketti',failure);
    assert(h.e.error.children.length>0,failure);
  }
  const h=setup();h.e.ticket.value='Ensimmäinen tiketti';const p=h.e.send.onclick();
  h.e.ticket.value='Uusi keskeneräinen tiketti';h.e.ticket.handlers.input();
  h.reply({ok:true,json:async()=>payload});await p;
  assert.equal(h.e.ticket.value,'Uusi keskeneräinen tiketti');assert.equal(h.e.out.children.length,0);
  return {initial_empty:true,success_states:6,error_paths:4,stale_response_preserved:true};
};
if(require.main===module){module.exports(require('node:fs').readFileSync('index.html','utf8'))
 .then(r=>console.log(r)).catch(e=>{console.error(e);process.exitCode=1});}
