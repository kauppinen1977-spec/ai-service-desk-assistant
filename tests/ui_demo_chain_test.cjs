// Tuotannon index.html:n JavaScript, rajattu DOM-korvike ja aidot demo-payloadit.
// Ei selainmoottori, verkkoa eikä mallia. Turvallisuuspuutteet raportoidaan
// policy_checks-taulukossa: rakennetestin onnistuminen EI hyväksy niitä.
const vm = require('node:vm');
const assert = require('node:assert/strict');

module.exports = async function testDemoUI(report, html) {
  assert.equal(report.cases.length, 12);
  const script = html.split('<script>')[1].split('</script>')[0];
  function element(tag = '') {
    return {
      tag, value: '', textContent: '', children: [], dataset: {}, handlers: {}, open: false,
      set innerHTML(_) { throw Error('Unsafe HTML rendering'); },
      setAttribute(key, value) { this[key] = value; },
      appendChild(child) { this.children.push(child); child.parent = this; },
      replaceChildren() { this.children = []; },
      addEventListener(name, fn) { this.handlers[name] = fn; }
    };
  }
  function tree(node) { return [node, ...node.children.flatMap(tree)]; }
  function insideDetails(node) {
    for (let p = node.parent; p; p = p.parent) if (p.tag === 'details') return true;
    return false;
  }
  function setup() {
    const els = Object.fromEntries(['ticket', 'mode', 'backend', 'send', 'status',
      'error', 'out', 'vpn', 'access', 'unknown', 'connection'].map(id => [id, element()]));
    els.mode.value = 'demo'; els.backend.value = 'keyword';
    let reply;
    const context = {
      document: { getElementById: id => els[id], createElement: tag => element(tag) },
      fetch: (url, options) => {
        if (url === '/health') return Promise.resolve({ json: async () => ({api_key_available:false}) });
        assert.equal(url, '/api/answer');
        assert.equal(JSON.parse(options.body).mode, 'demo');
        return new Promise(resolve => { reply = resolve; });
      }
    };
    vm.runInNewContext(script, context);
    return { els, context, respond: value => reply(value) };
  }
  const headings = {safety_stop:'Turvallisuuskeskeytys',candidates:'Hakuehdokkaat — ratkaisua ei ole valittu',
    ambiguous:'Hakutulos on monitulkintainen', insufficient:'Ohjeaineisto ei riitä'};
  const policy_checks = [];
  function policy(id, requirement, ok, severity, evidence) {
    policy_checks.push({id, requirement, passed:!!ok, severity, evidence});
  }
  let rendered = 0;
  for (const {card, controlled, keyword} of report.cases) {
    for (const [kind, payload] of [['controlled', controlled], ['keyword', keyword]]) {
      const h = setup();
      h.els.ticket.value = card.ticket;
      h.els.backend.value = payload.search.backend;
      const pending = h.els.send.onclick();
      h.respond({ok:true, json:async () => payload}); await pending;
      const nodes = tree(h.els.out);
      assert.equal(h.els.error.children.length, 0, card.id+'/'+kind);
      assert.equal(payload.mode, 'demo');
      assert.equal(payload.model_used, false, 'Demo ei saa käyttää OpenAI-mallia');
      const customer = h.els.out.children[0];
      assert.equal(customer.id, 'customer-result');
      assert(!insideDetails(customer));
      assert(tree(customer).some(n => n.tag === 'h2' && n.textContent === headings[payload.result.state]));
      assert(!nodes.some(n => n.textContent === 'Ratkaisuehdotus'));
      assert.equal(nodes.some(n => n.textContent === 'Vastauksessa käytetyt lähteet'), payload.result.state === 'safety_stop');
      const diagnostics = nodes.find(n => n.tag === 'details' && n.id === 'diagnostics');
      assert(diagnostics, 'IT-diagnostiikka puuttuu');
      assert.equal(diagnostics.open, false, 'Diagnostiikan pitää olla oletuksena suljettu');
      assert.equal(diagnostics.children[0].tag, 'summary');
      assert(tree(diagnostics.children[0]).some(n => n.textContent === 'IT-asiantuntijan diagnostiikka'));
      const diagnosticNodes = tree(diagnostics);
      assert(diagnosticNodes.some(n => n.textContent === 'Käsittelytila: Vain haku (demo) | vastauksen tila: '+payload.result.state));
      const backend = {keyword:'Sanahaku', vector:'Vektorihaku'}[payload.search.backend];
      assert(backend, 'Tuntematon testin hakutapa');
      assert(diagnosticNodes.some(n => n.textContent === 'Hakutapa: '+backend+' | mallin käyttö: OpenAI-kutsua ei tehty'),
        'OpenAI-kutsun tekemättä jääminen pitää ilmoittaa diagnostiikassa');
      assert(!tree(customer).some(n => n.textContent.includes('mallin käyttö:')));
      for (const question of payload.result.questions) {
        assert(tree(customer).some(n => n.tag === 'li' && n.textContent === question.text && !insideDetails(n)),
          'Tarkentavan kysymyksen pitää näkyä asiakasnäkymässä: '+card.id+'/'+kind);
      }
      assert.equal(h.els.send.disabled, false);
      for (const c of payload.candidates) {
        const entry = nodes.find(n => n.className === 'candidate' + (c.eligible ? '' : ' excluded') &&
          n.children.some(child => child.textContent.startsWith(c.guide_id+' —')));
        assert(entry, c.guide_id);
        assert(diagnosticNodes.includes(entry), 'Hakuehdokkaan pitää olla diagnostiikassa: '+c.guide_id);
        const children = tree(entry);
        assert(children.some(n => n.textContent.startsWith(c.eligible ? 'Hakuehdokas' : 'Ei hyväksytä vastauksen lähteeksi')));
        for (const s of c.steps) assert(!children.some(n => n.textContent === s.text));
        assert(!children.some(n => n.tag === 'ol' || n.tag === 'details'));
        assert(children.some(n => n.textContent.includes(c.version) &&
          n.textContent.includes(c.retrieval_method === 'lexical_fallback' ? 'Leksikaalinen varahaku — ei vektoripistettä' : 'pisteet '+c.score)));
        if(c.chunk_id) assert(children.some(n => n.textContent.includes('tekstiosa '+c.chunk_id)));
      }
      rendered++;
      if (kind !== 'controlled') continue;
      const visible = nodes.filter(n => !insideDetails(n)).map(n => n.textContent).join('\n');
      if (card.id === 'D06') {
        const excluded = nodes.filter(n => n.className === 'candidate excluded');
        policy(card.id, 'Poissuljetun ohjeen toimintavaiheita ei tarjota avattavaksi',
          !excluded.some(n => tree(n).some(x => x.tag === 'li')), 'medium',
          'Tarkistetaan, ettei poissuljetun ehdokkaan toimintavaiheita ole DOM:ssa.');
      }
      if (card.clarification_required) {
        policy(card.id, 'Olennainen tarkentava kysymys näkyy',
          payload.result.questions.length > 0, 'low',
          'Nykyinen tulos sisältää vain yleisen tarkennuskehotuksen, ei kohdennettua kysymystä.');
      }
      if (card.id === 'D09') {
        const candidate = payload.candidates.find(c => c.guide_id === 'IAM-001');
        policy(card.id, 'Vastausdatan ennakkohyväksyntä, IT-arvio ja kiertämiskielto säilyvät alkuperäisessä järjestyksessä',
          candidate.steps[1].text.includes('hyväksyttäväksi') &&
          candidate.steps[2].text.includes('hyväksynnän jälkeen') &&
          candidate.steps[2].text.includes('Älä yritä kiertää'), 'high',
          'Tämä tarkistus koskee vastausdatan eheyttä. Ehdokkaan vaiheita ei tarjota käyttöliittymässä toimintaohjeiksi.');
      }
      if (card.id === 'D10') {
        policy(card.id, 'Vieraan kirjautumisen hyväksymiskielto näkyy heti',
          visible.includes('Älä hyväksy kirjautumista, jota et itse aloittanut.'), 'high',
          'Näkyvyys tarkistetaan details-elementtien ulkopuolisesta tekstistä.');
      }
      if (card.id === 'D11') {
        policy(card.id, 'Tunnusten antamisen jälkeen välitön yhteys IT-tukeen näkyy heti',
          visible.includes('ilmoita siitä IT-tuelle heti'), 'high',
          'Välittömän ilmoituksen näkyvyys tarkistetaan ilman ohjeen avaamista.');
      }
      if (card.id === 'D12') {
        const steps = payload.result.state === 'safety_stop' ? payload.result.steps : payload.candidates.find(c => c.guide_id === 'DEVICE-004').steps;
        policy(card.id, 'Vaarallisen laitteen käytön lopettaminen näkyy heti',
          visible.includes('lopeta käyttö ja ota yhteys IT-tukeen'), 'high',
          'Keskeytysohjeen näkyvyys tarkistetaan ilman ohjeen avaamista.');
        policy(card.id, 'Vaaratilanteessa keskeytysohje edeltää lataustestausta',
          steps[0].text.includes('lopeta käyttö'), 'high',
          'Ensimmäisen tarjotun vaiheen pitää keskeyttää käyttö, ei testata laturia.');
      }
    }
  }
  // Todellisen tapahtumakäsittelijän vanhan vastauksen sivuutus ja tyhjennys.
  const h = setup();
  h.els.ticket.value = report.cases[0].card.ticket;
  const pending = h.els.send.onclick();
  h.els.ticket.handlers.input();
  h.respond({ok:true, json:async () => report.cases[0].controlled}); await pending;
  assert.equal(h.els.out.children.length, 0);
  for (const [id, event] of [['ticket','input'], ['mode','change'], ['backend','change']]) {
    h.els.out.children.push(element()); h.els[id].handlers[event]();
    assert.equal(h.els.out.children.length, 0);
  }
  // HTML:ää muistuttava sisältö kulkee tekstinä, ei innerHTML:n kautta.
  h.context.payload = JSON.parse(JSON.stringify(report.cases[0].controlled));
  h.context.payload.result.summary = '<img src=x onerror=alert(1)>';
  h.context.payload.known_facts = [{field:'internet_working', value:true,
    evidence:'<script>alert("diagnostics")</script>'}];
  vm.runInNewContext('render(payload)', h.context);
  assert(tree(h.els.out).some(n => n.textContent === '<img src=x onerror=alert(1)>'));
  assert(tree(h.els.out).some(n => insideDetails(n) && n.textContent.includes('<script>alert("diagnostics")</script>')));
  assert(!tree(h.els.out).some(n => n.tag === 'img' || n.tag === 'script'));
  return {test_kind:'production_js_in_dom_double', rendered_payloads:rendered,
    case_cards:report.cases.length, structural_checks:'passed',
    stale_and_clear_checks:'passed', text_rendering_check:'passed',
    browser_visual_review:'not_performed', policy_checks,
    policy_failed:policy_checks.filter(c => !c.passed).length};
};

// Paikallinen uusinta projektin juuressa:
// node tests/ui_demo_chain_test.cjs evaluation/demo_chain_runs/<aikaleima>/demo_observations.json
// Exit 2 tarkoittaa todettuja tavoitevaatimusten puutteita, ei testiajon kaatumista.
if (require.main === module) {
  const fs = require('node:fs');
  module.exports(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')),
    fs.readFileSync('index.html', 'utf8')).then(result => {
      console.log(JSON.stringify(result, null, 2));
      process.exitCode = result.policy_failed ? 2 : 0;
    }).catch(error => { console.error(error); process.exitCode = 1; });
}
