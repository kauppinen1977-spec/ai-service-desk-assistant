"""Offline real-model development/final evaluation; quality errors are findings, not assertions."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('operating_system', 'product', 'product_version')
SOURCE_FILES = ('solution_memory.py', 'memory.html', 'search.py')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metrics(rows):
    positive = [row for row in rows if row['expected']]
    negative = [row for row in rows if not row['expected']]
    return dict(cases=len(rows), positive_cases=len(positive),
                top1_correct=sum(row['top1_correct'] for row in positive),
                expected_found_cases=sum(not row['missing'] for row in positive),
                missing_expected_cases=sum(bool(row['missing']) for row in positive),
                rejected_correct_cases=sum(bool(row['rejected_correct']) for row in positive),
                no_solution_cases=len(negative), no_solution_with_hits=sum(bool(row['hits']) for row in negative),
                no_solution_empty=sum(not row['hits'] for row in negative),
                wrong_hit_cases=sum(bool(row['wrong']) for row in rows),
                wrong_hits=sum(len(row['wrong']) for row in rows),
                review_hit_cases=sum(any(hit['environment_check']['status']=='needs_review' for hit in row['hits']) for row in rows),
                missing_record_hits=sum(bool(hit['environment_check']['missing_record_fields']) for row in rows for hit in row['hits']),
                missing_query_hits=sum(bool(hit['environment_check']['missing_query_fields']) for row in rows for hit in row['hits']),
                wrong_declared_match_hits=sum(hit['key'] in row['wrong'] and hit['environment_check']['status']=='declared_match' for row in rows for hit in row['hits']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('development','final'), required=True)
    args = parser.parse_args()
    fixtures_path = ROOT / 'tests/fixtures/memory_environment_cases.json'
    fixtures = json.loads(fixtures_path.read_text(encoding='utf-8'))
    source_hashes = {name:digest(ROOT/name) for name in SOURCE_FILES}
    base = ROOT / 'data/environment-evaluation'
    base.mkdir(parents=True, exist_ok=True)
    if args.split == 'final':
        freeze = json.loads((base/'implementation-freeze.json').read_text(encoding='utf-8'))
        assert freeze['source_hashes'] == source_hashes, 'Implementation changed after freeze'
        assert freeze['fixture_sha256'] == digest(fixtures_path), 'Evaluation fixtures changed'
    run = base / (args.split+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir()
    db_path = run/'fictional-solutions.sqlite3'
    user_db = ROOT/'data/solutions.sqlite3'
    before_hash = digest(user_db)
    os.environ.update(HF_HOME=str(ROOT/'.model-cache'), HF_HUB_CACHE=str(ROOT/'.model-cache/hub'),
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      DO_NOT_TRACK='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2',
                      MKL_NUM_THREADS='2', DESK_MEMORY_DB=str(db_path))
    os.environ.pop('OPENAI_API_KEY',None)
    network_attempts = []
    def guard(event, details):
        if event in ('socket.connect','socket.sendto'):
            network_attempts.append(event)
            raise RuntimeError('Network connections forbidden during evaluation')
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT))
    import desk
    import search
    from solution_memory import Memory
    desk.CORPUS='batch1'
    threshold=inspect.signature(search.VectorSearch).parameters['threshold'].default
    assert threshold == 0.43
    print('Loading real local model, offline; split='+args.split,flush=True)
    model=search.encoder()
    assert len(model.encode(['Paikallinen upotuskoe.'], normalize_embeddings=True, show_progress_bar=False)[0])==384
    memory=Memory(db_path)
    by_key={}
    for sample in fixtures['records']:
        record=memory.save({key:sample[key] for key in ('title','problem','environment','solution',*FIELDS)})
        if sample['status']!='draft':
            record=memory.transition(dict(id=record['id'],revision=record['revision'],confirmed=True,
                                         verified_by='Synteettinen arviointitila, ei oikea tukihyväksyntä'),'verified')
        if sample['status']=='retired':
            record=memory.transition(dict(id=record['id'],revision=record['revision'],reason='Synteettinen vanhentunut tietue'),'retired')
        by_key[sample['key']]=record
    key_by_id={record['id']:key for key,record in by_key.items()}
    def evaluate(case, use_filters):
        result=memory.search(case['query'],'vector',filters=case['filters'] if use_filters else None)
        hits=[dict(key=key_by_id[hit['record']['id']],score=hit['score'],environment_check=hit['environment_check']) for hit in result['hits']]
        returned=[hit['key'] for hit in hits]
        rejected=[dict(key=key_by_id[row['id']],conflicting_fields=row['conflicting_fields']) for row in result['environment_filter']['excluded']]
        rejected_keys={row['key'] for row in rejected}
        assert all(by_key[hit['key']]['status']=='verified' for hit in hits)
        assert all(hit['environment_check']['status']!='conflict' for hit in hits)
        return dict(id=case['id'],group=case['group'],query=case['query'],filters=case['filters'],
                    expected=case['expected'],hits=hits,state=result['state'],
                    top1_correct=bool(returned) and returned[0] in case['expected'],
                    missing=[key for key in case['expected'] if key not in returned],
                    wrong=[key for key in returned if key not in case['expected']],
                    rejected_correct=[key for key in case['expected'] if key in rejected_keys],rejected=rejected)
    before,after=[],[]
    for case in fixtures[args.split]:
        unfiltered=evaluate(case,False)
        filtered=evaluate(case,True)
        before.append(unfiltered)
        after.append(filtered)
        print(case['id'],'after=',[(hit['key'],hit['score'],hit['environment_check']['status']) for hit in filtered['hits']],
              'missing=',filtered['missing'],'rejected_correct=',filtered['rejected_correct'],flush=True)
    with closing(sqlite3.connect(db_path)) as db:
        integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    assert integrity=='ok'
    assert before_hash==digest(user_db), 'User database changed during evaluation'
    assert source_hashes=={name:digest(ROOT/name) for name in SOURCE_FILES}
    assert not network_attempts
    packages={dist.metadata['Name']:dist.version for dist in importlib.metadata.distributions()}
    revision=(ROOT/'.model-cache/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/refs/main').read_text().strip()
    output=dict(split=args.split,threshold=threshold,top_k=3,model=search.MODEL_ID,model_revision=revision,
                python=platform.python_version(),packages=packages,source_hashes=source_hashes,
                evaluator_sha256=digest(__file__),fixture_sha256=digest(fixtures_path),
                user_database_unchanged=True,user_database_sha256=before_hash,network_attempts=network_attempts,
                metrics_before=metrics(before),metrics_after=metrics(after),before=before,after=after)
    (run/'results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (run/'fixtures.json').write_bytes(fixtures_path.read_bytes())
    (run/'requirements-installed.txt').write_text(''.join(f'{name}=={value}\n' for name,value in sorted(packages.items())),encoding='utf-8')
    lines=[f'# Rakenteisten ympäristötietojen arviointi: {args.split}', '',
           f'Malli `{search.MODEL_ID}`, revisio `{revision}`, CPU, 384 ulottuvuutta. Hakuraja **{threshold}**, top-k **3**.',
           '', 'Ennen = sama aineisto ja hakukoodi ilman rakenteisia rajauksia. Jälkeen = kyselyn erikseen annetut rajaukset käytössä. Vapaa hakuteksti ja aineiston tekstit ovat samat.',
           '', 'Odotus edellyttää oikeaa oiretta, organisaatiota, käyttöjärjestelmää ja ilmoitettua versiota. Rakenteinen organisaatiorajaus ei kuulu tähän toteutukseen. Puuttuvat tiedot jäävät tarkistettaviksi. Kaikki osumat ovat ehdokkaita, eivät soveltuvuuslupauksia.',
           '', '## Mittarit', '', '| Mittari | Ilman rajauksia | Rajauksilla |', '|---|---:|---:|']
    for key,value in output['metrics_before'].items():
        lines.append(f'| {key} | {value} | {output["metrics_after"][key]} |')
    lines+=['','## Kyselykohtaiset tulokset','','| Koe | Odotettu | Ilman rajauksia (pisteet) | Rajauksilla (pisteet, tarkistus) | Hylätty oikea | Puuttuva oikea | Väärät osumat rajauksilla |','|---|---|---|---|---|---|---|']
    for old,new in zip(before,after):
        oldhits=', '.join(f'{hit["key"]} {hit["score"]:.6f}' for hit in old['hits']) or 'ei osumia'
        newhits=', '.join(f'{hit["key"]} {hit["score"]:.6f} {hit["environment_check"]["status"]}' for hit in new['hits']) or 'ei osumia'
        lines.append(f'| {new["id"]} | {", ".join(new["expected"]) or "ei sopivaa"} | {oldhits} | {newhits} | {", ".join(new["rejected_correct"]) or "–"} | {", ".join(new["missing"]) or "–"} | {", ".join(new["wrong"]) or "–"} |')
    lines+=['','## Kyselyt, puuttuvat tiedot ja hylkäykset']
    for row in after:
        lines+=['',f'### {row["id"]}: {row["group"]}','',row['query'],'',f'Rajaukset: `{json.dumps(row["filters"],ensure_ascii=False)}`.',
                f'Odotus: {row["expected"] or "ei sopivaa tietuetta"}; hylätty oikea: {row["rejected_correct"]}; puuttuva oikea: {row["missing"]}; väärät: {row["wrong"]}.']
        for hit in row['hits']:
            check=hit['environment_check']
            lines.append(f'- `{hit["key"]}` ({hit["score"]:.6f}): {check["status"]}. Tietueesta puuttuu: {check["missing_record_fields"]}. Hausta puuttuu: {check["missing_query_fields"]}.')
        lines.append(f'Hylkäykset: {row["rejected"]}.')
    lines+=['','## Rajat ja säilyminen','',
            'Kyselyt laadittiin ennen toteutusta. Loppuarvioinnin kyselyt ovat uusia mutta saman kehitystyön tekijän laatimia ja käyttävät samaa kuvitteellista tapausaineistoa; kyse ei ole riippumattomasta holdout-arvioinnista.',
            'Laatuvirheet kirjataan tuloksiksi, eikä niitä piiloteta säätämällä hakurajaa tai kyselyitä. Kirjainkoko ja välilyönnit normalisoidaan, mutta aliaksia ja versioalueita ei päätellä.',
            f'Käyttäjän tietokannan SHA-256 säilyi kokeessa: `{before_hash}`. Python-socket-yhteysyrityksiä: {len(network_attempts)}. Mallikirjastot olivat offline-tilassa. Erillisen testitietokannan eheys: {integrity}.',
            f'Toteutuksen tarkistussummat: `{json.dumps(source_hashes)}`. Aineiston SHA-256: `{output["fixture_sha256"]}`.','']
    (run/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    (base/(args.split+'-latest.txt')).write_text(str(run),encoding='utf-8')
    print(json.dumps(dict(report=str(run/'report.md'),before=output['metrics_before'],after=output['metrics_after']),ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    main()
