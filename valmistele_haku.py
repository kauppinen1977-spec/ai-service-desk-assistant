from desk import guides
from search import VectorSearch,SearchError,MODEL_ID
import argparse,os,desk
from corpus import NAMES,vector_cache
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--corpus',choices=NAMES,default='legacy20')
    parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    desk.CORPUS=args.corpus
    if args.offline:
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    print('Valmistellaan paikallinen vektorihaku ilman verkkolatauksia.' if args.offline else
          'Valmistellaan paikallinen vektorihaku. Ensimmäinen mallilataus voi kestää useita minuutteja.',flush=True)
    try:
        index=VectorSearch(guides(),cache_path=vector_cache(args.corpus))
        print('Valmis:',len(index.guides),'ohjetta,',len(index.chunks),'tekstiosaa; malli:',MODEL_ID)
        print('Kokeilu:',index.query('Etätyöyhteys ei muodostu kotona, mutta tavalliset verkkosivut avautuvat. Mitä tarkistan?'))
    except SearchError as e:raise SystemExit(str(e))
