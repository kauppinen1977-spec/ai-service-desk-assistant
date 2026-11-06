"""Offline comparison on one temporary backup; expectations are fixed before model load."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                  DO_NOT_TRACK='1', TOKENIZERS_PARALLELISM='false')
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def guard(event, args):
    if event in ('socket.connect', 'socket.sendto'):
        raise RuntimeError('Network disabled')


sys.addaudithook(guard)
from solution_memory import Memory, check_environment, search_filters
from keyword_boundary_comparison import boundary_search
from joint_search_prototype import JointSearchPrototype
from search import encoder


CASES = [
    ('N1', 'Kohdistin ei liiku, vaikka liikutan hiirtä', ['hiiri', 'hiiri2']),
    ('N2', 'Selaimen teksti on liian pientä', ['selain']),
    ('N3', 'Grafiikkaohjaimen asetukset virheelliset', ['ohjain']),
    ('N4', 'Kuva pysähtyy ja näyttö jää jumiin', ['näyttö']),
    ('N5', 'Zoomaus on 50 prosenttia, miten suurennan?', ['selain']),
    ('N6', 'Nvidia ajuriasetukset ovat väärin', ['ohjain']),
    ('N7', 'Webkamera ei käynnisty', []),
    ('N8', 'Bluetooth-kuulokkeet eivät yhdisty', []),
    ('N9', 'Tallennuslaite on täynnä', []),
    ('N10', 'Ääniohjain pitäisi päivittää', []),
]
FILTERS = {
    'none': {},
    'lenovo': {'operating_system': 'Windows 11', 'product': 'LENOVO', 'product_version': '83GS'},
    'win10': {'operating_system': 'Windows 10'},
    'browser': {'operating_system': 'Windows 11', 'product': 'Selain'},
}


def key(row):
    title = row['title'].casefold()
    if 'näytönohjaimen' in title: return 'ohjain'
    if 'näyttö jumittaa' in title: return 'näyttö'
    if 'hiiren toimimattomuuden' in title: return 'hiiri'
    if title == 'hiiri ei toimi': return 'hiiri2'
    if 'selaimen zoomauksen' in title: return 'selain'
    return row['id']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = ROOT / 'data/solutions-soc.sqlite3'
    before = digest(original)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / 'soc.sqlite3'
        source = sqlite3.connect(original.resolve().as_uri() + '?mode=ro', uri=True)
        target = sqlite3.connect(copy)
        source.backup(target)
        source.close()
        target.close()
        memory = Memory(copy)
        records = {key(r): r for r in memory.list('verified')}
        planned = []
        for case, query, expected in CASES:
            for label, filters in FILTERS.items():
                wanted = [k for k in expected if k in records and
                          check_environment(records[k], search_filters(filters))['status'] != 'conflict']
                planned.append((case, query, label, filters, wanted))
        print('PREDECLARED', json.dumps(planned, ensure_ascii=False), flush=True)
        joint = JointSearchPrototype(memory, encoder())
        for case, query, label, filters, expected in planned:
            result = {}
            for method in ('boundary', 'joint'):
                out = boundary_search(memory, query, filters, score_environment=False) if method == 'boundary' else joint.search(query, filters)
                result[method] = {'state': out['state'], 'hits': [
                    {'key': key(h['record']), 'score': h['score']} for h in out['hits']]}
            print('RESULT', json.dumps({'case': case, 'filters': label, 'expected': expected, **result}, ensure_ascii=False), flush=True)
    print('HASH_SAME', before == digest(original), before, flush=True)


if __name__ == '__main__':
    main()
