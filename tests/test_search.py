import math,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import desk,search
class FakeEncoder:
    def __init__(self):self.calls=0
    def encode(self,texts,**kwargs):
        self.calls+=1
        return [[1.,0.] if 'VPN' in s or 'etä' in s else [0.,1.] for s in texts]
class WordTokenizer:
    def encode(self,text,**kwargs):return text.split()
class CharacterTokenizer:
    """Deterministic token counts, including two optional special tokens."""
    def encode(self,text,add_special_tokens=True):
        tokens=list(text)
        return ['<start>']+tokens+['<end>'] if add_special_tokens else tokens

class ChunkLimitTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer=CharacterTokenizer()
        self.guide=dict(id='BUG3',title='T',symptoms='S',category='muu',
                        version='test',keywords=['test'],steps=['ok'],
                        needs_human=False,follow_up='q')
        self.limit=20

    def test_bug3_oversized_word_at_start(self):
        self.guide['steps']=['x'*14]
        with self.assertRaisesRegex(search.SearchError,'Yksittäinen sana ylittää pilkkomisrajan'):
            search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)

    def test_bug3_oversized_word_after_short_word(self):
        self.guide['steps']=['ok '+'x'*14]
        with self.assertRaisesRegex(search.SearchError,'Yksittäinen sana ylittää pilkkomisrajan'):
            search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)

    def test_bug3_oversized_word_in_middle(self):
        self.guide['steps']=['ok '+'x'*14+' end']
        with self.assertRaisesRegex(search.SearchError,'Yksittäinen sana ylittää pilkkomisrajan'):
            search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)

    def test_bug3_exact_token_limit_is_accepted(self):
        self.guide['steps']=['ok '+'x'*13]
        parts=search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)
        step_parts=[p for p in parts if p['chunk_id'].startswith('BUG3:1:')]
        self.assertEqual([p['text'] for p in step_parts],['T. S ok','T. S '+'x'*13])
        self.assertEqual(len(self.tokenizer.encode(step_parts[-1]['text'])),self.limit)
        self.assertTrue(all(len(self.tokenizer.encode(p['text']))<=self.limit for p in parts))

    def test_bug3_header_uses_token_budget(self):
        self.guide['steps']=['aaaa bbbb']
        parts=search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)
        self.assertEqual([p['text'] for p in parts if p['chunk_id'].startswith('BUG3:1:')],
                         ['T. S aaaa bbbb'])
        for field,value in [('title','Header'),('symptoms','Sympto')]:
            with self.subTest(field=field):
                guide=dict(self.guide,**{field:value})
                parts=search.chunks([guide],self.tokenizer,max_tokens=self.limit)
                prefix='Header. S ' if field=='title' else 'T. Sympto '
                self.assertEqual([p['text'] for p in parts if p['chunk_id'].startswith('BUG3:1:')],
                                 [prefix+'aaaa',prefix+'bbbb'])
                self.assertTrue(all(len(self.tokenizer.encode(p['text']))<=self.limit for p in parts))

    def test_bug3_special_tokens_use_token_budget(self):
        self.guide['steps']=['aaaaaaa bbbbbb']
        unsplit='T. S aaaaaaa bbbbbb'
        self.assertEqual(len(self.tokenizer.encode(unsplit,add_special_tokens=False)),19)
        self.assertEqual(len(self.tokenizer.encode(unsplit,add_special_tokens=True)),21)
        parts=search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)
        self.assertEqual([p['text'] for p in parts if p['chunk_id'].startswith('BUG3:1:')],
                         ['T. S aaaaaaa','T. S bbbbbb'])
        self.assertTrue(all(len(self.tokenizer.encode(p['text']))<=self.limit for p in parts))

    def test_bug3_content_and_word_order_are_preserved(self):
        self.guide['steps']=['one two three four five six seven eight nine ten one two',
                             'alpha beta gamma delta epsilon']
        self.guide['follow_up']='repeat this question once'
        parts=search.chunks([self.guide],self.tokenizer,max_tokens=self.limit)
        bodies=[self.guide['symptoms']]+self.guide['steps']+[self.guide['follow_up']]
        self.assertGreater(len(parts),len(bodies))
        for section,body in enumerate(bodies):
            section_parts=[p for p in parts if p['chunk_id'].startswith(f'BUG3:{section}:')]
            self.assertTrue(section_parts)
            self.assertEqual([p['chunk_id'] for p in section_parts],
                             [f'BUG3:{section}:{i}' for i in range(len(section_parts))])
            self.assertEqual(' '.join(p['text'][len('T. S '):] for p in section_parts),body)
        self.assertEqual(len({p['chunk_id'] for p in parts}),len(parts))
        for part in parts:
            self.assertTrue(part['text'].startswith('T. S '))
            self.assertLessEqual(len(self.tokenizer.encode(part['text'])),self.limit)
            self.assertEqual(part['guide_id'],'BUG3')
            self.assertEqual(part['category'],'muu')
            self.assertEqual(part['version'],'test')

    def test_bug3_without_tokenizer_counts_words(self):
        words=['one','x'*1000,'two','three','four','five','six','seven','eight','nine','ten']
        self.guide['steps']=[' '.join(words)]
        parts=search.chunks([self.guide],max_tokens=12)
        step_parts=[p for p in parts if p['chunk_id'].startswith('BUG3:1:')]
        self.assertEqual(len(step_parts),2)
        self.assertEqual(len(step_parts[0]['text'].split()),12)
        self.assertTrue(all(len(p['text'].split())<=12 for p in parts))
        reconstructed=' '.join(p['text'][len('T. S '):] for p in step_parts)
        self.assertEqual(reconstructed.split(),words)
        self.assertGreater(len(step_parts[0]['text']),12)

