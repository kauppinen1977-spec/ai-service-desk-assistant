"""Rajatut soveltuvuussäännöt. Eivät korvaa kielentulkintaa tai ihmisarviointia."""
import re

# Keskeytystilassa vain nämä alkuperäiset turvallisuusvaiheet ovat sallittuja.
# DEVICE-004:n latausilmaisimen selvittäminen ei kuulu vaaratilanteeseen.
SAFETY_STEPS = {'DEVICE-004': (2,), 'IAM-003': (3,), 'MAIL-003': (1, 2, 3)}
SAFETY_EVENTS = {'unsolicited_authentication', 'suspicious_account_event', 'lost_work_device', 'malware_alert'}
FACT_VALUES = {'startup_stage': {'no_response','power_no_display','boot_stalled'},
               'recovery_prompt': {'disk_encryption'}, 'file_loss': {True},
               'signed_in': {True}, 'access_denied': {True}}
FACT_LABELS = {'startup_stage':'käynnistymisvaihe','recovery_prompt':'levyn salauksen palautuspyyntö',
               'file_loss':'tiedoston poistaminen tai ylikirjoittaminen',
               'signed_in':'onnistuva kirjautuminen','access_denied':'palvelukohtainen käyttöesto'}


def validate_guide_policy(guide):
    policy = guide.get('applicability', {})
    if not isinstance(policy,dict) or set(policy)-{'requires','excludes','startup_guide'}:
        raise ValueError('Invalid applicability policy')
    if 'startup_guide' in policy and type(policy['startup_guide']) is not bool:
        raise ValueError('Invalid startup guide flag')
    for group in ('requires','excludes'):
        conditions = policy.get(group,{})
        if not isinstance(conditions,dict):raise ValueError('Invalid applicability conditions')
        for key,value in conditions.items():
            if key not in FACT_VALUES or type(value) not in (str,bool) or value not in FACT_VALUES[key]:
                raise ValueError('Unknown applicability condition')
    if 'safety_event' in guide or 'safety_steps' in guide:
        indices = guide.get('safety_steps')
        if (guide.get('safety_event') not in SAFETY_EVENTS or guide.get('needs_human') is not True or
            not isinstance(indices,list) or not indices or
            any(type(i) is not int or not 1<=i<=len(guide['steps']) for i in indices) or
            len(set(indices))!=len(indices)):
            raise ValueError('Invalid safety source policy')


def safety_step_numbers(guide):
    return SAFETY_STEPS.get(guide['id'], tuple(guide.get('safety_steps',[])))


