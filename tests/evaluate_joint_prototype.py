"""Run from the SOC worktree root, offline, using a temporary SQLite backup.

Prints the predeclared expectations and each mode's results. The optional
application mode shares the prototype; the default remains keyword search.
"""
import os,sys,pathlib,sqlite3,tempfile,json,hashlib,subprocess,types
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false')
sys.stdout.reconfigure(encoding='utf-8');root=pathlib.Path.cwd();sys.path.insert(0,str(root))
def guard(event,args):
 if event in ('socket.connect','socket.sendto'):raise RuntimeError('Network disabled')
sys.addaudithook(guard)
from solution_memory import Memory
from joint_search_prototype import JointSearchPrototype
from keyword_boundary_comparison import boundary_search
from search import encoder
baseline_source = subprocess.run(['git', 'show', '3d87e01:solution_memory.py'], check=True, capture_output=True).stdout.decode('utf-8')
baseline = types.ModuleType('baseline_memory')
baseline.__file__ = str(root/'solution_memory.py')
exec(compile(baseline_source, '3d87e01:solution_memory.py', 'exec'), baseline.__dict__)
F={'operating_system':'Windows 11','product':'LENOVO','product_version':'83GS'}
C=[('Q1','Näytön ohjain ei toimi kunnolla ja kaipaan siihen päivitystä',['ohjain']),('Q2','Näytönohjain ei toimi',['ohjain']),('Q3','Hiiri ei toimi',['hiiri']),('Q4','Ei toimi',[]),('Q5','Teamsissa mikrofoni ei toimi',[]),('Q6','Näyttö jumittaa',['näyttö']),('Q7','Näytönohjaimen asetukset',['ohjain']),('Q8','Nvidia',['ohjain']),('Q9','Näytön ohjain asetukset pielessä',['ohjain']),('Q10','Näytönohjainta pitäisi päivittää',['ohjain']),('Q11','Hiiren vika',['hiiri']),('Q12','Ääniohjain ei toimi',[]),('Q13','Näppäimistö ei toimi',[]),('Q14','Ei toimi lainkaan',[]),('Q15','Tulostin paperitukos',[]),('Q16','NVDIA',['näyttö']),('Q17','Missä vika on?',[]),('Q18','Kuva jähmettyy näytössä',['näyttö']),('Q19','Kohdistin ei liiku kun siirrän hiirtä',['hiiri']),('Q20','Tietokoneen kaiuttimista ei kuulu ääntä',[]),('Q21','83GS!',[])]
print('PREDECLARED',json.dumps(C,ensure_ascii=False),flush=True)
SYNTHETIC = [('E42!!', 'Skanneri E42'), ('ZX147', 'Tulostin ZX147'),
             ('Q77!!', 'Sovellus kaatuu'), ('AB456', 'Sovellus kaatuu')]
print('SYNTHETIC_PREDECLARED', json.dumps(SYNTHETIC, ensure_ascii=False), flush=True)
# Previous prototype output on this exact corpus, including known misses and
# false hits; a regression check is not an endorsement of those quality defects.
SNAPSHOT_HASH='9019f9419c2fdc7472d50d347f4183754daade1ede7c943f0455bcddd1dfbb7c'
SNAPSHOT = dict(zip((f'Q{i}' for i in range(1,22)), [
 ['ohjain'],['ohjain'],['hiiri'],[],[],['näyttö'],['ohjain'],['ohjain'],['ohjain'],['ohjain'],
 ['hiiri'],[],[],[],[],[],[],[],['hiiri'],['näyttö'],[]]))
print('PREVIOUS_JOINT_SNAPSHOT', json.dumps(SNAPSHOT, ensure_ascii=False), flush=True)
def name(row):
 t=row['title'].casefold()
 if 'näytönohjaimen' in t:return 'ohjain'
 if 'näyttö jumittaa' in t:return 'näyttö'
 if 'hiiren toimimattomuuden' in t:return 'hiiri'
 return row['title']
def view(out):return {'state':out['state'],'hits':[{'name':name(h['record']),'score':h['score'],**({'keyword_score':h['keyword_score']} if 'keyword_score' in h else {})} for h in out['hits']]}
p=root/'data/solutions-soc.sqlite3'; checksum=lambda:hashlib.sha256(p.read_bytes()).hexdigest(); before=checksum()
with tempfile.TemporaryDirectory() as tmp:
 path=pathlib.Path(tmp)/'soc.sqlite3'; source=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True); target=sqlite3.connect(path); source.backup(target); source.close();target.close()
 m=Memory(path); original=baseline.Memory(path); model=encoder(); joint=JointSearchPrototype(m,model); changes=[]
 for label,q,expected in C:
  item={'id':label,'expected':expected}
  for method in ('baseline_3d87','keyword','boundary','vector','joint'):
   try:
    if method=='baseline_3d87': out=original.search(q,'keyword',filters=F)
    elif method=='boundary': out=boundary_search(m,q,F)
    elif method=='joint': out=joint.search(q,F)
    else: out=m.search(q,method,model if method=='vector' else None,filters=F)
    item[method]=view(out)
   except Exception as e:item[method]={'error':type(e).__name__,'message':str(e)}
  print('RESULT',json.dumps(item,ensure_ascii=False),flush=True)
  actual=[h['name'] for h in item['joint'].get('hits',[])]
  if actual != SNAPSHOT[label]: changes.append({'id':label,'before':SNAPSHOT[label],'after':actual})
 print('JOINT_REGRESSIONS', json.dumps(changes, ensure_ascii=False), flush=True)
 if before == SNAPSHOT_HASH and changes: raise AssertionError('Joint search results changed on the frozen SOC snapshot')
 synthetic=Memory(pathlib.Path(tmp)/'synthetic.sqlite3')
 for title,problem,environment in [('Skanneri E42','Skanneri ei toimi','Harjoitusympäristö'),
                                   ('Tulostin ZX147','Tulostin jumittaa','Harjoitusympäristö'),
                                   ('Sovellus kaatuu','Sovellus kaatuu käynnistyksessä','Virhe Q77 ja malli AB456')]:
  row=synthetic.save(dict(title=title,problem=problem,environment=environment,solution='Tarkista asetukset.'))
  synthetic.transition(dict(id=row['id'],revision=row['revision'],confirmed=True,verified_by='Synteettinen testaaja'),'verified')
 synthetic_joint=JointSearchPrototype(synthetic,model)
 for query,expected in SYNTHETIC:
  item={'query':query,'expected':expected}
  for method in ('keyword','boundary','vector','joint'):
   try:
    if method=='boundary': out=boundary_search(synthetic,query)
    elif method=='joint': out=synthetic_joint.search(query)
    else: out=synthetic.search(query,method,model if method=='vector' else None)
    item[method]=view(out)
   except Exception as e:item[method]={'error':type(e).__name__,'message':str(e)}
  print('SYNTHETIC_RESULT',json.dumps(item,ensure_ascii=False),flush=True)
print('HASH_SAME',before==checksum(),before,flush=True)
