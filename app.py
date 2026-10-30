import argparse,json,os,secrets
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from desk import answer,DeskError
import desk
from corpus import NAMES
from api_settings import settings
ROOT=Path(__file__).resolve().parent
APP_VERSION='0.3.1'
APP_UPDATED='29.10.2026'
STATIC_FILES={'/soc-theme.css': ('soc-theme.css','text/css'), '/soc-banner.jpg': ('soc-banner.jpg','image/jpeg')}
TOKEN=secrets.token_urlsafe(24)
PAGE=(Path(__file__).parent/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN)
MEMORY_PAGE=(Path(__file__).parent/'memory.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN).replace('__BASE_VERSION__',APP_VERSION).replace('__APP_UPDATED__',APP_UPDATED)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,data,kind='application/json'):
        raw=data if isinstance(data,bytes) else data.encode('utf-8');self.send_response(status)
        for key,value in [('Content-Type',kind if kind.startswith('image/') else kind+'; charset=utf-8'),('Content-Length',str(len(raw))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')]:self.send_header(key,value)
        self.end_headers();self.wfile.write(raw)
    def error_reply(self,error):
        result={'error':str(error),'code':error.code,'help':error.help_text}
        if hasattr(error,'upstream_status'):result.update(upstream_status=error.upstream_status,provider_code=error.provider_code,provider_param=error.provider_param,provider_description=error.provider_description,provider_terms=error.provider_terms)
        self.reply(error.status,json.dumps(result,ensure_ascii=False))
    def do_GET(self):
        # A page/token must not be exposed under an attacker-controlled DNS name.
        if self.headers.get('Host','').split(':')[0] not in ('127.0.0.1','localhost'):
            return self.reply(403,'{}')
        if self.path=='/':self.reply(200,PAGE.replace('__CORPUS__',desk.CORPUS),'text/html')
        elif self.path in STATIC_FILES:
            filename,kind=STATIC_FILES[self.path]
            resource=ROOT/filename
            # Exact routes only; never resolve a request path or follow resource symlinks.
            if resource.is_symlink() or resource.resolve().parent!=ROOT or not resource.is_file():return self.reply(404,'{}')
            self.reply(200,resource.read_bytes(),kind)
        elif self.path=='/memory':self.reply(200,MEMORY_PAGE,'text/html')
        elif self.path=='/pikaohje':
            folder=ROOT/'docs';resource=folder/'13_ratkaisumuistin_pikaohje.md'
            if folder.is_symlink() or resource.is_symlink() or resource.resolve().parent!=folder or not resource.is_file():return self.reply(404,'{}')
            self.reply(200,resource.read_bytes(),'text/plain')
        elif self.path=='/health':self.reply(200,json.dumps({'ok':True,'version':APP_VERSION,'corpus':desk.CORPUS,'api_key_available':settings.status()['configured']}))
        else:self.reply(404,'{}')
    def do_POST(self):
        if self.path!='/api/answer' and not self.path.startswith('/api/memory/'):return self.reply(404,'{}')
        try:
            size=int(self.headers.get('Content-Length','0'))
            # Finnish non-ASCII fields may expand when JSON is escaped.
            if not 0<size<=(120000 if self.path.startswith('/api/memory/') else 20000):raise DeskError('Pyyntö on liian suuri tai tyhjä.')
            # Consume the bounded body before rejecting: unread POST data can reset Windows sockets.
            body=self.rfile.read(size)
            if self.headers.get('X-Desk-Token')!=TOKEN:raise DeskError('Sivun istunto on vaihtunut.','session_expired',403,'Kopioi tallentamattomat lomaketekstit talteen ennen sivun päivittämistä. Päivitä sitten sivu ja yritä uudelleen.')
            obj=json.loads(body)
            if self.path=='/api/memory/suggest' and isinstance(obj,dict):obj['_session_id']=TOKEN
            if not isinstance(obj,dict):raise DeskError('Virheellinen pyyntö.')
            if self.path=='/api/memory/api-status':out=settings.status()
            elif self.path=='/api/memory/api-settings':out=settings.update(obj)
            elif self.path.startswith('/api/memory/'):
                from solution_memory import dispatch
                out=dispatch(self.path.removeprefix('/api/memory/'),obj)
            else:out=answer(obj.get('ticket'),obj.get('mode','demo'),obj.get('backend','vector'))
            self.reply(200,json.dumps(out,ensure_ascii=False))
        except DeskError as e:self.error_reply(e)
        except (ValueError,TypeError,UnicodeError):self.error_reply(DeskError('Pyyntöä ei voitu lukea.','invalid_request'))
        except Exception:self.error_reply(DeskError('Sovelluksessa tapahtui odottamaton virhe.','internal_error',500,'Yritä uudelleen. Jos virhe toistuu, ilmoita tämä virhekoodi. Avainta tai tukipyynnön sisältöä ei näytetä virheessä.'))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8501)
    parser.add_argument('--corpus',choices=NAMES,default='legacy20');args=parser.parse_args()
    desk.CORPUS=args.corpus
    desk.guides()  # Fail before serving if the selected manifest is invalid.
    try:server=HTTPServer(('127.0.0.1',args.port),Handler)
    except OSError:raise SystemExit('Portti ei ole käytettävissä. Sulje vanha palvelin Ctrl+C:llä tai käynnistä: python app.py --port 8502')
    print(f'AI Service Desk {APP_VERSION} ({desk.CORPUS}) - avaa http://127.0.0.1:{args.port} - lopeta Ctrl+C',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
