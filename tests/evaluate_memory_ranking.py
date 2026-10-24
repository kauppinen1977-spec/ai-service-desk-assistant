"""Offline alias/ranking comparison with frozen new final queries and an exact Git baseline."""
import argparse
import hashlib
import inspect
import json
import os
import sqlite3
import subprocess
import sys
import types
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from evaluate_memory_environment import digest, metrics

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/ranking-evaluation'
SOURCE_FILES=('solution_memory.py','search.py','memory.html')
FIELDS=('operating_system','product','product_version')
MODES=('baseline','normalized_poc','pure_vector')


def baseline_module(name, filename):
    source=subprocess.run(['git','show','2404b9e:'+filename],check=True,capture_output=True,encoding='utf-8').stdout
    module=types.ModuleType(name)
    module.__file__=str(ROOT/filename)
    exec(compile(source,'2404b9e/'+filename,'exec'),module.__dict__)
    return module


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=('development','final'),required=True)
    args=parser.parse_args()
    fixture=ROOT/'tests/fixtures/memory_ranking_cases.json'
    data=json.loads(fixture.read_text(encoding='utf-8'))
    checkpoint=json.loads((BASE/'before.json').read_text(encoding='utf-8'))
    assert digest(fixture)==checkpoint['fixture_sha256']
    source_hashes={name:digest(ROOT/name) for name in SOURCE_FILES}
    if args.split=='final':
        freeze=json.loads((BASE/'implementation-freeze.json').read_text(encoding='utf-8'))
        assert freeze['source_hashes']==source_hashes
        assert freeze['fixture_sha256']==digest(fixture)
    run=BASE/(args.split+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir()
    db_path=run/'fictional-solutions.sqlite3'
    assert digest(ROOT/'data/solutions.sqlite3')==checkpoint['user_database_sha256']
    os.environ.update(HF_HOME=str(ROOT/'.model-cache'),HF_HUB_CACHE=str(ROOT/'.model-cache/hub'),
                      HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',
                      DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='2',
                      MKL_NUM_THREADS='2',DESK_MEMORY_DB=str(db_path))
    os.environ.pop('OPENAI_API_KEY',None)
    attempts=[]
    def guard(event,details):
        if event in ('socket.connect','socket.sendto'):
            attempts.append(event)
            raise RuntimeError('Network disabled for model evaluation')
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT))
    import desk,search
    from solution_memory import Memory,as_guide,check_environment,search_filters
    desk.CORPUS='batch1'
    old_memory=baseline_module('baseline_memory','solution_memory.py')
    old_search=baseline_module('baseline_search','search.py')
    assert inspect.signature(search.VectorSearch).parameters['threshold'].default==0.43
    print('Loading real model offline; split='+args.split,flush=True)
    model=search.encoder()
    memory=Memory(db_path)
    by_key={}
    for record in data['records']:
        row=memory.save({key:record[key] for key in ('title','problem','environment','solution',*FIELDS)})
        if record['status']!='draft':
            row=memory.transition(dict(id=row['id'],revision=row['revision'],confirmed=True,verified_by='Synteettinen testitila'),'verified')
        if record['status']=='retired':
            row=memory.transition(dict(id=row['id'],revision=row['revision'],reason='Synteettinen vanhentunut tietue'),'retired')
        by_key[record['key']]=row
    key_by_id={row['id']:key for key,row in by_key.items()}
    baseline=old_memory.Memory(db_path)
    def pack(case,result):
        hits=[dict(key=key_by_id[hit['record']['id']],score=hit['score'],environment_check=hit['environment_check']) for hit in result['hits']]
        returned=[hit['key'] for hit in hits]
        rejected=[dict(key=key_by_id[row['id']],conflicting_fields=row['conflicting_fields']) for row in result['environment_filter']['excluded']]
        compatible=[hit['key'] for hit in hits if hit['environment_check']['status']=='declared_match']
        review=[hit['key'] for hit in hits if hit['environment_check']['status']=='needs_review']
        assert all(by_key[hit['key']]['status']=='verified' for hit in hits)
        return dict(id=case['id'],group=case['group'],query=case['query'],filters=case['filters'],expected=case['expected'],
                    hits=hits,compatible=compatible,review=review,no_compatible=not compatible,
                    displayed_first_correct=bool(compatible+review) and (compatible+review)[0] in case['expected'],
                    top1_correct=bool(returned) and returned[0] in case['expected'],
                    missing=[key for key in case['expected'] if key not in returned],
                    wrong=[key for key in returned if key not in case['expected']],
                    rejected_correct=[key for key in case['expected'] if key in {row['key'] for row in rejected}],rejected=rejected)
    results={mode:[] for mode in MODES}
    comparisons=[]
    poc_matches=0
    for case in data[args.split]:
        before=baseline.search(case['query'],'vector',filters=case['filters'])
        current=memory.search(case['query'],'vector',filters=case['filters'])
        requested=search_filters(case['filters'])
        eligible=[row for row in memory.list('verified') if check_environment(row,requested)['status']!='conflict']
        diagnostic=dict(case=case['id'],reranking=None,ranking_changed=False)
        poc=dict(current)
        if eligible:
            guides=[as_guide(row) for row in eligible]
            index=search.VectorSearch(guides,model=model,cache_path=db_path.with_suffix('.vectors.json'))
            default=index.query(case['query'])
            original=old_search.VectorSearch(guides,model=model,cache_path=db_path.with_suffix('.vectors.json')).query(case['query'])
            assert default==original,'Original PoC default behavior changed'
            poc_matches+=1
            pure=index.query(case['query'],apply_poc_heuristics=False)
            assert [(hit['record']['id'],hit['score']) for hit in current['hits']]==[(hit['guide_id'],hit['score']) for hit in pure['hits']]
            assert all(a['score']>=b['score'] for a,b in zip(current['hits'],current['hits'][1:]))
            by_id={row['id']:row for row in eligible}
            poc['hits']=[dict(record=by_id[hit['guide_id']],score=hit['score'],environment_check=check_environment(by_id[hit['guide_id']],requested)) for hit in default['hits']]
            diagnostic.update(reranking=default['reranking'],ranking_changed=[hit['guide_id'] for hit in default['hits']]!=[hit['guide_id'] for hit in pure['hits']],
                              poc_order=[key_by_id[hit['guide_id']] for hit in default['hits']],pure_order=[key_by_id[hit['guide_id']] for hit in pure['hits']])
        else:
            poc['hits']=[]
        for mode,result in [('baseline',before),('normalized_poc',poc),('pure_vector',current)]:
            results[mode].append(pack(case,result))
        assert [hit['record']['id'] for hit in current['compatible_hits']]==[hit['record']['id'] for hit in current['hits'] if hit['environment_check']['status']=='declared_match']
        assert [hit['record']['id'] for hit in current['review_hits']]==[hit['record']['id'] for hit in current['hits'] if hit['environment_check']['status']=='needs_review']
        if not current['compatible_hits']:
            assert 'yhteensopivia ehdokkaita ei löytynyt' in current['message']
        comparisons.append(diagnostic)
        print(case['id'],'baseline=',[hit['key'] for hit in results['baseline'][-1]['hits']],
              'poc=',[hit['key'] for hit in results['normalized_poc'][-1]['hits']],
              'pure=',[(hit['key'],hit['score']) for hit in results['pure_vector'][-1]['hits']],flush=True)
    summary={mode:metrics(rows) for mode,rows in results.items()}
    for mode,rows in results.items():
        summary[mode].update(compatible_hits=sum(len(row['compatible']) for row in rows),review_hits=sum(len(row['review']) for row in rows),
                             no_compatible_cases=sum(row['no_compatible'] for row in rows),
                             grouped_first_correct=sum(row['displayed_first_correct'] for row in rows if row['expected']))
    with closing(sqlite3.connect(db_path)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert digest(ROOT/'data/solutions.sqlite3')==checkpoint['user_database_sha256']
    assert source_hashes=={name:digest(ROOT/name) for name in SOURCE_FILES}
    assert not attempts
    output=dict(split=args.split,baseline_commit='2404b9e',threshold=0.43,top_k=3,model=search.MODEL_ID,
                model_revision=(ROOT/'.model-cache/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/refs/main').read_text().strip(),
                source_hashes=source_hashes,fixture_sha256=digest(fixture),user_database_unchanged=True,
                user_database_sha256=checkpoint['user_database_sha256'],network_attempts=attempts,
                original_poc_equal_cases=poc_matches,metrics=summary,results=results,comparisons=comparisons)
    (run/'results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (run/'fixtures.json').write_bytes(fixture.read_bytes())
    lines=[f'# OS-aliasten ja vektorijärjestyksen arviointi: {args.split}','','Malli: '+search.MODEL_ID+'. Hakuraja 0,43, top-k 3. Offline, sama kuvitteellinen aineisto kaikissa vertailuissa.',
           '', 'Baseline = commitin 2404b9e tiukka OS-vertailu ja PoC-järjestys. Normalized PoC = korjattu OS-vertailu mutta PoC-heuristiikat mukana. Pure vector = lopullinen ratkaisumuistin haku ilman PoC-erikoisheuristiikkoja.',
           '', 'API:n hits on puhdas kosinijärjestys. Käyttöliittymä näyttää ilmoitettujen tietojen perusteella yhteensopivat ja puuttuvien tietojen vuoksi tarkistettavat erikseen, kummankin ryhmän sisällä kosinijärjestyksessä. Kumpikaan ryhmä ei takaa ratkaisun toimivuutta.',
           '', '## Mittarit','','| Mittari | Baseline | Normalized PoC | Pure vector |','|---|---:|---:|---:|']
    for key in summary['baseline']:
        lines.append('| '+key+' | '+' | '.join(str(summary[mode][key]) for mode in MODES)+' |')
    lines+=['','## Kaikki kyselyt','','| Koe | Odotettu | Baseline | Normalized PoC | Pure vector (pisteet) | Väärät pure | Puuttuvat pure | Hylätyt oikeat pure |','|---|---|---|---|---|---|---|---|']
    for old,poc,pure in zip(results['baseline'],results['normalized_poc'],results['pure_vector']):
        hits=', '.join(f'{hit["key"]} {hit["score"]:.6f}' for hit in pure['hits']) or 'ei osumia'
        lines.append(f'| {pure["id"]} | {pure["expected"]} | {[hit["key"] for hit in old["hits"]]} | {[hit["key"] for hit in poc["hits"]]} | {hits} | {pure["wrong"]} | {pure["missing"]} | {pure["rejected_correct"]} |')
    lines+=['','## Kyselyt, ryhmät ja järjestysdiagnoosi']
    for row,comparison in zip(results['pure_vector'],comparisons):
        lines+=['',f'### {row["id"]}: {row["group"]}','',row['query'],'',f'Rajaukset: `{json.dumps(row["filters"],ensure_ascii=False)}`.',
                f'Ilmoitettujen tietojen perusteella yhteensopivat: {row["compatible"]}. Tarkistettavat: {row["review"]}.',
                f'Väärät: {row["wrong"]}; puuttuvat: {row["missing"]}; hylätyt oikeat: {row["rejected_correct"]}.',
                f'Järjestysdiagnoosi: `{json.dumps(comparison,ensure_ascii=False)}`.']
        for hit in row['hits']:
            lines.append(f'- `{hit["key"]}` {hit["score"]:.6f}: `{json.dumps(hit["environment_check"],ensure_ascii=False)}`.')
    lines+=['','## Rajat','',
            'Edellinen 17 kyselyn loppuarviointi on nyt kehitysaineistoa. Uudet loppukyselyt laadittiin ennen tätä toteutusta ja niiden tiedosto lukittiin tarkistussummalla. Aineisto ja tekijä ovat samat; kyse ei ole riippumattomasta holdout-arvioinnista.',
            'Laatuvirheet ovat raportoitavia tuloksia. Hakurajaa tai kyselyjä ei soviteta tulosten perusteella. Myös heikennykset on arvioitava ennen jatkokäyttöä.',
            f'Nykyisen PoC-oletuksen ja commitin 2404b9e hakumoottorin vastaukset olivat identtiset {poc_matches} kyselyssä samalla ehdokasjoukolla.',
            f'Käyttäjän tietokanta säilyi tarkistussummalla `{checkpoint["user_database_sha256"]}`. Python-socket-yhteysyrityksiä 0; mallikirjastot offline-tilassa.',
            f'Toteutus: `{json.dumps(source_hashes)}`. Aineisto: `{digest(fixture)}`.','']
    (run/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    (BASE/(args.split+'-latest.txt')).write_text(str(run),encoding='utf-8')
    print(json.dumps(dict(report=str(run/'report.md'),metrics=summary,original_poc_equal_cases=poc_matches),ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    main()
