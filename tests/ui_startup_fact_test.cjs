const vm=require('node:vm'),assert=require('node:assert/strict');
module.exports=async function(html){
  function el(tag=''){return {tag,textContent:'',children:[],handlers:{},dataset:{},
    appendChild(c){this.children.push(c)},replaceChildren(){this.children=[]},
    setAttribute(){},addEventListener(k,f){this.handlers[k]=f}}}
  const els=Object.fromEntries(['ticket','mode','backend','send','status','error','out','vpn','access','unknown','connection'].map(id=>[id,el()]));
  els.mode.value='demo';els.backend.value='vector';
  const payload={mode:'demo',model_used:false,
    known_facts:[{field:'device_startup_unresolved',value:true,evidence:'Tietokone ei lähde käyntiin'}],
    result:{state:'insufficient',category:'muu',summary:'Mitä viimeisellä käynnistysyrityksellä tapahtui?',
      steps:[],source_ids:[],questions:[],needs_human:true},
    sources:[],candidates:[],search:{category:'laitteet'}};
  vm.runInNewContext(html.split('<script>')[1].split('</script>')[0],{
    document:{getElementById:id=>els[id],createElement:el},
    fetch:async url=>({ok:true,json:async()=>url==='/health'?{api_key_available:false}:payload})});
  await els.send.onclick();
  function all(n){return [n,...n.children.flatMap(all)]}
  const text=all(els.out).map(n=>n.textContent).join('\n');
  assert(text.includes('Tietokoneen käynnistymisongelma'));
  assert(text.includes('Tietokone ei lähde käyntiin'));
  assert(text.includes('käynnistysyrityksellä'));
  assert(!text.includes('Internet toimii'));
  assert(!text.includes('Internet ei toimi'));
  assert(!all(els.out).some(n=>n.tag==='ol'));
  return {startup_fact_rendering:'passed'};
};
