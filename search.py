"""Ohjeiden pilkkominen, paikalliset upotukset ja kosinivertailu.
Ei kytkentää kielimallin API:in. Sanahaku säilyy vertailuna.
"""
import copy, hashlib, json, math, os, re, tempfile
from pathlib import Path
from functools import lru_cache
MODEL_ID='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
ROOT=Path(__file__).resolve().parent
class SearchError(Exception): pass

@lru_cache(maxsize=1)
def encoder():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SearchError('Vektorihaun kirjastot puuttuvat. Suorita asenna_vektorihaku.bat tai valitse sanahaku.') from None
    try:
        import torch
        torch.set_num_threads(2)
        try:
            return SentenceTransformer(MODEL_ID,device='cpu',trust_remote_code=False,local_files_only=True)
        except (OSError,ValueError):
            return SentenceTransformer(MODEL_ID,device='cpu',trust_remote_code=False)
    except Exception:
        raise SearchError('Paikallinen upotusmalli ei latautunut. Suorita valmistele_haku.py; ensimmäinen ajo tarvitsee internetyhteyden Hugging Faceen.') from None

def validate_guides(guides):
    seen=set()
    for g in guides:
        if not isinstance(g.get('id'),str) or g['id'] in seen: raise SearchError('Ohjeen tunniste puuttuu tai on päällekkäinen.')
        seen.add(g['id'])
        if g.get('category') not in ['verkko','käyttöoikeudet','sähköposti','laitteet','muu']: raise SearchError('Ohjeen luokka ei kelpaa.')
        if not all(isinstance(g.get(k),str) and g[k] for k in ['title','version','follow_up']): raise SearchError('Ohjeen metatiedot puuttuvat.')
        for k in ['steps','keywords']:
            if not isinstance(g.get(k),list) or not g[k] or any(not isinstance(x,str) for x in g[k]):raise SearchError('Ohjeen vaiheet tai hakusanat puuttuvat.')
        if type(g.get('needs_human')) is not bool: raise SearchError('Ohjeen jatkokäsittelykenttä ei kelpaa.')
        from response_rules import validate_guide_policy
        try:validate_guide_policy(g)
        except ValueError as error:raise SearchError(str(error)) from None

def chunks(guides,tokenizer=None,max_tokens=110):
    """Jokainen vaihe omaksi osakseen; pitkä vaihe pilkotaan tokenirajaan.
    Toistetaan otsikko ja oireet. Ei muuteta alkuperäisiä toimintaohjeita.
    """
    validate_guides(guides)
    out=[]
    for g in guides:
        header=g['title']+'. '+g.get('symptoms','')
        bodies=[g.get('symptoms',g['title'])]+g['steps']+[g['follow_up']]
        for section,body in enumerate(bodies):
            words=body.split();part=[];piece=0
            def count(t):return len(tokenizer.encode(t,add_special_tokens=True)) if tokenizer else len(t.split())
            if count(header)>=max_tokens-8: raise SearchError('Ohjeen otsikko ja oirekuva ovat liian pitkiä pilkkomiseen.')
            for word in words:
                candidate=header+' '+' '.join(part+[word])
                if count(candidate)>max_tokens:
                    if count(header+' '+word)>max_tokens:raise SearchError('Yksittäinen sana ylittää pilkkomisrajan.')
                    out.append({'chunk_id':f"{g['id']}:{section}:{piece}",'guide_id':g['id'],'category':g['category'],'version':g['version'],'text':header+' '+' '.join(part)})
                    piece+=1;part=[]
                part.append(word)
            if part:out.append({'chunk_id':f"{g['id']}:{section}:{piece}",'guide_id':g['id'],'category':g['category'],'version':g['version'],'text':header+' '+' '.join(part)})
    return out

def normalized(v):
    norm=math.sqrt(sum(float(x)**2 for x in v))
    if not norm or not math.isfinite(norm): raise SearchError('Virheellinen upotusvektori.')
    return [float(x)/norm for x in v]