def safety_sources(ticket,guides=None):
    """Rajattu ensiohje käyttäjän vahvistamasta vaarasta, ei hakuluokittelu."""
    text = re.sub(r'"[^"\n]*"|”[^”\n]*”|“[^”\n]*”|«[^»\n]*»', '', ticket.lower())
    clauses = [s.strip() for s in re.split(r'[.!?;\n]+|,\s*(?:mutta|vaikka)\b', text)]
    clauses = [s for s in clauses if s and not re.search(
        r'\b(?:jos|ohjeessa|esimerkissä|harjoituksessa)\b', s)]
    observed = ' '.join(clauses)

    def affirmed(pattern):
        for clause in clauses:
            for match in re.finditer(pattern, clause):
                prefix = clause[max(0, match.start()-60):match.start()]
                # Kielto eri osalauseessa ei kumoa vahvistettua vaarahavaintoa.
                prefix = re.split(r'\b(?:koska|sillä|ja|mutta)\b', prefix)[-1]
                if not re.search(r'\b(?:ei|en|eikä|emme|älä|ehkä|luulen|mahtaako)\b', prefix):
                    return True
        return False

    result = []
    if affirmed(r'\b(?:akku\s+(?:on\s+)?turvonnut|(?:pohja|akku|kuori)\s+pullistuu|'
                 r'(?:laite|kannettava|läppäri|akku|(?:tieto|pöytä|työ)?kone)\s+(?:on\s+poikkeuksellisen\s+kuuma|kuumenee\s+poikkeavasti))\b'):
        result.append('DEVICE-004')
    request = affirmed(r'kirjautumispyy\w*|tunnistautumispyy\w*|authenticator|'
                       r'pyytää\s+(?:taas\s+|jälleen\s+)?hyväksymään\s+kirjautumi\w*')
    uninitiated = re.search(r'\ben\s+(?:ole\s+)?(?:itse\s+)?(?:aloittanut|yritä\s+kirjautua)\b', observed)
    if request and uninitiated:
        result.append('IAM-003')
    disclosed = affirmed(r'\b(?:syötin|annoin|kirjoitin|olen\s+(?:syöttänyt|antanut|kirjoittanut))\b'
                         r'.{0,70}?(?:salasana\w*|tunnuks\w*|kertakoodi\w*|vahvistuskoodi\w*)')
    suspicious = affirmed(r'kalastelu\w*|epäilyttäv\w*|viera(?:alle|s|lle)\s+sivu\w*|'
                           r'tuntemattom\w*\s+sivu\w*')
    if disclosed and suspicious:
        result.append('MAIL-003')
    if guides is not None:
        events = []
        if 'IAM-003' in result:events.append('unsolicited_authentication')
        account_event = affirmed(r'ilmoituksen\s+onnistuneesta\s+kirjautumisesta|'
                                 r'tilini\s+(?:salasana|tunnistautumistapa)\s+on\s+vaihdettu')
        if (account_event and re.search(r'\ben\s+(?:tunnista|vaihtanut|muuttanut)\b',observed) and
                not re.search(r'\btunnistan\s+\w*\s+omakseni\b',observed)):
            events.append('suspicious_account_event')
        if (affirmed(r'\btyö(?:kannettava(?:ni)?|puhelin|puhelimeni|laite|laitteeni|tietokone(?:eni)?)\s+(?:on\s+)?(?:kadonnut|varastettu)\b') and
                not affirmed(r'\b(?:se|työlaite|työkannettava)\s+löytyi\s+ja\s+on\s+(?:nyt\s+)?hallussani\b')):
            events.append('lost_work_device')
        if affirmed(r'\b(?:virustorjunta|suojausohjelma)\s+(?:hälytti|hälyttää)\b|'
                    r'\bsuoritin\s+epäilyttävän\s+tiedoston\b'):
            events.append('malware_alert')
        for event in events:
            matching = [g['id'] for g in guides if g.get('safety_event')==event]
            if len(matching)==1:
                if event=='unsolicited_authentication':result.remove('IAM-003')
                result.append(matching[0])
    return result

def startup_problem(text):
    """Explicit whole-device startup report, not an inferred power/OS diagnosis.

    Do not turn quotations, uncertainty or contradictory running observations
    into a confirmed fact. Also used to check an explicitly matching guide scope.
    """
    text = re.sub(r'"[^"\n]*"|”[^”\n]*”|“[^”\n]*”|«[^»\n]*»', '', text)
    device = r'(?:(?:tieto|pöytä)?kone(?:eni)?|kannettava(?:ni)?|läppäri(?:ni)?)'
    if re.search(r'\b'+device+r'\s+(?:käynnistyy|toimii|on\s+käynnissä|lähtee\s+käyntiin)\b', text, re.I):
        return None
    pattern = (r'\b'+device+r'\s+ei\s+(?:(?:enää|nyt|ollenkaan|lainkaan)\s+)*'
               r'(?:käynnisty|lähde\s+(?:käyntiin|päälle)|mene\s+päälle)\b|'
               r'\ben\s+saa\s+(?:tietokonetta|konetta|pöytäkonetta|kannettavaa|läppäriä)'
               r'(?:ni)?\s+(?:käyntiin|päälle)\b')
    for sentence in re.finditer(r'[^.!?\n]+[.!?]?', text):
        clause = sentence.group()
        if '?' in clause or re.search(r'\b(?:jos|ehkä|luulen|mahtaako|mahdollisesti|ohjeessa|esimerkissä|lainaus)\b|'
                                     r'\bei\s+(?:ole\s+totta|pidä\s+paikkaansa)\b|'
                                     r'\ben\s+(?:ole\s+varma|tiedä|usko)\b', clause, re.I):
            continue
        match = re.search(pattern, clause, re.I)
        if match:
            return match.group()
    return None


