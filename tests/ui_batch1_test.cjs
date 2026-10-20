const vm=require('node:vm'),assert=require('node:assert/strict');
module.exports=async function(records,html){
  assert.equal(records.length,96);
  function el(tag=''){return {tag,children:[],handlers:{},dataset:{},textContent:'',value:'',open:false,
    set innerHTML(_){throw Error('Unsafe HTML rendering')},
    appendChild(c){this.children.push(c);c.parent=this},replaceChildren(){this.children=[]},
    addEventListener(k,f){this.handlers[k]=f},setAttribute(k,v){this[k]=v}}}
  function all(n){return [n,...n.children.flatMap(all)]}
  for(const {id,ticket,response} of records){
    const els=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
    els.ticket.value=ticket;els.mode.value=response.mode;els.backend.value='vector';
    vm.runInNewContext(html.split('<script>')[1].split('</script>')[0],{
      document:{getElementById:id=>els[id],createElement:el},
      fetch:async url=>({ok:true,json:async()=>url==='/health'?{api_key_available:false,corpus:'batch1'}:response})});
    await els.send.onclick();
    const nodes=all(els.out),state=response.result.state;
    assert.equal(els.error.children.length,0,id);
    assert.equal(els.ticket.value,'',id);
    assert(nodes.length>1,id);
    const customer=els.out.children[0],customerNodes=all(customer);
    assert.equal(customer.id,'customer-result',id);
    const diagnostics=nodes.find(n=>n.tag==='details'&&n.id==='diagnostics');
    assert(diagnostics,id);assert.equal(diagnostics.open,false,id);
    assert.equal(diagnostics.children[0].tag,'summary',id);
    assert(all(diagnostics.children[0]).some(n=>n.textContent==='IT-asiantuntijan diagnostiikka'),id);
    const diagnosticNodes=all(diagnostics);
    const mode=response.mode==='live'?'OpenAI (live)':'Vain haku (demo)';
    assert(diagnosticNodes.some(n=>n.textContent==='Käsittelytila: '+mode+' | vastauksen tila: '+state),id);
    const backend={keyword:'Sanahaku',vector:'Vektorihaku'}[response.search.backend];
    assert(backend,id);
    const model=response.model_used?'OpenAI-kutsu tehty':'OpenAI-kutsua ei tehty';
    assert(diagnosticNodes.some(n=>n.textContent==='Hakutapa: '+backend+' | mallin käyttö: '+model),id);
    assert(!customerNodes.some(n=>n.textContent.includes('mallin käyttö:')),id);
    for(const candidate of nodes.filter(n=>n.className==='candidate'||n.className==='candidate excluded')){
      assert(diagnosticNodes.includes(candidate),id);
      assert(!all(candidate).some(n=>n.tag==='li'||n.tag==='ol'||n.tag==='details'),id);
    }
    if(state==='safety_stop'){
      assert.equal(customer.role,'alert',id);
      assert(!nodes.some(n=>n.textContent==='Haun ehdokkaat — ei toimintaohjeita'),id);
      assert(!nodes.some(n=>n.textContent.includes('tarvittaessa')),id);
    }
    const numbered=customerNodes.filter(n=>n.tag==='li'&&response.result.steps.some(s=>s.text===n.textContent));
    assert.equal(numbered.length,response.result.steps.length,id);
    assert.deepEqual(numbered.map(n=>n.textContent),response.result.steps.map(s=>s.text),id);
    for(let i=0;i<numbered.length;i++){
      const step=response.result.steps[i],link=numbered[i].children.find(n=>n.tag==='a');
      assert(link,id);assert.equal(link.href,'#source-'+step.source_id,id);
      assert(link.textContent.includes('alkuperäinen vaihe '+step.source_step+' · '+step.version),id);
    }
    for(const source of response.sources){assert(customerNodes.some(n=>n.id==='source-'+source.id),id)}
    for(const question of response.result.questions){assert(customerNodes.some(n=>n.textContent===question.text),id)}
    if(state==='insufficient')assert(customerNodes.some(n=>n.textContent===response.result.summary),id);
  }
  return {case_cards:48,demo_and_mock_live_renderings:records.length,passed:true,
    real_language_model_used:false,browser_visual_review:'not_performed'};
};