def _nontechnical_request_evidence(text):
    """Recognize only explicit nontechnical outputs with confirmed working context.

    Action/output families are topic-independent. Missing technical vocabulary
    never suffices: unknown sentences, mixed requests and safety reports stay open.
    """
    if re.search(r'["“”«»]|\b(?:ehkä|mahdollisesti|luulen|jos|onko|osittain|huonosti|välillä|ajoittain|käännä|suomenna|'
                 r'esimerkk\w*|aiemm\w*|aikaisemm\w*|lainau\w*)\b|\ben\s+(?:tiedä|ole\s+varma)\b',text,re.I):
        return None
    # Protective vetoes, not a required vocabulary for legitimate IT requests.
    if re.search(r'\b(?:auta|auttaa|neuvo|neuvoa|palauta|korjaa|tarkista|selvitä|asenna|käynnistä|'
                 r'kytke|avaa|näytä|miten|miksi|mistä|kuinka|virhe\w*|häiriö\w*|katke\w*|kaatu\w*|'
                 r'jumitt\w*|lukitt\w*|epäonnist\w*|kuumen\w*|turvon\w*|kirjaut\w*|salasan\w*|'
                 r'tunnuk\w*|vahvistuskood\w*)\b|\b(?:ei|eivät|en|emme)\s+'
                 r'(?:(?:enää|ollenkaan|aina|nyt|mitenkään)\s+)*'
                 r'(?:toimi|avaudu|aukea|käynnisty|onnistu|pääse|yhdisty|lataudu|tallennu|kuulu|näy|saa)\b',text,re.I):
        return None
    working=(r'\b\w*(?:ohjelma|sovellus|palvelu|kalenteri|tiedosto|pdf|taulukkolaskenta|tulostin|laite|kone)\w*\b'
             r'[^.!?;\n]*\b(?:toimii|toimivat|aukeaa|avautuu)\b|'
             r'\b(?:teknis\w*\s+(?:vikaa|ongelmaa|häiriötä)\s+ei\s+ole|'
             r'ei\s+ole\s+teknis\w*\s+(?:vikaa|ongelmaa|häiriötä)|'
             r'en\s+(?:tarvitse|pyydä|halua)\s+teknis\w*\s+(?:apua|ohjeita|neuvontaa))\b')
    request=(r'^\s*(?:(?:voitko|voitteko|voisitko|voisitteko)\s+)?'
             r'(?P<action>laskea?|laadi|laatia|kirjoita|kirjoittaa|päätä|päättää|myönnä|myöntää|hyväksy|hyväksyä)'
             r'\s+(?P<object>.+)$')
    technical_target=(r'\b(?:käyttöoikeu\w*|tunnu\w*|tili\w*|verk\w*|levy\w*|tallenn\w*|asennu\w*|'
                      r'päivity\w*|korotet\w*|tulost\w*|näyt\w*|ruut\w*|mikrofon\w*|'
                      r'aloitu\w*|päättymi\w*|perehdy\w*|ohje\w*)\b')
    requests,observations=[],[]
    for sentence in re.split(r'[.!?;\n]+',text):
        if not sentence.strip():continue
        match=re.match(request,sentence,re.I)
        if match:
            action,target=match['action'].casefold(),match['object']
            if re.search(technical_target,target,re.I):return None
            numeric=action.startswith('laske') and re.search(
                r'\b\w*(?:summa\w*|keskiarvo\w*|prosent\w*|osuu\w*|kustann\w*|hint\w*|mediaan\w*|kate\w*)\b',target,re.I)
            content=action.startswith(('laadi','laati','kirjoit')) and re.search(
                r'\b\w*(?:teksti\w*|puhe\w*|tiedot\w*|kertomu\w*|viesti\w*|tarina\w*|suunnitelm\w*|hyväksyn\w*|raport\w*)\b',target,re.I)
            delegated=action.startswith(('päät','myön','hyväks')) and re.search(r'\bpuolest(?:ani|amme)\b',target,re.I)
            if not (numeric or content or delegated):return None
            requests.append(match)
        elif re.search(working,sentence,re.I):observations.append(sentence.strip())
        else:return None
    if not requests or not observations:return None
    return {'requested_action':[m['action'] for m in requests],
            'requested_object':[m['object'] for m in requests],
            'confirmed_observations':observations,
            'evidence':observations+[m.group(0).strip() for m in requests]}


