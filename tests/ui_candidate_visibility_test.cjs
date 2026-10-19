// Todellinen index.html:n tapahtuma- ja renderöintikoodi, ei verkko- tai mallikutsuja.
const vm = require('node:vm');
const assert = require('node:assert/strict');

module.exports = async function(html) {
  const script = html.split('<script>')[1].split('</script>')[0];
  function el(tag='') {
    return {tag, children:[], handlers:{}, dataset:{}, value:'', textContent:'',
      set innerHTML(_) { throw Error('Unsafe HTML rendering'); },
      appendChild(child){this.children.push(child);child.parent=this},
      replaceChildren(){this.children=[]}, setAttribute(k,v){this[k]=v},
      addEventListener(k,v){this.handlers[k]=v}};
  }
  function all(n){return [n,...n.children.flatMap(all)]}
  function setup(mode) {
    const els=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
    els.mode.value=mode;els.backend.value='keyword';els.ticket.value='Kuvitteellinen tukipyyntö';
    let respond;
    vm.runInNewContext(script,{
      document:{getElementById:id=>els[id],createElement:el},
      fetch:(url,options)=>{
        if(url==='/health')return Promise.resolve({json:async()=>({api_key_available:false})});
        assert.equal(url,'/api/answer');
        assert.equal(JSON.parse(options.body).mode,mode);
        return new Promise(resolve=>{respond=resolve});
      }});
    return {els,reply:p=>respond({ok:true,json:async()=>p})};
  }
  function payload(mode,state) {
    const selected=state==='suggestion'||state==='safety_stop';
    return {mode,model_used:mode==='live'&&state==='suggestion',known_facts:[],
      result:{state,category:'verkko',summary:'Kuvitteellinen tilanne.',needs_human:true,
        source_ids:selected?['CHOSEN']:[],questions:[],
        steps:selected?[{text:state==='safety_stop'?'TURVALLISUUS_ENSIN':'VALITTU_HYVAKSYNTAEHTO',source_id:'CHOSEN',source_step:2,version:'V1'}]:[]},
      sources:selected?[{id:'CHOSEN',title:'Valitun lähteen nimi',version:'V1'}]:[],
      search:{category:'verkko'},
      candidates:[
        {guide_id:'REJECTED',title:'Hylätty lähde',version:'V2',score:.91,chunk_id:'REJECTED:1',eligible:false,exclusion_reason:'Ristiriita vahvistetun tiedon kanssa.',
          excerpt:'KATKELMAN_TOIMINTAKASKY',steps:[{text:'HYLATTY_TOIMINTAVAIHE'}]},
        {guide_id:'UNSELECTED',title:'Valitsematon lähde',version:'V3',score:.87,chunk_id:'UNSELECTED:2',eligible:true,exclusion_reason:'',
          steps:[{text:'VALITSEMATON_TOIMINTAVAIHE'}]},
        {guide_id:'CHOSEN',title:'Valitun lähteen nimi',version:'V1',score:.84,chunk_id:'CHOSEN:1',eligible:true,exclusion_reason:'',
          steps:[{text:'VALITUN_LAHTEEN_TARPEETON_ALKUPERAINEN_VAIHE'}]}
      ]};
  }
  const results=[];
  async function test(name,fn) {
    try{await fn();results.push({name,passed:true})}
    catch(e){results.push({name,passed:false,error:e.message})}
  }
  async function render(mode,state,change) {
    const h=setup(mode),p=payload(mode,state);if(change)change(p);
    const pending=h.els.send.onclick();h.reply(p);await pending;
    assert.equal(h.els.error.children.length,0);
    return {h,p,nodes:all(h.els.out)};
  }
  for(const mode of ['demo','live']) {
    for(const state of ['candidates','ambiguous','insufficient','needs_details']) {
      await test(mode+'/'+state+': ei ehdokkaiden vaiheita, diagnostiikka säilyy',async()=>{
        const {nodes}=await render(mode,state,p=>{
          p.result.questions=[{id:'q',text:'TARKENTAVA_KYSYMYS',source_id:'CHOSEN'}];
        });
        const texts=nodes.map(n=>n.textContent).join('\n');
        for(const forbidden of ['HYLATTY_TOIMINTAVAIHE','VALITSEMATON_TOIMINTAVAIHE',
          'VALITUN_LAHTEEN_TARPEETON_ALKUPERAINEN_VAIHE','KATKELMAN_TOIMINTAKASKY',
          'Näytä alkuperäinen ohje'])assert(!texts.includes(forbidden),forbidden);
        assert(!nodes.some(n=>n.tag==='ol'));
        for(const metadata of ['REJECTED','UNSELECTED','CHOSEN','V2','V3','.91','.87','REJECTED:1','UNSELECTED:2',
          'Ristiriita vahvistetun tiedon kanssa.','TARKENTAVA_KYSYMYS'])assert(texts.includes(metadata),metadata);
        assert(texts.includes('ei toimintaohjeita'));
        assert(texts.includes('Ei hyväksytä vastauksen lähteeksi'));
      });
    }
    await test(mode+'/safety_stop: vain kiireelliset ensiohjeet',async()=>{
      const {nodes,h}=await render(mode,'safety_stop');
      const texts=nodes.map(n=>n.textContent).join('\n');
      assert(nodes.some(n=>n.role==='alert'));
      assert(nodes.some(n=>n.tag==='li'&&n.textContent==='TURVALLISUUS_ENSIN'));
      assert(!texts.includes('tarvittaessa'));
      assert(!texts.includes('REJECTED'));
      assert(!texts.includes('TOIMINTAVAIHE'));
      assert(texts.includes('Ota yhteys IT-tukeen'));
      assert(h.els.status.textContent.includes('Turvallisuuskeskeytys'));
    });
  }
  await test('live/suggestion: vain valitut lähteistetyt vaiheet',async()=>{
    const {nodes}=await render('live','suggestion',p=>{
      p.result.steps.push({text:'VAARA_LAHDE_TULOKSESSA',source_id:'UNSELECTED',source_step:1,version:'V3'});
    });
    const texts=nodes.map(n=>n.textContent).join('\n');
    assert(nodes.some(n=>n.tag==='li'&&n.textContent==='VALITTU_HYVAKSYNTAEHTO'));
    assert(nodes.some(n=>n.href==='#source-CHOSEN'));
    assert(!texts.includes('VAARA_LAHDE_TULOKSESSA'));
    assert(!texts.includes('TOIMINTAVAIHE'));
    assert(!texts.includes('TARPEETON_ALKUPERAINEN_VAIHE'));
  });
  await test('muut tilat eivät renderöi virheellisen payloadin ratkaisuvaiheita',async()=>{
    for(const state of ['candidates','ambiguous','insufficient','needs_details','tuntematon']) {
      const {nodes}=await render('live',state,p=>{
        p.result.steps=[{text:'EI_SAA_NAKYA',source_id:'CHOSEN',source_step:1,version:'V1'}];
        p.result.source_ids=['CHOSEN'];p.sources=[{id:'CHOSEN',title:'Nimi',version:'V1'}];
      });
      assert(!nodes.some(n=>n.textContent==='EI_SAA_NAKYA'),state);
    }
  });
  await test('demo ei näytä suggestion-vaiheita virheellisestä payloadista',async()=>{
    const {nodes}=await render('demo','suggestion');
    assert(!nodes.some(n=>n.textContent==='VALITTU_HYVAKSYNTAEHTO'));
  });
  for(const [id,event] of [['ticket','input'],['mode','change'],['backend','change']]) {
    await test(id+': vanha vastaus tyhjenee ja myöhäinen sivuutetaan',async()=>{
      const {h}=await render('live','suggestion');
      assert(h.els.out.children.length>0);
      const pending=h.els.send.onclick();h.els[id].handlers[event]();
      assert.equal(h.els.out.children.length,0);
      h.reply(payload('live','suggestion'));await pending;
      assert.equal(h.els.out.children.length,0);
    });
  }
  await test('varahaku erotetaan vektoripisteistä ilman ehdokkaiden ohjeita',async()=>{
    const {nodes}=await render('demo','candidates',p=>{
      p.candidates=[{...p.candidates[1],score:null,chunk_id:null,retrieval_method:'lexical_fallback'}];
    });
    const texts=nodes.map(n=>n.textContent).join('\n');
    assert(texts.includes('Leksikaalinen varahaku'));
    assert(!texts.includes('pisteet null'));
    assert(!texts.includes('TOIMINTAVAIHE'));
  });
  return {tests:results.length,passed:results.filter(r=>r.passed).length,
    failed:results.filter(r=>!r.passed).length,results};
};

if(require.main===module){
  const fs=require('node:fs');
  module.exports(fs.readFileSync('index.html','utf8')).then(r=>{
    console.log(JSON.stringify(r,null,2));process.exitCode=r.failed?1:0;
  }).catch(e=>{console.error(e);process.exitCode=1});
}
