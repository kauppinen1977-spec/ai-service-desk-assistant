import argparse,json,os,secrets
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from desk import answer,DeskError
import desk
from corpus import NAMES
TOKEN=secrets.token_urlsafe(24)
PAGE=(Path(__file__).parent/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,data,kind='application/json'):
        raw=data.encode('utf-8');self.send_response(status)
        for key,value in [('Content-Type',kind+'; charset=utf-8'),('Content-Length',str(len(raw))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')]:self.send_header(key,value)
        self.end_headers();self.wfile.write(raw)
    def error_reply(self,error):
        self.reply(error.status,json.dumps({'error':str(error),'code':error.code,'help':error.help_text},ensure_ascii=False))
    def do_GET(self):
        if self.path=='/':self.reply(200,PAGE.replace('__CORPUS__',desk.CORPUS),'text/html')
        elif self.path=='/health':self.reply(200,json.dumps({'ok':True,'version':'0.3.1','corpus':desk.CORPUS,'api_key_available':bool(os.environ.get('OPENAI_API_KEY','').strip())}))
        else:self.reply(404,'{}')
    def do_POST(self):
        if self.path!='/api/answer':return self.reply(404,'{}')
        if self.headers.get('X-Desk-Token')!=TOKEN:return self.error_reply(DeskError('Sivun istunto on vaihtunut.','session_expired',403,'Päivitä sivu ja yritä uudelleen.'))
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=20000:raise DeskError('Pyyntö on liian suuri tai tyhjä.')
            obj=json.loads(self.rfile.read(size))
            if not isinstance(obj,dict):raise DeskError('Virheellinen pyyntö.')
            out=answer(obj.get('ticket'),obj.get('mode','demo'),obj.get('backend','vector'))
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
    print(f'AI Service Desk 0.3.1 ({desk.CORPUS}) - avaa http://127.0.0.1:{args.port} - lopeta Ctrl+C',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