def _apply_request_scope(text,result):
    """Apply a high-precision service boundary, retaining the insurance regression."""
    evidence=_nontechnical_request_evidence(text)
    if evidence:
        return dict(result,hits=[],category='muu',ambiguous=False,
                    scope_filter=dict(evidence,reason='unsupported_requested_action',excluded_hits=result['hits']))
    policy=r'\b\w*vakuutu(?:s|ks\w+)\b'
    if not re.search(policy,text,re.I):return result
    request=r'^\s*(?:korvaako|korvaisiko|maksaako|maksaisiko|mikä|mitä|miten|miksi|missä|kuinka|paljonko|voiko|voitteko|saako|onko|kerro|selvitä|haluan\s+(?:tietää|selvittää))\b'
    questions=[part.strip() for part in re.split(r'[.!?;\n]+',text) if re.search(request,part,re.I)]
    def financial_question(part):
        if re.search(r'\b(?:miten|miksi|missä)\b',part,re.I):return False
        amount=re.search(r'\b(?:mikä|paljonko|kuinka\s+(?:paljon|suur\w*))\b.*\b(?:omavastu\w*|korvau\w*)\b',part,re.I)
        coverage=re.search(r'\b(?:korvaako|korvaisiko|maksaako|maksaisiko)\b',part,re.I) and re.search(policy,part,re.I)
        return bool(amount or coverage)
    # Keep mixed requests: a separate technical question must still reach support.
    if not questions or not all(financial_question(part) for part in questions):return result
    return dict(result,hits=[],category='muu',ambiguous=False,
                scope_filter={'reason':'insurance_financial_request','evidence':questions,
                              'excluded_hits':result['hits']})

def _rerank_same_category(text,hits,guides):
    """Promote only one unambiguously supported title/keyword match; keep cosine scores."""
    if len(hits)<2:return hits,None
    if re.search(r'\b(?:ehkä|mahdollisesti|luulen|jos|vai|onko)\b|\ben\s+tiedä\b',text,re.I):
        return hits,None
    # Failure statements support a topic; other negations conservatively prevent promotion.
    failure_verbs={'muista','toimi','onnistu','yhdisty','lataudu','avaudu',
                   'käynnisty','pääse','tunnista','lähetä','vastaanota'}
    if any(m.group(1).casefold() not in failure_verbs for m in re.finditer(
            r'\b(?:en|et|ei|emme|ette|eivät|älä|älkää|eikä|eivätkä)\s+(\w+)',text,re.I)):
        return hits,None
    def terms(value):
        # Short words match exactly; six-letter prefixes tolerate common Finnish inflections.
        return {word[:6]:word for word in re.findall(r'[^\W\d_]+',value.casefold()) if len(word)>=4}
    query_terms=terms(text)
    category=guides[hits[0]['guide_id']]['category']
    positions=[i for i,h in enumerate(hits) if guides[h['guide_id']]['category']==category]
    matches={}
    for i in positions:
        guide=guides[hits[i]['guide_id']]
        matches[i]=query_terms.keys() & terms(guide['title']+' '+' '.join(guide['keywords'])).keys()
    exclusive={i:match-set().union(*(other for j,other in matches.items() if j!=i))
               for i,match in matches.items()}
    supported=[i for i in positions if exclusive[i]]
    if len(supported)!=1 or supported[0]==0:return hits,None
    chosen=supported[0]
    order=[chosen]+[i for i in positions if i!=chosen]
    reordered=list(hits)
    for slot,original in zip(positions,order):reordered[slot]=hits[original]
    reason={'basis':'unique_title_or_keyword_term','promoted_source':hits[chosen]['guide_id'],
            'matched_terms':[query_terms[t] for t in sorted(exclusive[chosen])],
            'original_order':[h['guide_id'] for h in hits]}
    return reordered,reason

