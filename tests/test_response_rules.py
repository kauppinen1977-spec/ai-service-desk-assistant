import unittest

from response_rules import applicable, compatible, known_facts, questions_for, steps_for


class KnownFactsTests(unittest.TestCase):
    def test_questions_do_not_establish_internet_fact(self):
        for ticket in [
            'Internet toimii?',
            'Verkkosivut avautuvat?',
            'Internet ei toimi?',
            'Onko niin, että internet toimii?',
            'VPN ei yhdistä. Internet toimii?',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_negated_claims_do_not_establish_internet_fact(self):
        for ticket in [
            'En usko, että internet toimii.',
            'En usko, että internet ei toimi.',
            'En ole varma, että internet toimii.',
            'Ei ole varmaa, että internet toimii.',
            'Ei ole totta, että internet toimii.',
            'Ei pidä paikkaansa, että internet toimii.',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_uncertain_statements_do_not_establish_internet_fact(self):
        for ticket in [
            'Ehkä internet toimii.',
            'Luulen, että internet toimii.',
            'Internet toimii luultavasti.',
            'Internet toimii mahdollisesti.',
            'Internet toimii ilmeisesti.',
            'Internet toimii varmaan.',
            'Internet toimii vain välillä.',
            'Jos internet toimii, VPN ei yhdistä.',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_clear_positive_statements_preserve_evidence(self):
        for ticket, evidence in [
            ('Internet toimii.', 'Internet toimii'),
            ('Tavalliset verkkosivut avautuvat.', 'Tavalliset verkkosivut avautuvat'),
            ('VPN ei yhdistä, mutta netti muuten toimii.', 'netti muuten toimii'),
            ('Olen varma, että internet toimii.', 'internet toimii'),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [
                    {'field': 'internet_working', 'value': True, 'evidence': evidence}
                ])

    def test_clear_negative_statements_preserve_evidence(self):
        for ticket, evidence in [
            ('Internet ei toimi.', 'Internet ei toimi'),
            ('Netti ei toimi.', 'Netti ei toimi'),
            ('Yksikään verkkosivu ei avaudu.', 'Yksikään verkkosivu ei avaudu'),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [
                    {'field': 'internet_working', 'value': False, 'evidence': evidence}
                ])

    def test_unrelated_sentence_preserves_fact(self):
        for ticket, value in [
            ('Internet toimii. Miksi VPN ei yhdistä?', True),
            ('Internet ei toimi. Miten jatkan?', False),
            ('Internet toimii. VPN toimii varmaan.', True),
            ('Internet toimii. En usko, että VPN toimii.', True),
            ('Internet ei toimi. En ole varma VPN-asetuksista.', False),
            ('Internet toimii. Ei ole totta, että VPN toimii.', True),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket)[0]['value'], value)

    def test_uncertain_internet_does_not_exclude_guides(self):
        for ticket in ['Internet toimii?', 'En usko, että internet toimii.']:
            with self.subTest(ticket=ticket):
                facts = known_facts(ticket)
                # Uncertainty still establishes no contradictory internet fact.
                # It no longer constitutes positive eligibility on its own.
                for id in ('NET-004', 'VPN-001'):
                    self.assertEqual(compatible({'id': id}, facts), (True, ''))
                    self.assertFalse(applicable({'id': id}, facts)[0])

    def test_uncertain_internet_keeps_vpn_check_and_question(self):
        guide = {
            'id': 'VPN-001',
            'steps': ['Tarkista internetyhteys.', 'Sulje VPN-sovellus.'],
            'version': 'test',
        }
        for ticket in ['Internet toimii?', 'En usko, että internet toimii.']:
            with self.subTest(ticket=ticket):
                facts = known_facts(ticket)
                self.assertEqual([step['source_step'] for step in steps_for(guide, facts)], [1, 2])
                self.assertIn('VPN-001:internet', [question['id'] for question in questions_for(guide, facts)])


if __name__ == '__main__':
    unittest.main()