def batch_facts(ticket):
    text = re.sub(r'"[^"\n]*"|”[^”\n]*”|“[^”\n]*”', '', ticket)
    statements = [m.group() for m in re.finditer(r'[^.!?\n]+[.!?]?',text)
                  if '?' not in m.group() and not re.search(
                      r'\b(?:ehkä|jos|luulen|mahdollisesti|onko|ohjeessa|esimerkissä)\b|'
                      r'\ben\s+(?:tiedä|ole\s+varma|usko)\b|\bei\s+(?:ole\s+totta|pidä\s+paikkaansa)\b',m.group(),re.I)]
    observed = ' '.join(statements)
    def match(pattern):return re.search(pattern,observed,re.I)
    facts=[]
    no_lights=match(r'\bei\s+(?:syty\s+)?(?:valoja|merkkivaloja)\b|merkkivalot\s+eivät\s+syty')
    no_sound=match(r'\b(?:ei|eikä)\s+(?:kuulu\s+)?ääntä\b|'
                   r'(?:tuulettimesta\s+ei|eikä\s+tuulettimesta)\s+kuulu\s+ääntä')
    power=match(r'merkkivalot\s+palavat|tuuletin\s+pyörii')
    display=match(r'oma\s+näyttö\s+on\s+(?:musta|pimeä)')
    boot=match(r'käynnistys\s+pysähtyy\s+(?:logoon|virheilmoitukseen)|'
               r'(?:tieto)?kone\s+jää\s+(?:valmistajan\s+)?logoon')
    stage = None
    if no_lights and no_sound and not power and not boot:stage='no_response'
    elif power and display and not no_lights and not no_sound and not boot:stage='power_no_display'
    elif boot and not no_lights and not no_sound and not display:stage='boot_stalled'
    if stage and re.search(r'\b(?:(?:tieto|pöytä|työ)?kone\w*|kannettava\w*|läppäri\w*)\b',observed,re.I):
        facts.append(dict(field='startup_stage',value=stage,evidence=observed.strip()))
    recovery=match(r'näytössä\s+on\s+bitlocker[^.!?]{0,50}palautusavai\w*|'
                   r'(?:kone\s+)?pyytää\s+levyn\s+salauksen\s+palautusavai\w*')
    if recovery:facts.append(dict(field='recovery_prompt',value='disk_encryption',evidence=recovery.group()))
    lost=match(r'\b(?:poistin|ylikirjoitin)\s+(?:työ)?tiedoston\b|\btiedosto\s+on\s+(?:poistettu|ylikirjoitettu)\b')
    if lost:facts.append(dict(field='file_loss',value=True,evidence=lost.group()))
    signed=match(r'\bkirjautuminen\s+onnistuu\b')
    if signed:facts.append(dict(field='signed_in',value=True,evidence=signed.group()))
    denied=match(r'\bpalvelu\w*[^.!?]{0,45}(?:pääsy\s+estetty|käyttöoikeus\s+puuttuu)')
    if denied:facts.append(dict(field='access_denied',value=True,evidence=denied.group()))
    return facts


def known_facts(ticket):
    startup = startup_problem(ticket)
    facts = [{'field':'device_startup_unresolved','value':True,'evidence':startup}] if startup else []
    facts += batch_facts(ticket)
    # Näytetään myös täsmällinen tekstikohta, johon sääntö osui.
    positive=[r'(?:tavalliset\s+)?verkkosivut\s+avautuvat',r'(?:muu\s+)?internetyhteys\s+toimii',r'netti\s+(?:muuten\s+)?toimii',r'internet\s+(?:muuten\s+)?toimii']
    negative=[r'(?:mikään|yksikään)\s+(?:verkko)?sivu\s+ei\s+avaudu',r'(?:internet|netti|internetyhteys)\s+ei\s+toimi']
    pos=next((m for p in positive if (m:=re.search(p,ticket,re.I))),None)
    neg=next((m for p in negative if (m:=re.search(p,ticket,re.I))),None)
    # Kysymystä tai epävarmaa ilmaisua ei tulkita vahvistetuksi tiedoksi.
    uncertain=bool(re.search(r'\b(?:ehkä|jos|luulen|mahtaako|toimiiko|välillä|ajoittain|joskus|pätkii)\b',ticket,re.I))
    unconfirmed=any(re.search(
        r'\?|\b(?:luultavasti|mahdollisesti|ilmeisesti|varmaan|'
        r'en\s+(?:usko|tiedä|ole\s+varma)|'
        r'ei\s+(?:ole\s+(?:varmaa|totta)|pidä\s+paikkaansa))\b',
        sentence.group(),re.I)
        for sentence in re.finditer(r'[^.!?\n]+[.!?]?',ticket)
        if any(match and sentence.start()<=match.start()<sentence.end() for match in [pos,neg]))
    if uncertain or unconfirmed or bool(pos)==bool(neg):return facts
    match=pos or neg
    return facts+[{'field':'internet_working','value':bool(pos),'evidence':match.group(0)}]