def _rerank_unsolicited_approval(text,hits,candidates,guides):
    """Match an explicit uninitiated authentication request to a source safety condition.

    Inspect threshold-qualified candidates before the top-k cutoff, but move only
    slots in the original winning category. Never infer an incident from a keyword.
    """
    if not hits or re.search(
            r'\b(?:ehkä|mahdollisesti|luulen|jos|vai|onko|käännä|suomenna|lainaus)\b|'
            r'\ben\s+(?:tiedä|ole\s+varma)\b',text,re.I):return hits,None
    authentication=r'\b(?:kirjaut\w*|tunnistaut\w*|sisäänpääs\w*)\b'
    approval=r'\b(?:hyväksy\w*|kuitta\w*|vahvista\w*)\b'
    uninitiated=(r'\b(?:en|et|ei)\s+(?:(?:ole|itse)\s+)*(?:aloittan\w*|käynnistä\w*|kirjautun\w*|'
                 r'avann\w*\s+(?:mitään\s+)?(?:työpalvel\w*|kirjaut\w*|tunnistaut\w*))\b')
    evidence=[re.search(pattern,text,re.I) for pattern in (
        authentication,approval,r'\b(?:pyyt\w*|pyynn\w*|pyynt\w*)\b',uninitiated)]
    if not all(evidence):return hits,None
    # A denied request or an additional negation is not positive incident evidence.
    if re.search(r'\b(?:ei|eivät)\s+(?:pyydä|tule|saavu)\b|\ben\s+(?:saa|näe)\b',text,re.I):
        return hits,None
    remainder=re.sub(uninitiated,'',text,flags=re.I)
    if re.search(r'\b(?:en|et|ei|emme|ette|eivät|eikä|älä|älkää)\b',remainder,re.I):
        return hits,None
    if re.search(r'\b(?:aloitin|käynnistin|kirjauduin)\b|'
                 r'\bolen\s+(?:itse\s+)?(?:aloittanut|käynnistänyt|kirjautunut)\b',remainder,re.I):
        return hits,None
    category=guides[hits[0]['guide_id']]['category']
    supported=[]
    for candidate in candidates:
        guide=guides[candidate['guide_id']]
        if guide['category']!=category:continue
        for step in guide['steps']:
            if (re.search(authentication,step,re.I) and re.search(uninitiated,step,re.I) and
                    re.search(r'\b(?:älä|ei\s+saa)\s+(?:hyväksy\w*|kuitta\w*|vahvista\w*)\b',step,re.I)):
                supported.append((candidate,step));break
    if len(supported)!=1:return hits,None
    chosen,step=supported[0]
    if chosen['guide_id']==hits[0]['guide_id']:return hits,None
    positions=[i for i,h in enumerate(hits) if guides[h['guide_id']]['category']==category]
    order=[chosen]+[hits[i] for i in positions if hits[i]['guide_id']!=chosen['guide_id']]
    reordered=list(hits)
    for slot,candidate in zip(positions,order):reordered[slot]=candidate
    return reordered,{'basis':'unsolicited_authentication_approval',
                      'promoted_source':chosen['guide_id'],'source_evidence':step,
                      'request_evidence':[match.group(0) for match in evidence],
                      'original_order':[h['guide_id'] for h in hits]}