class RerankingTests(unittest.TestCase):
    """Controlled cosine scores; no embedding model, cache writes or benchmark run."""
    @classmethod
    def setUpClass(cls):
        cls.guides={g['id']:g for g in desk.guides()}

    def index(self,ids,scores=None):
        scores=scores or [.75,.70,.55][:len(ids)]
        index=object.__new__(search.VectorSearch)
        index.guides={gid:self.guides[gid] for gid in ids}
        index.model=SimpleNamespace(encode=Mock(return_value=[[1.,0.]]))
        index.threshold=.43
        index.fingerprint='synthetic-no-model'
        index.chunks=[{'guide_id':gid,'chunk_id':gid+':synthetic','text':'synthetic'} for gid in ids]
        index.vectors=[[score,math.sqrt(1-score**2)] for score in scores]
        return index

    def promoted(self,ticket,ids,expected,scores=None):
        index=self.index(ids,scores)
        result=index.query(ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],expected)
        self.assertEqual({h['guide_id']:h['score'] for h in result['hits']},
                         dict(zip(ids,scores or [.75,.70,.55][:len(ids)])))
        self.assertEqual(result['category'],index.guides[ids[0]]['category'])
        self.assertFalse(result['ambiguous'])
        self.assertEqual(result['best_candidate']['guide_id'],ids[0])
        self.assertEqual(result['reranking']['original_order'],ids)
        self.assertEqual(result['reranking']['promoted_source'],expected[0])
        self.assertTrue(result['reranking']['matched_terms'])
        index.model.encode.assert_called_once()

    def unchanged(self,ticket,ids,scores=None,**kwargs):
        result=self.index(ids,scores).query(ticket,**kwargs)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         [gid for gid,score in zip(ids,scores or [.75,.70,.55][:len(ids)])
                          if score>=.43][:kwargs.get('top_k',3)])
        self.assertFalse(result.get('reranking'))
        return result

    def test_f02_forgotten_password(self):
        self.promoted('En muista työtilini salasanaa kirjautumiseen.',
                      ['IAM-004','IAM-002'],['IAM-002','IAM-004'],[.537639,.516461])

    def test_f06_suspicious_login_link(self):
        self.promoted('Sain sähköpostissa epäilyttävän kirjautumislinkin.',
                      ['MAIL-001','MAIL-003','MAIL-002'],['MAIL-003','MAIL-001','MAIL-002'],
                      [.647303,.632042,.550625])

    def test_f10_wireless_join_failure(self):
        self.promoted('Langattomaan verkkoon liittyminen epäonnistuu.',
                      ['NET-004','NET-002','MAIL-001'],['NET-002','NET-004','MAIL-001'],
                      [.657897,.631348,.514405])

    def test_f12_administrator_rights(self):
        self.promoted('Tarvitsen ylläpitäjän oikeudet työkoneelle.',
                      ['IAM-006','IAM-005','IAM-001'],['IAM-001','IAM-006','IAM-005'],
                      [.660943,.632541,.604788])

    def test_locked_account_over_password(self):
        self.promoted('Työtili lukittui toistuvien kirjautumisyritysten jälkeen.',
                      ['IAM-002','IAM-004'],['IAM-004','IAM-002'])

    def test_general_email_failure_over_suspicious_message(self):
        self.promoted('Outlook ei lähetä eikä vastaanota sähköpostia.',
                      ['MAIL-003','MAIL-001','MAIL-002'],['MAIL-001','MAIL-003','MAIL-002'])

    def test_complete_internet_outage_over_wireless(self):
        self.promoted('Internet ei toimi millään sivulla.',
                      ['NET-002','NET-004','MAIL-001'],['NET-004','NET-002','MAIL-001'])

    def test_onboarding_over_administrator_rights(self):
        self.promoted('Uusi työntekijä aloittaa ja tarvitsee tilin.',
                      ['IAM-001','IAM-005','IAM-006'],['IAM-005','IAM-001','IAM-006'])

    def test_offboarding_over_administrator_rights(self):
        self.promoted('Työsuhde päättyy ja käyttöoikeudet on suljettava.',
                      ['IAM-001','IAM-006','IAM-005'],['IAM-006','IAM-001','IAM-005'])

    def test_generic_email_and_missing_evidence_keep_original_order(self):
        self.unchanged('Sähköpostin vastaanotto ei onnistu.',
                       ['MAIL-001','MAIL-003','MAIL-002'])
        self.unchanged('Tarvitsen apua kirjautumiseen.',['IAM-004','IAM-002'])

    def test_negation_uncertainty_and_conflicting_topics_do_not_override_cosine(self):
        for ticket in ['En ole unohtanut salasanaa, tili on lukittu.',
                       'Unohdin salasanan ja tili lukittui.',
                       'Ehkä salasana on unohtunut.',
                       'Onko salasana unohtunut vai tili lukittu?']:
            with self.subTest(ticket=ticket):
                self.unchanged(ticket,['IAM-004','IAM-002'])
        self.unchanged('Viesti ei ole epäilyttävä. Outlook ei vastaanota sähköpostia.',
                       ['MAIL-001','MAIL-003','MAIL-002'])
        self.unchanged('Langaton verkko ei ole ongelma. Internet ei toimi.',
                       ['NET-004','NET-002','MAIL-001'])
        self.unchanged('En tarvitse ylläpitäjän oikeuksia; uusi työntekijä aloittaa.',
                       ['IAM-005','IAM-001','IAM-006'])

    def test_other_category_slots_and_original_classification_are_preserved(self):
        self.promoted('Langattomaan verkkoon liittyminen epäonnistuu.',
                      ['NET-004','MAIL-001','NET-002'],['NET-002','MAIL-001','NET-004'],
                      [.75,.65,.64])
        result=self.unchanged('Tarvitsen ylläpitäjän oikeudet.',
                              ['MAIL-001','IAM-001','IAM-005'])
        self.assertEqual(result['category'],'sähköposti')

    def test_cross_category_ambiguity_is_not_overridden(self):
        result=self.unchanged('Tarvitsen ylläpitäjän oikeudet.',
                              ['MAIL-001','IAM-001','MAIL-003'],[.70,.68,.55])
        self.assertTrue(result['ambiguous'])
        self.assertEqual(result['category'],'muu')

    def test_threshold_top_k_and_rejection_are_unchanged(self):
        self.unchanged('Tarvitsen ylläpitäjän oikeudet.',
                       ['IAM-006','IAM-005','IAM-001'],[.70,.60,.42])
        self.unchanged('Tarvitsen ylläpitäjän oikeudet.',
                       ['IAM-006','IAM-001'],top_k=1)
        result=self.unchanged('Tarvitsen ylläpitäjän oikeudet.',
                              ['IAM-006','IAM-001'],[.42,.41])
        self.assertEqual(result['category'],'muu')

    def test_reranking_uses_metadata_not_source_identifiers(self):
        index=self.index(['IAM-004','IAM-002'])
        index.guides={name:dict(guide,id=name) for name,guide in zip(['A','B'],index.guides.values())}
        for part,name in zip(index.chunks,['A','B']):part['guide_id']=name
        result=index.query('Salasana on unohtunut.')
        self.assertEqual([h['guide_id'] for h in result['hits']],['B','A'])