def internet_value(facts):
    return next((f['value'] for f in facts if f['field']=='internet_working'),None)

# Source scopes are matched against source metadata, never source identifiers.
# The request must independently describe a problem/request in that same scope.
# Unknown scopes fail closed until supported by a validated fact policy.
PROBLEM_SCOPES = (
    ('printing', r'tulost', r'tulost\w*|monitoimikone\w*|paperituk\w*'),
    ('display', r'näyttö|monitor', r'näyttö\w*|näytön\w*|näytössä|monitor\w*|kuva\w*'),
    ('storage', r'tallennustila|levytila|kiintolevy', r'levy\w*|kiintolevy\w*|tallennu\w*'),
    ('charging', r'lataus|akku|laturi', r'akku\w*|akun|latur\w*|lata\w*'),
    ('application', r'sovellus|ohjelma', r'\w*ohjelm\w*|\w*sovellu\w*'),
    ('privilege', r'ylläpito|järjestelmänvalvoj|admin', r'admin\w*|ylläpi\w*|järjestelmänvalvoj\w*|korotet\w*'),
    ('forgotten_password', r'unohtunut salasana', r'salasan\w*|password\w*'),
    ('authentication', r'monivaihei|tunnistautumis|mfa|authenticator', r'mfa\w*|authenticator\w*|tunnistaut\w*|vahvistuskood\w*|hyväksynt\w*|sisäänpääsy\w*|kirjautumis\w*'),
    ('locked_account', r'lukittu|lukkiut', r'lukit\w*|lukki\w*'),
    ('onboarding', r'uusi työntekijä|uuden työntekijän|perehdytys|onboarding', r'aloitta\w*|aloitu\w*|perehdy\w*|onboarding|uusi työntekijä'),
    ('offboarding', r'työsuhteen päättym|offboarding', r'päätty\w*|lähtev\w*|viimeinen työpäivä|offboarding'),
    ('mail_capacity', r'postilaatikon tila|kiintiö', r'(?:sähkö)?postilaatik\w*|kiintiö\w*|viestitila\w*|laatikkoni|vastaanottaj\w*[^.!?]{0,60}viest\w*'),
    ('suspicious_message', r'epäilyttävä sähköposti|kalastelu|phishing', r'kalastel\w*|phishing|epäilyttäv\w*|viesti\w*'),
    ('calendar', r'kalenteri|kokouskutsu', r'kalenter\w*|kokouskutsu\w*'),
    ('meeting_audio', r'kokouksen ääni|mikrofoni|kuulokkeet', r'teams\w*|kokou\w*|mikrofon\w*|kuulokk\w*'),
    ('mail', r'sähköposti|outlook', r'sähköpost\w*|outlook\w*|verkkopost\w*|viestiohjelm\w*'),
    ('wireless', r'langaton|wifi|wlan', r'langato\w*|langattom\w*|wifi\w*|wlan\w*'),
    ('internal_address', r'sisäisen palvelun|nimipalvelu|dns', r'sisäi\w*\s+(?:\w+\s+)?(?:palvel\w*|sivu\w*)|dns|nimipalvel\w*'),
    ('internet', r'internet', r'internet\w*|netti\w*|verkko(?:sivu|yhtey)\w*'),
    ('remote_access', r'vpn|etäyhteys', r'vpn\w*|etäyhte\w*|etätyöyhte\w*'),
)