def _rerank_credential_threat(text,hits,guides):
    """Prefer an existing safety source for an explicit credential threat in a message."""
    if len(hits)<2 or re.search(
            r'\b(?:ehkä|mahdollisesti|luulen|jos|vai|onko|käännä|suomenna|lainaus|esimerkk\w*)\b|'
            r'\ben\s+(?:tiedä|ole\s+varma)\b',text,re.I):return hits,None
    if re.search(r'\bei\s+pidä\s+paikkaansa\b|'
                 r'\b(?:ei|eivät)\s+(?:(?:ole|lainkaan|enää)\s+)*'
                 r'(?:uhka\w*|pyyd\w*|vaadi\w*|käske\w*|viiväst\w*|epäilyttäv\w*)\b',text,re.I):
        return hits,None
    patterns=[r'\b(?:viesti\w*|sähköposti\w*|lähettäj\w*)\b',
              r'\b(?:uhka\w*|viiväst\w*|sulkemis\w*)\b',
              r'\b(?:käske\w*|pyyd\w*|pyyt\w*|vaadi\w*|vaat\w*)\b',
              r'\b(?:vahvista(?:maan|mista)?|syöttämään|syötä|antamaan|anna)\b',
              r'\b(?:tunnuk\w*|salasan\w*|kirjautumistie\w*)\b',
              r'\b(?:osoitte\w*|link\w*|sivul\w*)\b']
    # All incident evidence must be in one affirmative sentence. A separate
    # "I have not opened it" describes exposure, not the absence of a threat.
    evidence=next((sentence.strip() for sentence in re.split(r'[.!?;\n]+',text)
                   if not re.search(r'\b(?:en|et|ei|emme|ette|eivät|eikä|älä|älkää)\b',sentence,re.I)
                   and all(re.search(pattern,sentence,re.I) for pattern in patterns)),None)
    if evidence is None:return hits,None
    category=guides[hits[0]['guide_id']]['category']
    supported=[]
    for i,hit in enumerate(hits):
        guide=guides[hit['guide_id']]
        if guide['category']!=category:continue
        avoid=next((s for s in guide['steps'] if re.search(
            r'\b(?:älä|ei\s+saa)\s+ava\w*\b[^.!?]*\b(?:link\w*|osoit\w*|liitte\w*)\b',s,re.I)),None)
        report=next((s for s in guide['steps'] if re.search(
            r'\b(?:ilmoit\w*|raportoi\w*)\b[^.!?]*\b(?:tietoturv\w*|turvallisuus\w*)\b',s,re.I)),None)
        if avoid and report:supported.append((i,[avoid,report]))
    if len(supported)!=1 or supported[0][0]==0:return hits,None
    chosen,source_evidence=supported[0]
    positions=[i for i,h in enumerate(hits) if guides[h['guide_id']]['category']==category]
    order=[chosen]+[i for i in positions if i!=chosen]
    reordered=list(hits)
    for slot,original in zip(positions,order):reordered[slot]=hits[original]
    return reordered,{'basis':'credential_threat_in_message',
                      'promoted_source':hits[chosen]['guide_id'],
                      'request_evidence':[evidence],'source_evidence':source_evidence,
                      'original_order':[h['guide_id'] for h in hits]}

