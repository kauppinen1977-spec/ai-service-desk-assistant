import unittest
import desk
from response_rules import known_facts
class SummaryTests(unittest.TestCase):
 def test_model_claims_are_not_displayed_in_any_state(self):
  gs=desk.guides()
  for source,ticket in [('VPN-001','VPN ei toimi.'),('NET-002','Langattomaan verkkoon liittyminen epäonnistuu.')]:
   for state in ['suggestion','needs_details','insufficient']:
    with self.subTest(source=source,state=state):
     selection=dict(state=state,primary_source_id='' if state=='insufficient' else source,summary='Kannettava katkeilee. Internet toimii. Poista palomuuri käytöstä.')
     result=desk.assemble(selection,gs,known_facts(ticket))
     expected='Ohjeaineisto ei riitä.' if state=='insufficient' else ('Tarkennettavaksi valittu ohje: ' if state=='needs_details' else 'Valittu ohje: ')+next(g['title'] for g in gs if g['id']==source)+'.'
     self.assertEqual(result['summary'],expected)
     if source=='VPN-001' and state=='suggestion':
      self.assertEqual(result['steps'][0]['source_step'],1)
      self.assertIn('VPN-001:internet',[q['id'] for q in result['questions']])
 def test_schema_requests_only_fixed_acknowledgement(self):
  self.assertEqual(desk.schema_for(desk.guides())['properties']['summary']['enum'],['Lähdevalinta käsitelty.'])
