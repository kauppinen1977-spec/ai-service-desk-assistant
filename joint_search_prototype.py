"""Optional experimental joint search; the application's default is unchanged.

Candidate policy is deliberately fixed before evaluation: a lexical candidate
needs cosine >= .43; a semantic-only candidate needs cosine >= .60. Lexical
agreement adds .05 to ranking, not to the published cosine. These are trial
parameters, not calibrated probabilities or a production relevance guarantee.
"""
import re

from search import SearchError, _apply_request_scope, encoder, normalized
from solution_memory import check_environment, safety_check, search_filters, text
from keyword_boundary_comparison import boundary_search


class JointSearchPrototype:
    def __init__(self, memory, model=None):
        self.memory = memory
        self.model = model
        self._signature = None
        self._vectors = None

    def search(self, query, filters=None):
        query = text(query, 'Ongelman kuvaus', 4000, 5)
        requested = search_filters(filters)
        stopped = safety_check(query)
        if stopped:
            return stopped
        records = self.memory.list('verified')
        checks = {r['id']: check_environment(r, requested) for r in records}
        rejected = [{'id': r['id'], 'conflicting_fields': checks[r['id']]['conflicting_fields']}
                    for r in records if checks[r['id']]['status'] == 'conflict']
        eligible = [r for r in records if checks[r['id']]['status'] != 'conflict']
        result = {'backend': 'joint_prototype', 'state': 'empty' if not records else 'insufficient',
                  'hits': [], 'environment_filter': {'requested': requested,
                  'excluded_count': len(rejected), 'excluded': rejected, 'review_hit_count': 0}}
        if re.fullmatch(r'\W*ei\s+toimi\W*', query.casefold()):
            result.update(state='clarification', message='Mikä laite, ohjelma tai toiminto ei toimi?')
            return result
        if not eligible:
            return result
        word_result = boundary_search(self.memory, query, filters, score_environment=False)
        lexical = {h['record']['id']: h['score'] for h in word_result['hits']}
        try:
            if self.model is None:
                self.model = encoder()
            signature = tuple((r['id'], r['title'], r['problem']) for r in eligible)
            if signature != self._signature:
                vectors = self.model.encode([r['title'] + '. ' + r['problem'] for r in eligible],
                                            normalize_embeddings=True, show_progress_bar=False)
                self._vectors = [normalized(v) for v in vectors]
                self._signature = signature
            q = normalized(self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0])
            if any(len(v) != len(q) for v in self._vectors):
                raise SearchError('Kyselyn ja indeksin vektorikoot eroavat.')
        except Exception:
            fallback = word_result
            fallback.update(backend='joint_prototype', semantic_status='error', keyword_fallback=True,
                            message='Merkityshaku ei ole käytettävissä. Näytetään sanahaun tulokset.')
            return fallback
        candidates = []
        for row, vec in zip(eligible, self._vectors):
            cosine = sum(a*b for a, b in zip(q, vec))
            lex = lexical.get(row['id'], 0)
            if cosine >= (.43 if lex else .60):
                candidates.append({'record': row, 'score': round(cosine, 6),
                                   'keyword_score': lex,
                                   'environment_check': checks[row['id']]})
        candidates.sort(key=lambda h: h['score'] + (.05 if h['keyword_score'] else 0), reverse=True)
        scoped = _apply_request_scope(query, {'hits': candidates[:3]})
        result['hits'] = scoped['hits']
        result['semantic_status'] = 'ok'
        result['keyword_fallback'] = False
        result['state'] = 'candidates' if result['hits'] else 'insufficient'
        result['environment_filter']['review_hit_count'] = sum(
            h['environment_check']['status'] == 'needs_review' for h in result['hits'])
        return result