def _rerank_mailbox_capacity(text,hits,guides):
    """Resolve an explicit recipient quota failure, not a local disk-space mention."""
    denial=(r'\b(?:sähköpostilaatik\w*|postilaatik\w*|kiintiö\w*|laatikkoni)\s+ei\s+ole\s+'
            r'(?:täynnä|täyttynyt)\b|\bvastaanottaj\w*\s+mahtuu\b|\bei\s+pidä\s+paikkaansa\b')
    if len(hits)<2 or re.search(denial,text,re.I) or re.search(
            r'\b(?:ehkä|mahdollisesti|luulen|jos|vai|onko|käännä|suomenna|lainaus|esimerkk\w*)\b|'
            r'\ben\s+(?:tiedä|ole\s+varma)\b',text,re.I):return hits,None
    # A second actual storage failure makes this a mixed request. Free space alone
    # is background; no numeric free-space threshold is inferred.
    if re.search(r'\b(?:levy\w*|[a-z]-asem\w*)\s+(?:(?:on|olevan)\s+)?(?:täynnä|loppu\w*|vähissä)\b|'
                 r'\btallennus\s+epäonnist\w*\b|\b(?:en|ei)\s+(?:saa|pysty)\s+tallenn\w*',text,re.I):
        return hits,None
    capacity=(r'\b(?:ettei\s+vastaanottaj\w*\s+mahdu|vastaanottaj\w*\s+ei\s+(?:mahdu|ole\s+tilaa))\b'
              r'[^.!?\n]*\bviest\w*\b|\b(?:vastaanottaj\w*\s+(?:(?:sähkö)?postilaatik\w*|kiintiö\w*)|'
              r'laatikkoni)\s+(?:on\s+)?(?:täynnä|täyttynyt)\b')
    delivery=r'\b(?:palaut\w*|toimitu\w*\s+epäonnist\w*|lähett\w*\b[^.!?\n]*\b(?:ilmoitu\w*|virhe\w*))\b'
    evidence=next((s.strip() for s in re.split(r'[.!?\n]+',text)
                   if re.search(capacity,s,re.I) and re.search(delivery,s,re.I)
                   and re.search(r'\b(?:viest\w*|sähköpost\w*|postilaatik\w*|laatikkoni)\b',s,re.I)
                   and not re.search(r'\b(?:ei|eivät)\s+(?:palau\w*|epäonnist\w*|'
                                     r'(?:saa|saanut|saaneet)\s+(?:mitään\s+)?(?:virhe\w*|ilmoitu\w*))\b',s,re.I)),None)
    if evidence is None:return hits,None
    supported=[]
    for i,hit in enumerate(hits):
        symptoms=guides[hit['guide_id']].get('symptoms','')
        if not re.search(denial,symptoms,re.I) and all(re.search(p,symptoms,re.I) for p in (
                r'\b(?:sähköpost\w*|postilaatik\w*)\b',r'\btäy(?:nnä|tt\w*|den)\b',
                r'\b(?:estyy|epäonnist\w*|palaut\w*)\b')):
            supported.append((i,symptoms))
    if len(supported)!=1 or supported[0][0]==0:return hits,None
    chosen,symptoms=supported[0]
    return [hits[chosen]]+[h for i,h in enumerate(hits) if i!=chosen],{
        'basis':'recipient_mailbox_capacity','promoted_source':hits[chosen]['guide_id'],
        'original_category':guides[hits[0]['guide_id']]['category'],
        'request_evidence':[evidence],'source_evidence':symptoms,
        'original_order':[h['guide_id'] for h in hits]}