def _observed_clauses(ticket):
    text = re.sub(r'"[^"\n]*"|”[^”\n]*”|“[^”\n]*”|«[^»\n]*»', '', ticket)
    return [s.strip() for s in re.split(r'[.!?;\n]+|,?\s+\b(?:mutta|vaikka|lisäksi)\b', text)
            if s.strip() and not re.search(
                r'\b(?:jos|ehkä|luulen|mahdollisesti|ohjeessa|esimerkissä|lainaus)\b|'
                r'\ben\s+(?:tiedä|ole\s+varma|usko)\b|'
                r'\bei\s+(?:ole\s+totta|pidä\s+paikkaansa)\b', s, re.I)]


def applicability_evidence(guide,facts,ticket=None):
    """Explainable, bounded positive support, not a semantic correctness verdict."""
    required = guide.get('applicability',{}).get('requires',{})
    if required:
        evidence = [f for f in facts if f['field'] in required and required[f['field']]==f['value']]
        return evidence if {f['field'] for f in evidence}==set(required) else []
    scope = guide.get('title','')+'. '+guide.get('symptoms','')
    if startup_problem(scope):
        return [f for f in facts if f['field']=='device_startup_unresolved' and f['value'] is True]
    if ticket is None:
        return []
    metadata = guide.get('title','')+' '+' '.join(guide.get('keywords',[]))
    selected = next(((name,request) for name,source,request in PROBLEM_SCOPES
                     if re.search(source,metadata,re.I)), None)
    if selected is None:return []
    name, target = selected
    clauses = [s for s in _observed_clauses(ticket) if re.search(r'\b(?:'+target+r')\b',s,re.I)]
    healthy = (r'\b(?:toimii|toimivat)\b|'
               r'\bei\s+ole\s+(?:\w+\s+){0,2}(?:vikaa|ongelmaa|häiriötä|loppu|täynnä|pimeä|musta)\b')
    def after_target(s, pattern):
        # A failure of another object before this target is not supporting
        # evidence. Do not carry predicates across an independent conjunction.
        return any(re.search(pattern,re.split(r'\b(?:ja|eikä)\b',s[m.start():],maxsplit=1,flags=re.I)[0],re.I)
                   for m in re.finditer(r'\b(?:'+target+r')\b',s,re.I))
    if any(after_target(s,healthy) for s in clauses):return []
    problem = (r'\b(?:ei|eivät|en)\s+(?:(?:enää|nyt|ollenkaan|lainkaan)\s+)*'
               r'(?:toimi|reagoi|liiku|näy\w*|käynnisty|lataudu|yhdist\w*|muodostu|tulosta|avaudu|onnistu|'
               r'kuulu|saavu|saa|pääse|muista|vastaanota|lähetä)\b|'
               r'\b(?:ei|ettei)\s+(?:tallennu\w*\s+)?ole\s+tilaa\b|'
               r'\b(?:virhe\w*|ongelm\w*|häiriö\w*|epäonnis\w*|hylk\w*|jää\w*|'
               r'pysäht\w*|musta|pimeä|täynnä|täytty\w*|loppu\w*|puuttu\w*|'
               r'lukit\w*|lukki\w*|unoh\w*|tarvits\w*|vaatii|paperituk\w*|'
               r'aloitta\w*|päätty\w*|lähtev\w*|epäilyttäv\w*|kalastel\w*)\b')
    capacity = r'\btäynnä\b|\btäytty\w*\b|\b(?:ei|ettei)\b[^.!?]{0,45}\bmahdu\b|\bkiintiö\w*\s+ylitt\w*'
    def supported(s):
        if name=='charging' and re.search(r'\bei\s+(?:enää\s+)?lataudu\b',s,re.I):return True
        if name=='storage' and re.search(r'\b(?:ei|ettei)\s+(?:tallennu\w*\s+)?ole\s+tilaa\b',s,re.I):return True
        if name=='mail_capacity':return bool(re.search(capacity,s,re.I))
        if name=='suspicious_message':
            return bool(re.search(r'\b(?:kalastel\w*|phishing|epäilyttäv\w*)\b',s,re.I) or
                        (re.search(r'\b(?:salasan\w*|tunnuk\w*)\b',s,re.I) and
                         re.search(r'\b(?:pyyt\w*|vaati\w*|käske\w*|uhka\w*)\b',s,re.I)))
        if name=='authentication' and re.search(r'\b(?:pyyt\w*|kuitta\w*|vahvista\w*)\b',s,re.I):return True
        return after_target(s,problem) or bool(re.search(
            r'\b(?:tarvits\w*|vaati\w*|unoh\w*|en\s+(?:saa|muista))\b[^.!?]{0,60}\b(?:'+target+r')\b',s,re.I))
    return [dict(field='problem_scope',value=name,evidence=s) for s in clauses if supported(s)]


