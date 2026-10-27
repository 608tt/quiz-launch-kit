"""Single-product redemption reference. Bind to loopback behind HTTPS proxy."""
import argparse, hashlib, json, os, secrets, sqlite3, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
class Store:
 def __init__(self,path):
  self.db=sqlite3.connect(path)
  self.db.executescript('CREATE TABLE IF NOT EXISTS codes(hash TEXT PRIMARY KEY, expires REAL, redeemed INTEGER DEFAULT 0, revoked INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY, code TEXT, expires REAL);')
 def issue(self,n,days):
  codes=[secrets.token_urlsafe(24) for _ in range(n)]
  with self.db:self.db.executemany('INSERT INTO codes(hash,expires) VALUES (?,?)',[(digest(c),time.time()+days*86400) for c in codes])
  return codes
 def redeem(self,code):
  token=secrets.token_urlsafe(32);h=digest(code);now=time.time()
  with self.db:
   cur=self.db.execute('UPDATE codes SET redeemed=1 WHERE hash=? AND redeemed=0 AND revoked=0 AND expires>?',(h,now))
   if cur.rowcount!=1:return None
   self.db.execute('INSERT INTO sessions VALUES (?,?,?)',(digest(token),h,now+86400))
  return token
 def allowed(self,token):
  return bool(self.db.execute('SELECT 1 FROM sessions s JOIN codes c ON c.hash=s.code WHERE s.hash=? AND s.expires>? AND c.revoked=0',(digest(token),time.time())).fetchone())
 def revoke(self,code):
  with self.db:self.db.execute('UPDATE codes SET revoked=1 WHERE hash=?',(digest(code),))

def serve(store,quiz,port,origin,dev):
 class Handler(BaseHTTPRequestHandler):
  attempts={}
  def log_message(self,*args):pass # Do not log codes, cookies or answer data.
  def send(self,status,body,kind='text/html; charset=utf-8',cookie=None):
   self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Frame-Options','DENY')
   if cookie:self.send_header('Set-Cookie',cookie)
   self.end_headers();self.wfile.write(body.encode())
  def do_GET(self):
   if self.path=='/':return self.send(200,'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>兑换测试</title><body style="max-width:600px;margin:10vh auto;padding:24px;font:18px/1.8 system-ui;background:#f5f0e4;color:#315e56"><h1>打开你的探索</h1><p>请输入订单中收到的兑换码。兑换后本浏览器可使用 24 小时；请勿清除 Cookie。更换设备请联系订单客服。</p><form method="post" action="/redeem"><label>兑换码 <input name="code" required maxlength="100" autocomplete="off"></label><button>兑换并开始</button></form><p>娱乐体验，不是科学测评。遇到失效或打开失败，请通过原订单售后。</p></body></html>')
   if self.path=='/quiz':
    cookie=SimpleCookie()
    try:cookie.load(self.headers.get('Cookie',''));token=cookie['session'].value if 'session' in cookie else ''
    except Exception:token=''
    if not store.allowed(token):return self.send(403,'入口已失效或尚未兑换。<a href="/">返回兑换</a>')
    return self.send(200,quiz.read_text())
   self.send(404,'Not found','text/plain')
  def do_POST(self):
   if self.path!='/redeem':return self.send(404,'Not found','text/plain')
   if self.headers.get('Origin')!=origin:return self.send(403,'请求来源不匹配','text/plain')
   # Loopback reverse proxy collapses clients; intentionally global fallback limit.
   now=time.time();key=self.client_address[0];times=[x for x in self.attempts.get(key,[]) if x>now-60];self.attempts[key]=times
   if len(times)>=20:return self.send(429,'请求过多，请一分钟后再试','text/plain')
   times.append(now)
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<1024:raise ValueError()
    code=parse_qs(self.rfile.read(n).decode()).get('code',[''])[0].strip()
   except (ValueError,UnicodeError):return self.send(400,'无效请求','text/plain')
   token=store.redeem(code)
   if not token:return self.send(400,'兑换码无效、已使用或已过期。请通过原订单申请核查。','text/plain')
   self.send(200,'兑换成功。<a href="/quiz">开始测试</a>',cookie='session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400'+('' if dev else '; Secure'))
 server=HTTPServer(('127.0.0.1',port),Handler);server.timeout=10
 print('Local: http://127.0.0.1:'+str(port),flush=True);server.serve_forever()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['issue','serve','revoke']);parser.add_argument('--db',default='codes.sqlite');parser.add_argument('--count',type=int,default=1);parser.add_argument('--days',type=int,default=30);parser.add_argument('--port',type=int,default=8787);parser.add_argument('--quiz',default='quiz.html');parser.add_argument('--origin',default='http://127.0.0.1:8787');parser.add_argument('--dev',action='store_true');args=parser.parse_args()
 if args.count<1 or args.count>10000 or args.days<1:parser.error('count 1..10000; days >=1')
 st=Store(args.db)
 if args.action=='issue':print('\n'.join(st.issue(args.count,args.days)))
 elif args.action=='revoke':st.revoke(input('Code to revoke: ').strip());print('Revoked if present')
 else:
  quiz=Path(args.quiz).resolve()
  if not quiz.is_file():parser.error('Export quiz.html first')
  if not args.dev and not args.origin.startswith('https://'):parser.error('Production requires HTTPS origin; --dev is local-only')
  serve(st,quiz,args.port,args.origin,args.dev)