class VectorSearch:
    def __init__(self,guides,model=None,cache_path=None,threshold=.43):
        self.model=model if model is not None else encoder()
        self.guides={g['id']:g for g in guides};self.threshold=threshold
        self.chunks=chunks(guides,getattr(self.model,'tokenizer',None))
        signature=json.dumps({'model':MODEL_ID,'chunks':self.chunks,'schema':2},sort_keys=True,ensure_ascii=False)
        self.fingerprint=hashlib.sha256(signature.encode()).hexdigest()
        self.path=Path(cache_path) if cache_path else ROOT/'data'/'vectors.json'
        saved=None
        if self.path.exists():
            try:
                data=json.loads(self.path.read_text(encoding='utf-8'))
                if data.get('fingerprint')==self.fingerprint and len(data.get('vectors',[]))==len(self.chunks):saved=data['vectors']
            except (ValueError,OSError):pass
        if saved is None:
            vectors=self.model.encode([c['text'] for c in self.chunks],normalize_embeddings=True,show_progress_bar=False)
            self.vectors=[normalized(v) for v in vectors]
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(prefix='vectors-',suffix='.json',dir=self.path.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump({'model':MODEL_ID,'fingerprint':self.fingerprint,'vectors':self.vectors},f)
                os.replace(name,self.path)
            finally:
                if os.path.exists(name):os.unlink(name)
        else:
            try:self.vectors=[normalized(v) for v in saved]
            except (ValueError,TypeError,SearchError):raise SearchError('Vektori-indeksi on vioittunut. Poista data/vectors.json ja valmistele haku uudelleen.') from None
        dims={len(v) for v in self.vectors}
        if len(dims)!=1:raise SearchError('Vektori-indeksin ulottuvuudet eivät täsmää.')
    def query(self,text,top_k=3):
        # Keskimäärä pitkän pyynnön kaikista ikkunoista: ei hiljaista loppuosan katoamista.
        tokenizer=getattr(self.model,'tokenizer',None)
        if tokenizer:
            ids=tokenizer.encode(text,add_special_tokens=False)
            texts=[tokenizer.decode(ids[i:i+100],skip_special_tokens=True) for i in range(0,len(ids),100)]
        else:texts=[text]
        vectors=self.model.encode(texts,normalize_embeddings=True,show_progress_bar=False)
        q=normalized([sum(float(v[j]) for v in vectors)/len(vectors) for j in range(len(vectors[0]))])
        if len(q)!=len(self.vectors[0]):raise SearchError('Kyselyn ja indeksin vektorikoot eroavat. Rakenna indeksi uudelleen.')
        best={}
        for c,v in zip(self.chunks,self.vectors):
            score=sum(x*y for x,y in zip(q,v))
            if c['guide_id'] not in best or score>best[c['guide_id']]['score']:
                best[c['guide_id']]={'guide_id':c['guide_id'],'chunk_id':c['chunk_id'],'score':round(score,6),'excerpt':c['text']}
        ranked=sorted(best.values(),key=lambda x:x['score'],reverse=True)
        candidates=[h for h in ranked if h['score']>=self.threshold]
        hits=candidates[:top_k]
        category=self.guides[hits[0]['guide_id']]['category'] if hits else 'muu'
        uncertain=False
        if hits:
            other=next((h for h in ranked if self.guides[h['guide_id']]['category']!=category),None)
            uncertain=bool(other and hits[0]['score']-other['score']<.04)
            if uncertain:category='muu'
        # Ambiguity uses the original cosine ranking. Only an explicit mailbox
        # capacity relation may change category after the safety rerankers.
        hits,reranking=_rerank_same_category(text,hits,self.guides) if not uncertain else (hits,None)
        if not uncertain:
            hits,safety_reranking=_rerank_unsolicited_approval(text,hits,candidates,self.guides)
            if safety_reranking:reranking=safety_reranking
            else:
                hits,threat_reranking=_rerank_credential_threat(text,hits,self.guides)
                if threat_reranking:reranking=threat_reranking
                else:
                    hits,capacity_reranking=_rerank_mailbox_capacity(text,hits,self.guides)
                    if capacity_reranking:
                        reranking=capacity_reranking
                        category=self.guides[hits[0]['guide_id']]['category']
        return _apply_request_scope(text,{'backend':'vector','category':category,'ambiguous':uncertain,'threshold':self.threshold,'hits':hits,'best_candidate':ranked[0] if ranked else None,'fingerprint':self.fingerprint,'reranking':reranking})

_cached=None
_cached_signature=None


def hybrid_fallback(ticket,pure,guides):
    """A distinct lexical path; never alter the pure vector query or its scores.

    Only a unique source with explicit fact requirements and a specific keyword
    in an affirmed event is allowed. Broad keywords and fuzzy matches are not
    a substitute for evidence. Uncertainty and mixed negations fail closed.
    """
    if (pure.get('backend')!='vector' or pure.get('hits') or pure.get('ambiguous') or
            pure.get('scope_filter')):return pure
    best=pure.get('best_candidate') or {}
    if not isinstance(best.get('score'),(int,float)) or not isinstance(pure.get('threshold'),(int,float)):
        return pure
    if not math.isfinite(best['score']) or not math.isfinite(pure['threshold']):return pure
    if best['score']>=pure['threshold']:return pure
    from response_rules import known_facts,applicable,safety_sources
    if safety_sources(ticket,guides):return pure
    if re.search(r'["“”«»]|\b(?:jos|ehkä|luulen|mahdollisesti|onko|vai|'
                 r'ohjeessa|esimerk\w*|kuvitte\w*|oleteta\w*|harjoitu\w*|lainau\w*|'
                 r'kirjoita|laadi|käännä|suomenna|sepitä)\b|'
                 r'\ben\s+(?:tiedä|ole\s+varma|usko)\b',ticket,re.I):return pure
    failures={'toimi','onnistu','saa','löydä','avaudu','muista','pääse','käynnisty','yhdisty'}
    if any(m[1].casefold() not in failures for m in re.finditer(
            r'\b(?:en|ei|eivät|emme|eikä|älä)\s+(\w+)',ticket,re.I)):return pure
    clauses=re.split(r'[.!?;\n]+',ticket)
    facts=known_facts(ticket)
    # The event must be a user's own declarative observation, not an embedded
    # example/story/request. Only a small set of neutral prefixes is accepted.
    def affirmed(fact):
        evidence=fact['evidence']
        return any(evidence.casefold() in s.casefold() and re.fullmatch(
            r'\s*(?:(?:minä|vahingossa|tänään|eilen|juuri|äsken|nyt|aamulla)\s+)*',
            s[:s.casefold().index(evidence.casefold())],re.I) for s in clauses)
    confirmed=[f for f in facts if affirmed(f)]
    generic={'tiedosto','tiedoston','laite','laitteen','kone','tietokone','ongelma','virhe','on','ei','ole'}
    supported=[]
    for guide in guides:
        requires=guide.get('applicability',{}).get('requires',{})
        if not requires or not all(any(f['field']==key and f['value']==value for f in confirmed)
                                   for key,value in requires.items()):continue
        if not applicable(guide,facts,ticket)[0]:continue
        evidence=[f for f in confirmed if f['field'] in requires]
        matches=[keyword for keyword in guide['keywords']
                 if any(len(w)>=4 and w not in generic for w in re.findall(r'\w+',keyword.casefold()))
                 and any(re.search(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',f['evidence'],re.I) for f in evidence)]
        if matches:supported.append((guide,matches,evidence))
    if len(supported)!=1:return pure
    guide,matches,evidence=supported[0]
    candidate=dict(guide_id=guide['id'],chunk_id=None,score=None,
                   excerpt=guide.get('symptoms',guide['title']),retrieval_method='lexical_fallback',
                   matched_keywords=matches)
    result=copy.deepcopy(pure)
    result.update(hits=[candidate],category=guide['category'],ambiguous=False,
                retrieval_method='lexical_fallback',pure_vector=copy.deepcopy(pure),
                fallback=dict(applied=True,method='unique_keyword_and_confirmed_requirements',
                              matched_keywords=matches,evidence=copy.deepcopy(evidence),
                              vector_threshold_passed=False))
    # Reapply the existing service boundary; a lexical route never overrides it.
    scoped=_apply_request_scope(ticket,result)
    return scoped if scoped['hits'] else pure


def vector_search(ticket,guides,cache_path=None):
    global _cached,_cached_signature
    signature=hashlib.sha256(json.dumps(guides,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if cache_path is not None:signature+=':'+str(Path(cache_path).resolve())
    try:
        if _cached is None or signature!=_cached_signature:
            _cached=VectorSearch(guides,cache_path=cache_path);_cached_signature=signature
        return hybrid_fallback(ticket,_cached.query(ticket),guides)
    except SearchError:raise
    except Exception:raise SearchError('Vektorihaku epäonnistui. Tarkista asennus ja valmistele haku uudelleen.') from None

def keyword_search(ticket,guides):
    validate_guides(guides)
    ranked=sorted([(sum(k.casefold() in ticket.casefold() for k in g['keywords']),g) for g in guides],key=lambda x:x[0],reverse=True)
    hits=[{'guide_id':g['id'],'chunk_id':None,'score':n,'excerpt':g.get('symptoms',g['title'])} for n,g in ranked if n>0][:3]
    category=next((g['category'] for _,g in ranked if hits and g['id']==hits[0]['guide_id']),'muu')
    return _apply_request_scope(ticket,{'backend':'keyword','category':category,'ambiguous':False,'threshold':None,'hits':hits})