def input_problem_question(ticket):
    """Ask observations only; no invented peripheral troubleshooting runbook."""
    target = r'\b(?:hiir\w*|osoiti\w*|kosketuslev\w*|touchpad\w*)\b'
    failure = r'\b(?:ei|eivät)\s+(?:(?:enää|nyt|ollenkaan)\s+)*(?:toimi|reagoi|liiku)\b'
    if any(re.search(target,s,re.I) and re.search(failure,s,re.I) for s in _observed_clauses(ticket)):
        return 'Onko kyse erillisestä hiirestä vai kannettavan kosketuslevystä? Liikkuuko osoitin, ja toimivatko painikkeet?'
    return None


def compatible(guide,facts):
    """Negative constraints, also rechecked when assembling prefiltered sources."""
    values={f['field']:f['value'] for f in facts}
    policy=guide.get('applicability',{})
    if guide.get('safety_event'):
        return False,'Turvallisuusohje näytetään vain vahvistetun tapahtuman ensiohjepolussa.'
    for field,value in policy.get('requires',{}).items():
        if values.get(field)!=value:
            return False,'Ohjeen edellyttämä havainto puuttuu tai on ristiriitainen: '+FACT_LABELS[field]+'.'
    for field,value in policy.get('excludes',{}).items():
        if values.get(field)==value:
            return False,'Ohje on suljettu pois vahvistetun havainnon perusteella: '+FACT_LABELS[field]+'.'
    if values.get('recovery_prompt')=='disk_encryption' and policy.get('requires',{}).get('recovery_prompt')!='disk_encryption':
        return False,'Salauksen palautuspyyntö edellyttää omaa hyväksyttyä käsittelyä.'
    if values.get('device_startup_unresolved') is True or 'startup_stage' in values:
        scope = guide.get('title','')+'. '+guide.get('symptoms','')
        if not policy.get('startup_guide') and not startup_problem(scope):
            return False,'Ohje ei käsittele ilmoitettua koko tietokoneen käynnistymisongelmaa. Tilannetta on tarkennettava ennen ohjeen valintaa.'
    value=internet_value(facts)
    if value is True and guide['id']=='NET-004':
        return False,'Ohje koskee täydellistä internetkatkoa, mutta käyttäjä ilmoitti yhteyden toimivan.'
    if value is False and guide['id']=='VPN-001':
        return False,'VPN-ohjeen sijaan selvitetään ensin ilmoitettu yleinen internetkatko.'
    return True,''


def applicable(guide,facts,ticket=None):
    ok,reason=compatible(guide,facts)
    if not ok:return ok,reason
    if not applicability_evidence(guide,facts,ticket):
        return False,'Ohjeen ongelma-alueeseen liittyvää myönteistä soveltuvuusnäyttöä ei ole vahvistettu.'
    return True,''

def questions_for(guide,facts):
    if guide['id']=='VPN-001':
        q=[{'id':'VPN-001:error','text':'Mikä tarkka virheilmoitus näkyy VPN-yhteyden muodostuksessa?','source_id':'VPN-001'}]
        if internet_value(facts) is None:
            q.append({'id':'VPN-001:internet','text':'Toimiiko tavallinen internetyhteys ilman VPN-yhteyttä?','source_id':'VPN-001'})
        return q
    if guide['id']=='NET-004':
        return [{'id':'NET-004:other_device','text':'Toimiiko toinen laite samassa verkossa?','source_id':'NET-004'}]
    return [{'id':guide['id']+':detail','text':guide['follow_up'],'source_id':guide['id']}]

def steps_for(guide,facts):
    # Vain täsmällinen, jo vastattu VPN-internettarkistus ohitetaan.
    # Muut vaiheet ja hyväksyntäehdot säilyvät sanasta sanaan alkuperäisestä ohjeesta.
    return [{'text':text,'source_id':guide['id'],'source_step':i,'version':guide['version']}
            for i,text in enumerate(guide['steps'],1)
            if not (guide['id']=='VPN-001' and i==1 and internet_value(facts) is True)]
