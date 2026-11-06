"""Conservative word-boundary search used by the optional joint-search experiment.

Uses whole tokens, a limited partitive suffix rule, and concatenation of adjacent
words for separated/compound spellings. This is not a Finnish morphological
analyser. Reuses the memory's symptom, safety and structured environment rules.
"""
import re

from search import _apply_request_scope
from solution_memory import check_environment, safety_check, search_filters, text

SYMPTOMS = {'toimi', 'toimii', 'toiminut', 'toimimaton', 'toimimattomuus'}


def tokens(value):
    return re.findall(r'[^\W_]+', value.casefold())


def variants(word):
    out = {word}
    if len(word) >= 8 and word.endswith(('ta', 'tä')):
        out.add(word[:-2])
    return out


def compounds(words):
    return {a + b for a, b in zip(words, words[1:])
            if len(a) >= 3 and len(b) >= 3 and a not in SYMPTOMS and b not in SYMPTOMS}


def boundary_search(memory, query, filters=None, *, score_environment=True):
    query = text(query, 'Ongelman kuvaus', 4000, 5)
    requested = search_filters(filters)
    stopped = safety_check(query)
    if stopped:
        return stopped
    rows = memory.list('verified')
    checks = {r['id']: check_environment(r, requested) for r in rows}
    eligible = [r for r in rows if checks[r['id']]['status'] != 'conflict']
    rejected = [{'id': r['id'], 'conflicting_fields': checks[r['id']]['conflicting_fields']}
                for r in rows if checks[r['id']]['status'] == 'conflict']
    result = {'backend': 'boundary_experiment', 'state': 'empty' if not rows else 'insufficient',
              'hits': [], 'compatible_hits': [], 'review_hits': [],
              'environment_filter': {'requested': requested, 'excluded_count': len(rejected),
                                     'excluded': rejected, 'review_hit_count': 0}}
    if re.fullmatch(r'\W*ei\s+toimi\W*', query.casefold()):
        result.update(state='clarification', message='Mikä laite, ohjelma tai toiminto ei toimi?')
        return result
    qwords = tokens(query)
    qvariants = set().union(*(variants(w) for w in qwords + list(compounds(qwords))))
    hits = []
    for row in eligible:
        title, problem, environment = (tokens(row[k]) for k in ('title', 'problem', 'environment'))
        topic_words = {w for w in title + problem if len(w) >= 3}
        all_words = topic_words | ({w for w in environment if len(w) >= 3} if score_environment else set())
        matching = {w for w in all_words if variants(w) & qvariants}
        qualifying = any(w not in SYMPTOMS and variants(w) & qvariants for w in topic_words)
        if not qualifying:
            phrase_match = any(variants(w) & qvariants for w in compounds(title) | compounds(problem))
            if phrase_match:
                matching.add('__compound__')
                qualifying = True
        if qualifying:
            hits.append({'record': row, 'score': len(matching), 'environment_check': checks[row['id']]})
    hits.sort(key=lambda h: h['score'], reverse=True)
    result['hits'] = _apply_request_scope(query, {'hits': hits[:3]})['hits']
    result['compatible_hits'] = [h for h in result['hits'] if h['environment_check']['status'] == 'declared_match']
    result['review_hits'] = [h for h in result['hits'] if h['environment_check']['status'] == 'needs_review']
    result['environment_filter']['review_hit_count'] = len(result['review_hits'])
    result['state'] = 'candidates' if result['hits'] else 'insufficient'
    return result