class MailboxCapacityTests(unittest.TestCase):
    """Recipient-capacity regressions with controlled vectors, never model inference."""
    ticket=('Minulle lähettävä kollega saa ilmoituksen, ettei vastaanottajalle mahdu lisää viestejä. '
            'Omassa läppärissä on 120 gigatavua vapaana. Mitä tilaa pitäisi tarkistaa?')

    @classmethod
    def setUpClass(cls):
        cls.guides={g['id']:g for g in desk.guides()}

    def index(self,scores=None):
        return RerankingTests.index(self,['DEVICE-003','MAIL-001','MAIL-002'],
                                   scores or [.615266,.532495,.515283])

    def assert_unchanged(self,ticket,index=None):
        result=(index or self.index()).query(ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['DEVICE-003','MAIL-001','MAIL-002'])
        self.assertEqual(result['category'],'laitteet')
        self.assertFalse(result['reranking'])
        return result

    def test_u13_recipient_capacity_corrects_ranking_and_category(self):
        index=self.index()
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['MAIL-002','DEVICE-003','MAIL-001'])
        self.assertEqual([h['score'] for h in result['hits']],[.515283,.615266,.532495])
        self.assertEqual(result['category'],'sähköposti')
        self.assertFalse(result['ambiguous'])
        self.assertEqual(result['best_candidate']['guide_id'],'DEVICE-003')
        self.assertEqual(result['reranking']['basis'],'recipient_mailbox_capacity')
        self.assertEqual(result['reranking']['original_category'],'laitteet')
        self.assertTrue(result['reranking']['request_evidence'])
        self.assertTrue(result['reranking']['source_evidence'])
        index.model.encode.assert_called_once()

    def test_recipient_capacity_paraphrases(self):
        for ticket in ['Lähettäjä saa virheen, että vastaanottajan postilaatikko on täynnä eikä viestiä voi toimittaa.',
                       'Kollegan lähettämä sähköposti palautuu, koska vastaanottajan kiintiö on täyttynyt.',
                       'Vastaanottajalle ei mahdu uusia viestejä; lähetys palautuu.',
                       'Minulle lähetetty viesti palautuu lähettäjälle, koska laatikkoni on täynnä.',
                       'Postipalvelu ilmoittaa viestin palautuneen: vastaanottajalle ei ole tilaa uusille viesteille.']:
            with self.subTest(ticket=ticket):
                result=self.index().query(ticket)
                self.assertEqual(result['hits'][0]['guide_id'],'MAIL-002')
                self.assertEqual(result['category'],'sähköposti')

    def test_free_local_space_is_background_not_a_fixed_numeric_rule(self):
        for background in ['', 'Koneella on 8 gigatavua vapaana.', 'Levyllä on runsaasti vapaata tilaa.']:
            with self.subTest(background=background):
                result=self.index().query(self.ticket.split('. ')[0]+'. '+background)
                self.assertEqual(result['hits'][0]['guide_id'],'MAIL-002')

    def test_real_local_disk_exhaustion_is_not_mailbox_capacity(self):
        for ticket in ['C-asemalla on 200 megatavua vapaana ja liitetiedoston tallennus epäonnistuu. Sähköposti muuten toimii.',
                       'Kone ilmoittaa levyn olevan täynnä. En saa tallennettua sähköpostin liitettä.',
                       'Vastaanottajan koneen levy on täynnä ja viestien paikallinen tallennus epäonnistuu.',
                       'Postilaatikossa on tilaa. Tietokoneen levy on täynnä.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_ordinary_mail_failure_is_not_a_capacity_diagnosis(self):
        for ticket in ['Viestit jäävät jonoon eikä lähettäminen onnistu. Vastaanottaja ei saa niitä.',
                       'Viestin toimitus epäonnistuu tuntemattomaan osoitteeseen.',
                       'Vastaanottaja kertoo postilaatikon koon, mutta sähköposti toimii.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_capacity_denials_are_not_positive_evidence(self):
        for ticket in ['Lähettäjä saa ilmoituksen, ettei vastaanottajan postilaatikko ole täynnä. Viesti ei silti mene perille.',
                       'Vastaanottajan kiintiö ei ole täyttynyt, mutta sähköposti palautuu.',
                       'Vastaanottajalle mahtuu lisää viestejä, mutta toimitus epäonnistuu.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_two_actual_capacity_problems_remain_conservative(self):
        for local_problem in ['Tietokoneen levy on täynnä ja tallennus epäonnistuu.',
                              'C-asemalla on tilaa vain vähän ja liitteen tallennus epäonnistuu.']:
            with self.subTest(local_problem=local_problem):
                self.assert_unchanged(self.ticket+' '+local_problem)

    def test_uncertainty_translation_and_hypothetical_requests_do_not_override(self):
        for prefix in ['Ehkä ', 'En tiedä, ', 'En ole varma, ', 'Jos ', 'Käännä englanniksi: ']:
            with self.subTest(prefix=prefix):self.assert_unchanged(prefix+self.ticket)

    def test_explicit_retraction_is_respected(self):
        for ending in ['Tuo ei pidä paikkaansa.', 'Vastaanottajan postilaatikko ei ole täynnä.']:
            with self.subTest(ending=ending):self.assert_unchanged(self.ticket+' '+ending)

    def test_no_unrelated_clause_combination(self):
        self.assert_unchanged('Kollega saa virheen viestin lähetyksessä. '
                              'Vastaanottajan tietokoneen levy on täynnä. Oma postilaatikko toimii.')

    def test_source_ids_titles_and_keywords_are_not_routing_rules(self):
        index=self.index()
        names={gid:'source-'+str(i) for i,gid in enumerate(index.guides)}
        index.guides={names[gid]:dict(g,id=names[gid],title='Ohje',keywords=['yleinen'])
                      for gid,g in index.guides.items()}
        for chunk in index.chunks:chunk['guide_id']=names[chunk['guide_id']]
        result=index.query(self.ticket)
        self.assertEqual(result['hits'][0]['guide_id'],names['MAIL-002'])
        self.assertEqual(result['category'],index.guides[names['MAIL-002']]['category'])

    def test_source_requires_a_mail_delivery_capacity_symptom(self):
        for symptoms in ['Sähköposti ei toimi.', 'Tietokoneen levy on täynnä.',
                         'Sähköpostilaatikko ei ole täynnä ja viestit kulkevat.']:
            with self.subTest(symptoms=symptoms):
                index=self.index()
                index.guides['MAIL-002']=dict(index.guides['MAIL-002'],symptoms=symptoms)
                self.assert_unchanged(self.ticket,index)

    def test_multiple_supported_sources_do_not_force_selection(self):
        index=self.index()
        index.guides['MAIL-001']=dict(index.guides['MAIL-001'],symptoms=index.guides['MAIL-002']['symptoms'])
        self.assert_unchanged(self.ticket,index)

    def test_threshold_and_top_k_are_preserved(self):
        result=self.index([.70,.55,.42]).query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['DEVICE-003','MAIL-001'])
        self.assertEqual(result['category'],'laitteet')
        self.assertFalse(result['reranking'])
        result=self.index().query(self.ticket,top_k=1)
        self.assertEqual([h['guide_id'] for h in result['hits']],['DEVICE-003'])
        self.assertEqual(result['category'],'laitteet')

    def test_cross_category_uncertainty_is_not_removed(self):
        result=self.index([.60,.58,.57]).query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['DEVICE-003','MAIL-001','MAIL-002'])
        self.assertTrue(result['ambiguous'])
        self.assertEqual(result['category'],'muu')
        self.assertFalse(result['reranking'])

    def test_denied_delivery_failure_is_not_positive_evidence(self):
        for ticket in ['Vastaanottajan kiintiö on täyttynyt, mutta viesti ei palaudu ja toimitus onnistuu.',
                       'Lähettäjä ei saa virhettä: vastaanottajan postilaatikko on täynnä.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_nonmail_recipient_quota_does_not_select_mail_instructions(self):
        self.assert_unchanged('Lähettäjä saa virheen tiedostonsiirrossa, koska vastaanottajan kiintiö on täyttynyt.')

    def test_existing_security_promotions_take_priority(self):
        cases=[(UnsolicitedApprovalTests.ticket,['IAM-004','IAM-003','MAIL-002'],'IAM-003'),
               (CredentialThreatTests.ticket,['MAIL-001','MAIL-003','MAIL-002'],'MAIL-003')]
        for ticket,ids,expected in cases:
            with self.subTest(expected=expected):
                index=RerankingTests.index(self,ids,[.70,.65,.55])
                result=index.query(ticket+' '+self.ticket)
                self.assertEqual(result['hits'][0]['guide_id'],expected)
                self.assertEqual(result['category'],index.guides[expected]['category'])
                self.assertNotEqual(result['reranking']['basis'],'recipient_mailbox_capacity')


class CredentialThreatTests(unittest.TestCase):
    """Controlled vectors; no embedding model or evaluation run."""
    ticket=('Palkanlaskennalta näyttävä lähettäjä uhkaa maksun viivästymisellä '
            'ja käskee vahvistamaan tunnukseni viestin osoitteessa. En ole avannut osoitetta.')

    @classmethod
    def setUpClass(cls):
        cls.guides={g['id']:g for g in desk.guides()}

    def index(self,scores=None):
        return RerankingTests.index(self,['MAIL-001','MAIL-003','MAIL-004'],
                                   scores or [.643467,.629219,.563165])

    def assert_unchanged(self,ticket,index=None):
        result=(index or self.index()).query(ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['MAIL-001','MAIL-003','MAIL-004'])
        self.assertFalse(result['reranking'])
        return result

    def test_u11_credential_threat_promotes_safety_source(self):
        index=self.index()
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['MAIL-003','MAIL-001','MAIL-004'])
        self.assertEqual([h['score'] for h in result['hits']],[.629219,.643467,.563165])
        self.assertEqual(result['best_candidate']['guide_id'],'MAIL-001')
        self.assertEqual(result['category'],'sähköposti')
        self.assertFalse(result['ambiguous'])
        self.assertEqual(result['reranking']['basis'],'credential_threat_in_message')
        self.assertTrue(result['reranking']['request_evidence'])
        self.assertTrue(result['reranking']['source_evidence'])
        index.model.encode.assert_called_once()

    def test_threat_paraphrases_do_not_need_phishing_keywords(self):
        for ticket in ['Sähköposti uhkaa tilin sulkemisella ja vaatii syöttämään salasanan linkin sivulle.',
                       'Viesti uhkaa palkan viivästymisellä ja pyytää vahvistamaan tunnukset linkin kautta.']:
            with self.subTest(ticket=ticket):
                self.assertEqual(self.index().query(ticket)['hits'][0]['guide_id'],'MAIL-003')

    def test_exposure_status_does_not_negate_the_threat(self):
        incident=self.ticket.split('. En ole')[0]+'. '
        for status in ['En ole avannut osoitetta.','En ole syöttänyt tunnuksia.',
                       'Avasin linkin, mutta en antanut salasanaa.']:
            with self.subTest(status=status):
                self.assertEqual(self.index().query(incident+status)['hits'][0]['guide_id'],'MAIL-003')

    def test_ordinary_mail_failures_are_not_credential_threats(self):
        for ticket in ['Outlook ei lähetä eikä vastaanota sähköpostia.',
                       'Saapuneita viestejä tulee, mutta omat lähetykseni jäävät jonoon. Niissä ei pyydetä tunnuksia eikä ole outoja osoitteita.',
                       'Sähköpostiviesti ei avaudu, enkä ole vaihtanut salasanaa.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_negated_demands_and_threats_do_not_promote(self):
        for ticket in ['Viesti ei uhkaa maksun viivästymisellä eikä käske vahvistamaan tunnuksia osoitteessa.',
                       'Viesti ei pyydä vahvistamaan tunnuksia linkissä. Maksu voi viivästyä.',
                       'Viesti uhkaa maksun viivästymisellä, mutta ei vaadi syöttämään salasanaa linkissä.',
                       'Viesti uhkaa maksun viivästymisellä ja käskee olemaan vahvistamatta tunnuksia osoitteessa. En ole avannut sitä.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_payment_notice_or_password_mention_alone_is_not_enough(self):
        for ticket in ['Palkanlaskennan lähettäjä kertoo maksun viivästymisestä. Tunnukseni toimivat normaalisti.',
                       'Sähköposti pyytää vahvistamaan kokouksen ajan ennen maksun eräpäivää.',
                       'Sähköposti käskee vahvistamaan tunnukset osoitteessa.',
                       'Sovellus uhkaa sulkeutua, jos levy täyttyy. Salasana on tallessa.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_hypothetical_uncertain_and_translation_requests_remain_conservative(self):
        for prefix in ['Ehkä ', 'En tiedä, ', 'En ole varma, ', 'Jos ', 'Käännä englanniksi: ']:
            with self.subTest(prefix=prefix):self.assert_unchanged(prefix+self.ticket)

    def test_source_ids_titles_and_keywords_are_not_routing_rules(self):
        index=self.index()
        names={gid:'source-'+str(i) for i,gid in enumerate(index.guides)}
        index.guides={names[gid]:dict(g,id=names[gid],title='Ohje',keywords=['yleinen'])
                      for gid,g in index.guides.items()}
        for chunk in index.chunks:chunk['guide_id']=names[chunk['guide_id']]
        self.assertEqual(index.query(self.ticket)['hits'][0]['guide_id'],names['MAIL-003'])

    def test_source_requires_both_link_safety_and_security_reporting(self):
        for steps in [['Älä avaa linkkejä tai liitteitä.'],
                      ['Ilmoita viestistä organisaation tietoturvakanavalla.'],
                      ['Avaa linkki ja ilmoita viestistä tietoturvakanavalla.']]:
            with self.subTest(steps=steps):
                index=self.index()
                index.guides['MAIL-003']=dict(index.guides['MAIL-003'],steps=steps)
                self.assert_unchanged(self.ticket,index)

    def test_multiple_matching_sources_do_not_force_a_choice(self):
        index=self.index()
        index.guides['MAIL-004']=dict(index.guides['MAIL-004'],steps=index.guides['MAIL-003']['steps'])
        self.assert_unchanged(self.ticket,index)

    def test_original_cross_category_ambiguity_is_preserved(self):
        index=self.index()
        index.guides['MAIL-004']=dict(index.guides['MAIL-004'],category='laitteet')
        index.vectors[2]=[.63,math.sqrt(1-.63**2)]
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['MAIL-001','MAIL-004','MAIL-003'])
        self.assertFalse(result['reranking'])
        self.assertTrue(result['ambiguous'])
        self.assertEqual(result['category'],'muu')

    def test_other_category_slot_and_cosine_scores_are_preserved(self):
        index=self.index([.70,.64,.65])
        index.guides['MAIL-004']=dict(index.guides['MAIL-004'],category='laitteet')
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['MAIL-003','MAIL-004','MAIL-001'])
        self.assertEqual([h['score'] for h in result['hits']],[.64,.65,.70])
        self.assertEqual(result['category'],'sähköposti')

    def test_below_threshold_and_unreturned_sources_are_not_injected(self):
        result=self.index([.70,.42,.55]).query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['MAIL-001','MAIL-004'])
        self.assertFalse(result['reranking'])
        result=self.index().query(self.ticket,top_k=1)
        self.assertEqual([h['guide_id'] for h in result['hits']],['MAIL-001'])
        self.assertFalse(result['reranking'])

    def test_other_winning_category_cannot_be_overridden(self):
        index=self.index([.75,.65,.55])
        index.guides['MAIL-001']=dict(index.guides['MAIL-001'],category='laitteet')
        result=self.assert_unchanged(self.ticket,index)
        self.assertEqual(result['category'],'laitteet')

    def test_explicit_retraction_or_denial_in_another_sentence_prevents_promotion(self):
        for ending in ['Tuo ei pidä paikkaansa.',
                       'Todellisuudessa viesti ei vaadi tunnuksia eikä uhkaa mitään.']:
            with self.subTest(ending=ending):self.assert_unchanged(self.ticket+' '+ending)

    def test_training_example_is_not_an_actual_incident(self):
        self.assert_unchanged('Tämä on esimerkkiteksti koulutukseen: '+self.ticket)

    def test_unrelated_sentences_do_not_combine_into_incident_evidence(self):
        self.assert_unchanged('Lähettäjä ilmoittaa maksun viivästymisestä. '
                              'IT-tuen ohje käskee vahvistamaan salasanan organisaation osoitteessa. '
                              'En ole avannut ohjelmaa.')

    def test_remaining_classification_failures_are_unchanged(self):
        cases=[
            ('Olen ollut talossa viisi vuotta. Mittalaitteen apuohjelma vaatii korotettua suoritusta, eikä esihenkilö ole vielä käsitellyt asiaa. Miten etenen?',
             ['IAM-001','MAIL-001'],[.43719,.42],['IAM-001'],'muu',True),
            ('Maanantaina meille tulevan harjoittelijan pitäisi päästä myyntijärjestelmään. HR on ilmoittanut aloituspäivän, mutta esihenkilön vahvistus puuttuu.',
             ['IAM-005','MAIL-004','IAM-006'],[.521839,.518812,.469428],['IAM-005','MAIL-004','IAM-006'],'muu',True)]
        for ticket,ids,scores,expected,category,ambiguous in cases:
            with self.subTest(ticket=ticket):
                result=RerankingTests.index(self,ids,scores).query(ticket)
                self.assertEqual([h['guide_id'] for h in result['hits']],expected)
                self.assertEqual(result['category'],category)
                self.assertEqual(result['ambiguous'],ambiguous)
                self.assertFalse(result['reranking'])


class UnsolicitedApprovalTests(unittest.TestCase):
    """Synthetic scores: no model inference or benchmark evaluation."""
    ticket=('Puhelimeni pyytää kuittaamaan sisäänpääsyjä, vaikka en ole avannut '
            'mitään työpalvelua. Voinko hyväksyä ne, jotta ilmoitukset loppuvat?')

    @classmethod
    def setUpClass(cls):
        cls.guides={g['id']:g for g in desk.guides()}

    def index(self):
        # Only the top three and target score come from diagnostics; positions
        # four and five are controlled distractors, not measured source ranks.
        return RerankingTests.index(self,
            ['IAM-004','IAM-005','MAIL-001','IAM-002','IAM-006','IAM-003'],
            [.594669,.557691,.554267,.54,.53,.52609])

    def assert_unchanged(self,ticket,index=None):
        result=(index or self.index()).query(ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['IAM-004','IAM-005','MAIL-001'])
        self.assertFalse(result['reranking'])
        return result

    def test_u03_sixth_candidate_can_enter_top_three(self):
        index=self.index()
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],
                         ['IAM-003','IAM-004','MAIL-001'])
        self.assertEqual(result['hits'][0]['score'],.52609)
        self.assertEqual(result['best_candidate']['guide_id'],'IAM-004')
        self.assertEqual(result['category'],'käyttöoikeudet')
        self.assertFalse(result['ambiguous'])
        self.assertEqual(result['reranking']['basis'],'unsolicited_authentication_approval')
        self.assertTrue(result['reranking']['request_evidence'])
        self.assertIn('et itse aloittanut',result['reranking']['source_evidence'])
        index.model.encode.assert_called_once()

    def test_paraphrases_without_mfa_or_case_identifiers(self):
        for ticket in ['Saan kirjautumispyyntöjä, joita en itse aloittanut. Ne pyytävät hyväksymään kirjautumisen.',
                       'Puhelin pyytää vahvistamaan kirjautumisen. En ole itse käynnistänyt kirjautumista.']:
            with self.subTest(ticket=ticket):
                self.assertEqual(self.index().query(ticket)['hits'][0]['guide_id'],'IAM-003')

    def test_user_initiated_login_does_not_trigger_promotion(self):
        self.assert_unchanged('Puhelin pyytää kuittaamaan kirjautumisen, jonka aloitin itse. Voinko hyväksyä sen?')

    def test_uncertainty_and_alternatives_remain_conservative(self):
        for prefix in ['Ehkä ', 'En tiedä, ', 'En ole varma, ', 'Mahdollisesti ']:
            with self.subTest(prefix=prefix):self.assert_unchanged(prefix+self.ticket)
        self.assert_unchanged('En muista, aloittiko joku kirjautumisen vai enkö itse aloittanut. Puhelin pyytää hyväksymään sen.')

    def test_negated_request_is_not_positive_evidence(self):
        self.assert_unchanged('Puhelin ei pyydä hyväksymään kirjautumista, en ole avannut työpalvelua.')

    def test_phone_replacement_or_missing_notification_does_not_trigger(self):
        for ticket in ['Uusi puhelin ei saa kirjautumisen hyväksymispyyntöä.',
                       'Puhelin ei pyydä kuittaamaan kirjautumista. Aloitin kirjautumisen itse.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_manager_approval_and_password_or_lock_problems_do_not_trigger(self):
        result=self.index().query('Esihenkilö pyytää hyväksymään uuden työntekijän aloituksen.')
        self.assertEqual(result['hits'][0]['guide_id'],'IAM-005')
        self.assertEqual(result['reranking']['basis'],'unique_title_or_keyword_term')
        for ticket in ['En ole avannut työpalvelua, koska salasana unohtui.',
                       'Tili on lukittu, vaikka en ole avannut työpalvelua.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_phishing_and_negated_phishing_are_not_authentication_pushes(self):
        for ticket in ['Palkanlaskennalta näyttävä viesti käskee vahvistamaan tunnukseni. En ole avannut osoitetta.',
                       'Viestit jäävät jonoon. Niissä ei pyydetä tunnuksia eikä ole outoja osoitteita.']:
            with self.subTest(ticket=ticket):self.assert_unchanged(ticket)

    def test_translation_request_is_not_a_support_incident(self):
        self.assert_unchanged('Käännä englanniksi: '+self.ticket)

    def test_threshold_and_cross_category_ambiguity_are_preserved(self):
        index=self.index();index.vectors[-1]=[.42,math.sqrt(1-.42**2)]
        self.assert_unchanged(self.ticket,index)
        index=self.index();index.vectors[2]=[.58,math.sqrt(1-.58**2)]
        result=index.query(self.ticket)
        self.assertEqual([h['guide_id'] for h in result['hits']],['IAM-004','MAIL-001','IAM-005'])
        self.assertFalse(result['reranking'])
        self.assertTrue(result['ambiguous'])
        self.assertEqual(result['category'],'muu')

    def test_source_must_have_the_relevant_safety_condition(self):
        index=self.index()
        index.guides['IAM-003']=dict(index.guides['IAM-003'],steps=['Älä hyväksy tuntemattomia kalenterikutsuja.'])
        self.assert_unchanged(self.ticket,index)

    def test_multiple_supported_sources_do_not_force_a_choice(self):
        index=self.index()
        index.guides['IAM-002']=dict(index.guides['IAM-002'],steps=index.guides['IAM-003']['steps'])
        self.assert_unchanged(self.ticket,index)

    def test_source_ids_and_titles_are_not_routing_rules(self):
        index=self.index()
        names={gid:'source-'+str(i) for i,gid in enumerate(index.guides)}
        index.guides={names[gid]:dict(g,id=names[gid],title='Ohje',keywords=['yleinen'])
                      for gid,g in index.guides.items()}
        for chunk in index.chunks:chunk['guide_id']=names[chunk['guide_id']]
        result=index.query(self.ticket)
        self.assertEqual(result['hits'][0]['guide_id'],names['IAM-003'])

    def test_another_category_cannot_be_promoted(self):
        index=self.index()
        index.guides['IAM-003']=dict(index.guides['IAM-003'],category='sähköposti')
        self.assert_unchanged(self.ticket,index)

    def test_existing_top_k_contract_is_preserved(self):
        for count in [1,2,3,6]:
            with self.subTest(top_k=count):
                result=self.index().query(self.ticket,top_k=count)
                self.assertEqual(len(result['hits']),count)
                self.assertEqual(result['hits'][0]['guide_id'],'IAM-003')

    def test_conflicting_positive_initiation_prevents_promotion(self):
        for ending in ['Aloitin kirjautumisen itse.', 'Olen itse käynnistänyt kirjautumisen.']:
            with self.subTest(ending=ending):self.assert_unchanged(self.ticket+' '+ending)

    def test_unopened_unrelated_object_is_not_uninitiated_authentication(self):
        for noun in ['sähköpostia','liitetiedostoa','kalenteria']:
            with self.subTest(noun=noun):
                self.assert_unchanged('Puhelin pyytää hyväksymään kirjautumisen. En ole avannut '+noun+'.')

    def test_alternative_source_wording_is_supported(self):
        index=self.index()
        index.guides['IAM-003']=dict(index.guides['IAM-003'],
            steps=['Älä vahvista tunnistautumista, jota et itse käynnistänyt.'])
        self.assertEqual(index.query(self.ticket)['hits'][0]['guide_id'],'IAM-003')

    def test_financial_scope_filter_still_has_final_authority(self):
        result=self.index().query(self.ticket.split('Voinko')[0]+
            ' Korvaako kotivakuutus vahingon ja paljonko omavastuu olisi?')
        self.assertEqual(result['hits'],[])
        self.assertEqual(result['category'],'muu')
        self.assertEqual(result['scope_filter']['reason'],'insurance_financial_request')


class RequestScopeTests(unittest.TestCase):
    """Intent regressions with controlled vectors, never a real embedding model."""
    def query(self,ticket,source='DEVICE-003',score=.458248):
        index=object.__new__(search.VectorSearch)
        index.guides={g['id']:g for g in desk.guides()}
        index.model=SimpleNamespace(encode=Mock(return_value=[[1.,0.]]))
        index.threshold=.43
        index.fingerprint='synthetic-no-model'
        index.chunks=[{'guide_id':source,'chunk_id':source+':synthetic','text':'synthetic'}]
        index.vectors=[[score,math.sqrt(1-score**2)]]
        result=index.query(ticket)
        index.model.encode.assert_called_once()
        return result

    def assert_rejected(self,result):
        self.assertEqual(result['hits'],[])
        self.assertEqual(result['category'],'muu')
        self.assertFalse(result['ambiguous'])
        self.assertEqual(result['scope_filter']['reason'],'insurance_financial_request')
        self.assertTrue(result['scope_filter']['evidence'])
        self.assertTrue(result['scope_filter']['excluded_hits'])

    def test_u19_insurance_compensation_and_deductible_are_outside_support(self):
        ticket='Työreppuni ja siinä ollut läppäri kastuivat. Korvaako kotivakuutus vahingon ja paljonko omavastuu olisi?'
        result=self.query(ticket)
        self.assert_rejected(result)
        self.assertEqual(result['best_candidate']['guide_id'],'DEVICE-003')
        self.assertEqual(result['best_candidate']['score'],.458248)
        self.assertEqual(result['scope_filter']['excluded_hits'][0]['score'],.458248)

    def test_real_it_problem_at_insurance_company_is_not_rejected(self):
        ticket='Vakuutusyhtiön Outlook ei vastaanota sähköpostia. Miten saan viestit taas näkyviin?'
        for result in [self.query(ticket,'MAIL-001'),search.keyword_search(ticket,desk.guides())]:
            with self.subTest(backend=result['backend']):
                self.assertEqual(result['hits'][0]['guide_id'],'MAIL-001')
                self.assertEqual(result['category'],'sähköposti')
                self.assertNotIn('scope_filter',result)

    def test_policy_and_deductible_as_background_do_not_block_it_support(self):
        ticket='Koneella on kotivakuutus ja omavastuu on 200 euroa. Outlook ei vastaanota sähköpostia. Miten saan työpostin taas toimimaan?'
        result=self.query(ticket,'MAIL-001')
        self.assertEqual(result['hits'][0]['guide_id'],'MAIL-001')
        self.assertNotIn('scope_filter',result)

    def test_financial_question_paraphrases_do_not_need_case_ids_or_deductible_keyword(self):
        for ticket in ['Tietokone varastettiin. Korvaisiko matkavakuutukseni vahingon?',
                       'Kotivakuutuksen ehdot ovat edessäni. Mikä omavastuu tässä olisi?',
                       'Haluan selvittää, kuinka suuren korvauksen vakuutuksesta saa rikkinäisestä laitteesta.']:
            with self.subTest(ticket=ticket):
                self.assert_rejected(self.query(ticket))

    def test_keyword_backend_uses_the_same_request_scope_rule(self):
        ticket='Korvaako kotivakuutus vahingon, jos kannettavan kiintolevy rikkoutui?'
        self.assert_rejected(search.keyword_search(ticket,desk.guides()))

    def test_quoted_financial_question_and_mixed_it_request_are_preserved(self):
        ticket='Aiemmassa viestissä luki: Korvaako kotivakuutus vahingon? Nyt Outlook ei vastaanota sähköpostia. Miten korjaan postiongelman?'
        result=self.query(ticket,'MAIL-001')
        self.assertEqual(result['hits'][0]['guide_id'],'MAIL-001')
        self.assertNotIn('scope_filter',result)

    def test_negated_or_same_sentence_financial_context_does_not_hide_it_request(self):
        for ticket in ['En kysy, korvaako kotivakuutus vahingon, vaan miten saan Outlookin vastaanottamaan viestejä.',
                       'Korvaako kotivakuutus vahingon ja miten saan Outlookin vastaanottamaan viestejä?',
                       'Koneella on kotivakuutus. Korvaako uusi Outlook vanhan sähköpostisovelluksen?']:
            with self.subTest(ticket=ticket):
                result=self.query(ticket,'MAIL-001')
                self.assertEqual(result['hits'][0]['guide_id'],'MAIL-001')
                self.assertNotIn('scope_filter',result)

    def test_demo_chain_rejects_financial_question_without_model_call(self):
        ticket='Korvaako kotivakuutus vahingon ja paljonko omavastuu olisi?'
        with patch('search.vector_search',side_effect=lambda text,guides:self.query(text)), \
                patch('desk.call_model',side_effect=AssertionError('No model call')) as model:
            result=desk.answer(ticket,backend='vector')
        self.assertEqual(result['result']['state'],'insufficient')
        self.assertEqual(result['result']['steps'],[])
        self.assertEqual(result['sources'],[])
        model.assert_not_called()


class ExplicitServiceBoundaryTests(unittest.TestCase):
    """New development examples, not replayed holdout tickets or model outputs."""
    calculation='Sovellus toimii normaalisti. Laske osallistujamäärien keskiarvo.'
    decision='Kalenteri toimii. Päätä puolestamme, ketkä saavat edustaa yhdistystä, ja kirjoita hyväksyntä.'

    def query(self,ticket):
        return RequestScopeTests.query(self,ticket,source='DEVICE-001',score=.7)

    def assert_rejected(self,ticket):
        result=self.query(ticket)
        self.assertEqual(result['hits'],[])
        self.assertEqual(result['category'],'muu')
        self.assertFalse(result['ambiguous'])
        scope=result['scope_filter']
        self.assertEqual(scope['reason'],'unsupported_requested_action')
        self.assertTrue(scope['requested_action'])
        self.assertTrue(scope['requested_object'])
        self.assertTrue(scope['confirmed_observations'])
        self.assertEqual(scope['excluded_hits'][0]['score'],.7)
        self.assertEqual(result['best_candidate']['score'],.7)
        return result

    def assert_preserved(self,ticket):
        result=self.query(ticket)
        self.assertEqual(result['hits'][0]['guide_id'],'DEVICE-001')
        self.assertNotIn('scope_filter',result)
        return result

    def test_explicit_nontechnical_calculation_requests_are_rejected(self):
        for ticket in [self.calculation,
                       'Teknistä ongelmaa ei ole. Voisitko laskea ryhmien prosenttiosuudet?',
                       'Tiedosto aukeaa oikein. Laske tilaisuuden kustannusten summa.']:
            with self.subTest(ticket=ticket):self.assert_rejected(ticket)

    def test_content_generation_is_not_a_technical_fault(self):
        for ticket in ['Ohjelma toimii. Laadi juhlapuhe yhdistyksen vuosipäivään.',
                       'PDF avautuu normaalisti. Kirjoita tiedote kilpailun voittajasta.',
                       'En tarvitse teknisiä ohjeita. Voitteko kirjoittaa kertomuksen retkestämme?']:
            with self.subTest(ticket=ticket):self.assert_rejected(ticket)

    def test_delegated_nontechnical_decisions_are_rejected(self):
        for ticket in [self.decision,
                       'Sovellus toimii. Myönnä puolestani osallistumislupa tapahtumaan.']:
            with self.subTest(ticket=ticket):self.assert_rejected(ticket)

    def test_no_confirmed_observation_means_unknown_not_rejection(self):
        for ticket in ['Laske osallistujamäärien keskiarvo.',
                       'Päätä puolestamme mitä tehdään.',
                       'Laadi seuraavaa vaihetta varten suunnitelma.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_uncertain_observations_do_not_establish_nontechnical_scope(self):
        for prefix in ['Ehkä ', 'En tiedä, ', 'En ole varma, ', 'Jos ']:
            with self.subTest(prefix=prefix):self.assert_preserved(prefix+self.calculation)

    def test_technical_fault_with_business_background_is_preserved(self):
        for ticket in ['Ohjelma toimii toisella koneella. PDF ei avaudu täällä. Laske myös summat, jos saat sen auki.',
                       'Kalenteri toimii, mutta tulostin ei tulosta osallistujaluetteloa.',
                       'Tiedosto aukeaa. En pääse tallentamaan muutoksia, laadi ohje asian selvitykseen.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_service_workflows_do_not_require_a_fault(self):
        for ticket in ['Ohjelma toimii. Laadi käyttöoikeuspyyntö uudelle työntekijälle.',
                       'Kalenteri toimii. Päätä puolestamme, miten tilin päättymisilmoitus toimitetaan IT-tuelle.',
                       'Sovellus toimii. Miten pyydän hyväksytyn lisäosan asennusta?']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_missing_technical_keywords_do_not_imply_out_of_scope(self):
        for ticket in ['Se jäi taas pyörimään. En pääse eteenpäin.',
                       'Se ei näy enää. Voitteko auttaa?',
                       'Sovellus toimii. Kirjoita, miten saan sen takaisin näkyviin.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_mixed_requests_are_preserved_even_in_one_sentence(self):
        for ticket in [self.calculation+' Lisäksi tarvitsen apua, kun yhteys katkeaa.',
                       'Ohjelma toimii. Laske keskiarvo ja auta saamaan toinen ruutu näkyviin.',
                       'Kalenteri toimii. Päätä puolestamme osallistujat ja neuvo miten haen käyttöoikeutta.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_negated_request_is_not_a_current_request(self):
        self.assert_preserved('Ohjelma toimii. En pyydä laskemaan keskiarvoa, vaan tarvitsen apua näkymän asetuksiin.')

    def test_quotations_and_previous_requests_are_not_current_intent(self):
        for ticket in ['Ohjelma toimii. Aiemmassa pyynnössä luki: Laske keskiarvo. Nyt asia on toinen.',
                       'Sovellus toimii. Esimerkki koulutukseen: Laske keskiarvo.',
                       'Sovellus toimii. Viestissä luki ”Laske keskiarvo”.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_technical_calculations_and_instructions_are_not_content_work(self):
        for ticket in ['Sovellus toimii. Laske paljonko levytilaa tarvitaan päivitykseen.',
                       'Ohjelma toimii. Kirjoita ohje miten näen vapaan tilan.',
                       'Sovellus toimii. Laadi verkon vian selvityssuunnitelma.']:
            with self.subTest(ticket=ticket):self.assert_preserved(ticket)

    def test_safety_incident_has_priority_over_working_application(self):
        for incident in ['Työpuhelin pyytää hyväksymään kirjautumisen, jota en itse aloittanut.',
                         'Viestissä pyydetään salasanaa tuntemattomalla sivulla.',
                         'Akku on turvonnut ja laite kuumenee.']:
            with self.subTest(incident=incident):self.assert_preserved(self.calculation+' '+incident)

    def test_same_scope_rule_applies_to_keyword_backend(self):
        guide=dict(desk.guides()[0],id='SYNTHETIC',keywords=['sovellus','kalenteri','ohjelma'])
        for ticket in [self.calculation,self.decision]:
            with self.subTest(ticket=ticket):
                result=search.keyword_search(ticket,[guide])
                self.assertEqual(result['hits'],[])
                self.assertEqual(result['scope_filter']['reason'],'unsupported_requested_action')
                self.assertEqual(result['scope_filter']['excluded_hits'][0]['guide_id'],'SYNTHETIC')

    def test_rejection_does_not_depend_on_source_ids_or_scores(self):
        for source,score in [('MAIL-004',.9),('IAM-005',.6)]:
            result=RequestScopeTests.query(self,self.decision,source=source,score=score)
            self.assertEqual(result['hits'],[])
            self.assertEqual(result['best_candidate']['guide_id'],source)
            self.assertEqual(result['scope_filter']['excluded_hits'][0]['score'],score)

    def test_demo_and_live_rejections_do_not_call_language_model(self):
        for mode in ['demo','live']:
            with self.subTest(mode=mode), \
                    patch('search.vector_search',side_effect=lambda text,guides:self.query(text)), \
                    patch('desk.call_model',side_effect=AssertionError('No model call')) as model:
                result=desk.answer(self.calculation,mode=mode,backend='vector')
                self.assertEqual(result['result']['state'],'insufficient')
                self.assertEqual(result['result']['steps'],[])
                self.assertEqual(result['sources'],[])
                self.assertFalse(result['model_used'])
                model.assert_not_called()

    def test_partially_working_tool_is_not_a_confirmed_nontechnical_context(self):
        for observation in ['Sovellus toimii vain osittain.', 'Ohjelma toimii huonosti.',
                            'Kalenteri toimii välillä.']:
            with self.subTest(observation=observation):
                self.assert_preserved(observation+' Laske osallistujamäärien keskiarvo.')

    def test_additional_technical_action_without_technical_nouns_is_preserved(self):
        for ending in ['ja palauta se takaisin paikalleen.', 'ja korjaa se ennen seuraavaa käyttöä.',
                       'ja auta saamaan se takaisin.']:
            with self.subTest(ending=ending):
                self.assert_preserved('Sovellus toimii. Laske keskiarvo '+ending)

    def test_unclear_onboarding_approval_is_not_a_nontechnical_decision(self):
        self.assert_preserved('Kalenteri toimii. Hyväksy puolestamme uuden työntekijän aloitus.')


class SearchTests(unittest.TestCase):
    def test_corpus_integrity(self):
        gs=desk.guides();search.validate_guides(gs);self.assertEqual(len(gs),20)
    def test_chunk_boundaries(self):
        g=dict(desk.guides()[0]);g['steps']=[' '.join('sana'+str(i) for i in range(300))]
        parts=search.chunks([g],WordTokenizer(),max_tokens=50)
        self.assertTrue(all(len(p['text'].split())<=50 for p in parts))
        text=' '.join(p['text'] for p in parts)
        for i in range(300):self.assertIn('sana'+str(i),text)
        self.assertEqual(len(parts),len({c['chunk_id'] for c in parts}))
    def test_cache_reuse_and_invalidation(self):
        g=next(g for g in desk.guides() if g['id']=='VPN-001');model=FakeEncoder()
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)/'vectors.json';first=search.VectorSearch([g],model,cache);self.assertEqual(model.calls,1)
            second=search.VectorSearch([g],model,cache);self.assertEqual(model.calls,1);self.assertEqual(first.fingerprint,second.fingerprint)
            third=search.VectorSearch([dict(g,version='changed')],model,cache);self.assertEqual(model.calls,2);self.assertNotEqual(first.fingerprint,third.fingerprint)
    def test_vector_threshold_and_category(self):
        g=next(g for g in desk.guides() if g['id']=='VPN-001')
        with tempfile.TemporaryDirectory() as tmp:
            index=search.VectorSearch([g],FakeEncoder(),Path(tmp)/'vectors.json')
            found=index.query('etätyöyhteys');self.assertEqual(found['category'],'verkko');self.assertEqual(found['hits'][0]['guide_id'],'VPN-001')
            missing=index.query('lomamatka');self.assertEqual(missing['category'],'muu');self.assertEqual(missing['hits'],[])
    def test_ambiguity_abstains(self):
        gs=[dict(desk.guides()[0],id='A',category='verkko'),dict(desk.guides()[1],id='B',category='laitteet')]
        class Same:
            def encode(self,texts,**kwargs):return [[1.,0.] for _ in texts]
        with tempfile.TemporaryDirectory() as tmp:
            out=search.VectorSearch(gs,Same(),Path(tmp)/'x.json').query('epäselvä')
            self.assertTrue(out['ambiguous']);self.assertEqual(out['category'],'muu')
    def test_keyword_failure_preserved(self):
        out=search.keyword_search('Etätyöyhteys ei muodostu kotona, mutta tavalliset verkkosivut avautuvat. Mitä tarkistan?',desk.guides());self.assertEqual(out['hits'],[])
    def test_duplicate_rejected(self):
        g=desk.guides()[0]
        with self.assertRaises(search.SearchError):search.validate_guides([g,g])
    def test_search_failure_visible(self):
        with patch('search.vector_search',side_effect=search.SearchError('testivirhe')):
            with self.assertRaisesRegex(desk.DeskError,'testivirhe'):desk.answer('VPN ei toimi',backend='vector')
    def test_ambiguous_does_not_invent_answer(self):
        mocked={'backend':'vector','category':'muu','ambiguous':True,'hits':[{'guide_id':'VPN-001'}]}
        with patch('search.vector_search',return_value=mocked):
            out=desk.answer('VPN vai muu',backend='vector');self.assertEqual(out['result']['steps'],[]);self.assertEqual(out['sources'],[])
if __name__=='__main__':unittest.main()
