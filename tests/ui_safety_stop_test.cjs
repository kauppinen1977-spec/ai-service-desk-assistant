const vm = require('node:vm');
const assert = require('node:assert/strict');

module.exports = async function(html) {
  function el(tag='') { return {tag, children:[], handlers:{}, dataset:{}, textContent:'', value:'',
    appendChild(c){this.children.push(c)}, replaceChildren(){this.children=[]},
    setAttribute(k,v){this[k]=v}, addEventListener(k,v){this.handlers[k]=v}}; }
  function all(n){return [n,...n.children.flatMap(all)]}
  const warnings = ['lopeta käyttö ja ota yhteys IT-tukeen',
    'Älä hyväksy kirjautumista, jota et itse aloittanut.', 'ilmoita siitä IT-tuelle heti'];
  for (const warning of warnings) {
    const els=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
    els.mode.value='demo';els.backend.value='keyword';
    const payload={mode:'demo',model_used:false,known_facts:[],sources:[{id:'SAFE',title:'Turvallisuuslähde',version:'test'}],
      search:{backend:'keyword',category:'muu',hits:[]},
      result:{state:'safety_stop',category:'muu',summary:'Ota yhteys IT-tukeen.',
        needs_human:true,source_ids:['SAFE'],questions:[],
        steps:[{text:warning,source_id:'SAFE',source_step:2,version:'test'}]},
      // Turvallisuustila ei saa avata ehdokkaita edes ristiriitaisesta payloadista.
      candidates:[{guide_id:'UNSAFE',title:'Tavallinen tarkistus',eligible:true,
        steps:[{text:'Testaa laturia ja jatka kirjautumista.'}]}]};
    vm.runInNewContext(html.split('<script>')[1].split('</script>')[0],{
      document:{getElementById:id=>els[id],createElement:el},
      fetch:async url=>({ok:true,json:async()=>url==='/health'?{api_key_available:false}:payload})});
    await els.send.onclick();
    const nodes=all(els.out);
    assert(nodes.some(n=>n.tag==='h2'&&n.textContent==='Turvallisuuskeskeytys'));
    assert(nodes.some(n=>n.role==='alert'));
    assert(nodes.some(n=>n.tag==='li'&&n.textContent===warning));
    const customer=els.out.children[0];
    assert.equal(customer.id,'customer-result');
    assert.equal(customer.role,'alert');
    assert(all(customer).some(n=>n.tag==='li'&&n.textContent===warning));
    const diagnostics=nodes.find(n=>n.tag==='details');
    assert(diagnostics);assert(!diagnostics.open);
    assert.equal(diagnostics.children[0].tag,'summary');
    assert(!all(diagnostics).some(n=>n.tag==='ol'));
    assert(!nodes.some(n=>n.textContent.includes('Testaa laturia')));
    assert(!nodes.some(n=>n.textContent.includes('tarvittaessa')));
    assert(els.status.textContent.includes('Turvallisuuskeskeytys'));
  }
  return {safety_stop_renderings:3,passed:true};
};
