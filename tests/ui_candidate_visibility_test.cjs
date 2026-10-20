// Todellinen index.html:n tapahtuma- ja renderöintikoodi, ei verkko- tai mallikutsuja.
const vm = require('node:vm');
const assert = require('node:assert/strict');

module.exports = async function(html) {
  const script = html.split('<script>')[1].split('</script>')[0];
  function el(tag='') {
    return {tag, children:[], handlers:{}, dataset:{}, attributes:{}, open:false, value:'', textContent:'',
      set innerHTML(_) { throw Error('Unsafe HTML rendering'); },
      appendChild(child){this.children.push(child);child.parent=this},
      replaceChildren(){this.children=[]}, setAttribute(k,v){this.attributes[k]=v;this[k]=v},
      addEventListener(k,v){this.handlers[k]=v},
      // DOM-korvike mallintaa summary-elementin natiivin avaus-/sulkutoiminnon.
      // Näppäimistökäyttö on tarkistettava lisäksi oikeassa selaimessa.
      click(){if(this.tag==='summary'&&this.parent.tag==='details')this.parent.open=!this.parent.open}};
  }
  function all(n){return [n,...n.children.flatMap(all)]}
  function visible(n){
    if(n.tag==='details'&&!n.open)return [n,...n.children.filter(c=>c.tag==='summary').flatMap(visible)];
    return [n,...n.children.flatMap(visible)];
  }
  const texts=nodes=>nodes.map(n=>n.textContent).join('\n');
  function setup(mode) {
    const els=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
    els.mode.value=mode;els.backend.value='keyword';els.ticket.value='Kuvitteellinen tukipyyntö';
    let respond,calls=0;
    vm.runInNewContext(script,{
      document:{getElementById:id=>els[id],createElement:el},
      fetch:(url,options)=>{
        if(url==='/health')return Promise.resolve({json:async()=>({api_key_available:false})});
        calls++;
        assert.equal(url,'/api/answer');
        assert.equal(JSON.parse(options.body).mode,mode);
        return new Promise(resolve=>{respond=resolve});
      }});
    return {els,reply:p=>respond({ok:true,json:async()=>p}),calls:()=>calls};
  }
  function payload(mode,state) {
    const selected=state==='suggestion'||state==='safety_stop';
    return {mode,model_used:mode==='live'&&state==='suggestion',known_facts:[],
      result:{state,category:'verkko',summary:'Kuvitteellinen tilanne.',needs_human:true,
        source_ids:selected?['CHOSEN']:[],questions:[],
        steps:selected?[{text:state==='safety_stop'?'TURVALLISUUS_ENSIN':'VALITTU_HYVAKSYNTAEHTO',source_id:'CHOSEN',source_step:2,version:'V1'}]:[]},
      sources:selected?[{id:'CHOSEN',title:'Valitun lähteen nimi',version:'V1'}]:[],
      search:{category:'verkko',backend:'keyword'},
      candidates:[
        {guide_id:'REJECTED',title:'Hylätty lähde',version:'V2',score:.91,chunk_id:'REJECTED:1',eligible:false,exclusion_reason:'Ristiriita vahvistetun tiedon kanssa.',
          excerpt:'KATKELMAN_TOIMINTAKASKY',steps:[{text:'HYLATTY_TOIMINTAVAIHE'}]},
        {guide_id:'UNSELECTED',title:'Valitsematon lähde',version:'V3',score:.87,chunk_id:'UNSELECTED:2',eligible:true,exclusion_reason:'',
          eligibility_evidence:[{field:'problem_scope',value:'remote_access',evidence:'SOVELTUVUUDEN_TEKSTINAYTTO'}],
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
  const appQuestions=[
    {id:'clarification:work_service',text:'Mikä työpalvelu tai ohjelma ei avaudu, ja mikä tarkka virheilmoitus näkyy?',source_id:''},
    {id:'clarification:internet_vpn',text:'Avautuvatko tavalliset verkkosivut samalla laitteella ilman VPN-yhteyttä, ja mitä etäyhteyden virheilmoituksessa lukee?',source_id:''},
    {id:'clarification:storage_mail',text:'Missä ohjelmassa kumpikin tilailmoitus näkyy, ja mitä ilmoituksissa tarkalleen lukee?',source_id:''}
  ];
  for(const state of ['insufficient','ambiguous','candidates']) {
    for(const question of appQuestions) {
      await test(state+'/'+question.id+': lähteetön havaintokysymys näkyy asiakkaalle',async()=>{
        for(const backend of ['keyword','vector']) {
          const h=setup('demo'),p=payload('demo',state);h.els.backend.value=backend;
          p.search.backend=backend;p.result.questions=[question];
          const pending=h.els.send.onclick();h.reply(p);await pending;
          assert.equal(h.els.error.children.length,0);
          const customer=h.els.out.children[0],diagnostics=h.els.out.children.find(n=>n.tag==='details');
          assert(visible(customer).some(n=>n.tag==='li'&&n.textContent===question.text));
          assert(visible(customer).some(n=>n.tag==='h3'&&n.textContent==='Tarkentavat kysymykset'));
          assert(!all(customer).some(n=>n.tag==='ol'||n.tag==='a'));
          assert(!all(diagnostics).some(n=>n.textContent===question.text));
          assert.equal(diagnostics.open,false);
          assert(!Object.hasOwn(diagnostics.attributes,'open'));
          assert(!texts(visible(h.els.out)).includes('REJECTED:1'));
        }
      });
    }
  }
  for(const [mode,state] of [['live','suggestion'],['demo','candidates'],['live','insufficient'],['demo','safety_stop']]) {
    await test(mode+'/'+state+': asiakasnäkymä näkyy ja diagnostiikka on oletuksena suljettu',async()=>{
      const {h}=await render(mode,state,p=>{
        p.known_facts=[{field:'internet_working',value:true,evidence:'HAVAINNON_TEKSTINAYTTO'}];
      });
      const customer=h.els.out.children[0],diagnostics=h.els.out.children.find(n=>n.tag==='details');
      assert.equal(customer.tag,'section');assert.equal(customer.id,'customer-result');
      assert.equal(customer.attributes['aria-labelledby'],'result-title');
      assert(all(customer).some(n=>n.tag==='h2'&&n.id==='result-title'));
      assert(diagnostics);assert.equal(diagnostics.open,false);
      assert(!Object.hasOwn(diagnostics.attributes,'open'));
      assert.equal(diagnostics.children[0].tag,'summary');
      assert.equal(diagnostics.children[0].children[0].tag,'h2');
      assert.equal(diagnostics.children[0].children[0].textContent,'IT-asiantuntijan diagnostiikka');
      const shown=texts(visible(h.els.out)),hidden=texts(all(diagnostics));
      assert(shown.includes('Kuvitteellinen tilanne.'));
      for(const value of ['Käsittelytila:','Hakutapa:','mallin käyttö:','HAVAINNON_TEKSTINAYTTO',
        'Soveltuvuusnäyttö:','REJECTED:1','pisteet 0.91','Ei hyväksytä vastauksen lähteeksi'])assert(!shown.includes(value),value);
      for(const value of ['Käsittelytila:','Hakutapa: Sanahaku','mallin käyttö:',
        'HAVAINNON_TEKSTINAYTTO','rajattuun tekstisääntöön'])assert(hidden.includes(value),value);
      assert(hidden.includes('vastauksen tila: '+state));
      assert(hidden.includes(mode==='live'?'OpenAI (live)':'Vain haku (demo)'));
      assert(hidden.includes(state==='suggestion'?'OpenAI-kutsu tehty':'OpenAI-kutsua ei tehty'));
      if(state==='safety_stop') {
        assert.equal(customer.role,'alert');assert(shown.includes('TURVALLISUUS_ENSIN'));
        assert(!hidden.includes('REJECTED'));assert(hidden.includes('Haku ohitettiin'));
      } else {
        for(const value of ['REJECTED:1','pisteet 0.91','Ei hyväksytä vastauksen lähteeksi',
          'SOVELTUVUUDEN_TEKSTINAYTTO'])assert(hidden.includes(value),value);
      }
      if(state==='suggestion') {
        assert(shown.includes('VALITTU_HYVAKSYNTAEHTO'));
        assert(visible(customer).some(n=>n.href==='#source-CHOSEN'));
        assert(visible(customer).some(n=>n.id==='source-CHOSEN'));
      } else if(state!=='safety_stop') assert(!visible(customer).some(n=>n.tag==='ol'));
    });
  }
  await test('diagnostiikan avaaminen ja sulkeminen ei muuta vastausta eikä lähetä pyyntöä',async()=>{
    const {h}=await render('demo','candidates');
    const customer=h.els.out.children[0],before=texts(all(customer)),calls=h.calls();
    const diagnostics=h.els.out.children.find(n=>n.tag==='details'),summary=diagnostics.children[0];
    summary.click();assert.equal(diagnostics.open,true);
    const shown=texts(visible(h.els.out));
    assert(shown.includes('REJECTED:1'));assert(shown.includes('SOVELTUVUUDEN_TEKSTINAYTTO'));
    assert(!shown.includes('TOIMINTAVAIHE'));assert(!shown.includes('KATKELMAN_TOIMINTAKASKY'));
    assert.equal(h.els.out.children[0],customer);assert.equal(texts(all(customer)),before);
    assert.equal(h.calls(),calls);
    summary.click();assert.equal(diagnostics.open,false);
    assert(!texts(visible(h.els.out)).includes('REJECTED:1'));
    assert.equal(h.calls(),calls);
  });
  await test('uusi vastaus sulkee edellisen vastauksen avatun diagnostiikan',async()=>{
    const {h}=await render('demo','candidates');
    const old=h.els.out.children.find(n=>n.tag==='details');old.children[0].click();
    assert(old.open);
    const pending=h.els.send.onclick();h.reply(payload('demo','insufficient'));await pending;
    const current=h.els.out.children.find(n=>n.tag==='details');
    assert.notEqual(current,old);assert.equal(current.open,false);
    assert(texts(visible(h.els.out)).includes('Ohjeaineisto ei riitä'));
  });
  await test('ratkaisuvaiheiden järjestys, alkuperäiset numerot ja lähteet säilyvät',async()=>{
    const steps=[
      {text:'ALKUPERAINEN_VAIHE_KAKSI',source_id:'CHOSEN',source_step:2,version:'V1'},
      {text:'ALKUPERAINEN_VAIHE_NELJA',source_id:'CHOSEN',source_step:4,version:'V1'}];
    const {h}=await render('live','suggestion',p=>{p.result.steps=steps});
    const list=all(h.els.out.children[0]).find(n=>n.tag==='ol');
    assert.deepEqual(list.children.map(n=>n.textContent),steps.map(s=>s.text));
    for(let i=0;i<steps.length;i++) {
      const link=list.children[i].children[0];
      assert(link.textContent.includes('alkuperäinen vaihe '+steps[i].source_step));
      assert(link.textContent.includes('V1'));assert.equal(link.href,'#source-CHOSEN');
    }
  });
  for(const mode of ['demo','live']) {
    for(const state of ['candidates','ambiguous','insufficient','needs_details']) {
      await test(mode+'/'+state+': ei ehdokkaiden vaiheita, diagnostiikka säilyy',async()=>{
        const {nodes,h}=await render(mode,state,p=>{
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
        const customer=all(h.els.out.children[0]);
        assert(customer.some(n=>n.textContent==='TARKENTAVA_KYSYMYS'));
        assert(!customer.some(n=>n.textContent.includes('REJECTED')));
        if(['insufficient','ambiguous'].includes(state))
          assert(customer.some(n=>n.textContent.includes('siirrä pyyntö IT-tuen käsiteltäväksi')));
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
      h.els.out.children.find(n=>n.tag==='details').children[0].click();
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
