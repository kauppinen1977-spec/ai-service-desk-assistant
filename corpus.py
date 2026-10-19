"""Explicit local corpus manifests; legacy inputs and vector cache stay untouched."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ('legacy20', 'batch1')


def load_guides(name='legacy20', root=ROOT):
    root = Path(root).resolve()
    if name not in NAMES:
        raise ValueError('Unknown corpus')
    if name == 'legacy20':
        return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((root/'knowledge').glob('*.json'))]
    manifest = json.loads((root/'knowledge/corpora/batch1.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != '1.0' or manifest.get('corpus_id') != name:
        raise ValueError('Invalid corpus manifest')
    rows = manifest.get('sources', [])
    if len(rows) != 30 or manifest.get('source_count') != 30:
        raise ValueError('Incomplete first batch corpus')
    result = []
    for row in rows:
        path = Path(row['path'])
        if path.is_absolute() or '..' in path.parts or path.suffix != '.json':
            raise ValueError('Invalid corpus source path')
        target = root/path
        if not target.resolve().is_relative_to(root/'knowledge') or any(
                p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
                for p in [target, *target.parents] if p.is_relative_to(root)):
            raise ValueError('Corpus links/path escape forbidden')
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Corpus source fingerprint mismatch')
        guide = json.loads(raw.decode('utf-8'))
        if guide.get('id') != row['id'] or target.stem != row['id']:
            raise ValueError('Corpus source identity mismatch')
        result.append(guide)
    if len({g['id'] for g in result}) != 30:
        raise ValueError('Duplicate corpus source')
    return result


def vector_cache(name='legacy20', root=ROOT):
    if name not in NAMES:
        raise ValueError('Unknown corpus')
    return Path(root)/'data'/('vectors.json' if name == 'legacy20' else 'vectors-batch1.json')
