import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json
import sqlite3

class RequestHandler(http.server.SimpleHTTPRequestHandler):
  static_dir = '/client_1'
  server_version = 'TD3_map_FR-CA.py/0.1'
  
  def init_params(self):
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]
    self.query_string = info.query
    self.params = parse_qs(info.query)
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' :
        self.params = parse_qs(self.body)
    else:
      self.body = ''
    #print('info_path =',self.path_info)
    #print('body =',length,ctype,self.body)
    #print('params =', self.params)

  def do_GET(self):
    self.init_params()
    if self.path_info[0] == "location":
      data = self.data_loc()
      self.send_json(data)
    elif self.path_info[0] == "description":
      self.send_json_country(self.path_info[1])
    elif self.path_info[0] == "service":
      self.send_html('<p>Path info : <code>{}</p><p>Chaîne de requête : <code>{}</code></p>'.format('/'.join(self.path_info),self.query_string));
    else:
      self.send_static()

  def do_HEAD(self):
      self.send_static()

  def do_POST(self):
    self.init_params()
    if self.path_info[0] == "service":
      self.send_html(('<p>Path info : <code>{}</code></p><p>Chaîne de requête : <code>{}</code></p><p>Corps :</p><pre>{}</pre>').format('/'.join(self.path_info),self.query_string,self.body));
    else:
      self.send_error(405)

  def send_static(self):
    self.path = self.static_dir + self.path
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)

  def send_html(self,content):
     headers = [('Content-Type','text/html;charset=utf-8')]
     html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}'.format(self.path_info[0],content)
     self.send(html,headers)

  def send_json(self,data,headers=[]):
    body = bytes(json.dumps(data),'utf-8')
    self.send_response(200)
    self.send_header('Content-Type','application/json')
    self.send_header('Content-Length',int(len(body)))
    [self.send_header(*t) for t in headers]
    self.end_headers()
    self.wfile.write(body)

  def send(self,body,headers=[]):
     encoded = bytes(body, 'UTF-8')
     self.send_response(200)
     [self.send_header(*t) for t in headers]
     self.send_header('Content-Length',int(len(encoded)))
     self.end_headers()
     self.wfile.write(encoded)


  def send_json_country(self, country) :
    r = self.db_get_country(country)
    if r == None:
      self.send_error(404,'Country not found')
    else :
      data = {k:r[k] for k in r.keys()}
      json_data = json.dumps(data, indent=4)
      headers = [('Content-Type','application/json')]
      self.send(json_data,headers)

  def data_loc(self) :
      c = base_donnee.cursor()
      sql = 'SELECT * from countries'
      c.execute(sql)
      r = c.fetchall()
      data = []
      for i in r :
          wp = i['wp']
          name = i['name']
          cap = i['capital']
          lat = i['latitude']
          lon = i['longitude']
          cont=i['continent']
          pop=i['Population']
          sup=i['Superficie']
          flag = i['drapeau']
          data.append({'wp': wp, 'name' : name, 'capital' : cap, 'lat': lat, 'lon': lon, 'continent' : cont, 'Population' : pop, 'Superficie' : sup, 'drapeau' : flag})
          #print(data)
      return data

  def db_get_country(self,country):
    c = base_donnee.cursor()
    sql = 'SELECT * from countries WHERE wp=?'
    c.execute(sql,(country,))
    return c.fetchone()



base_donnee = sqlite3.connect('base_de_donnee.sqlite') 
base_donnee.row_factory = sqlite3.Row

httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
