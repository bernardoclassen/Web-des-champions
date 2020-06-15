


import http.server
import socketserver
import sqlite3
import json


from urllib.parse import urlparse, parse_qs, unquote


#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'countries/0.1'
  
  # On surcharge la méthode qui traite les requêtes GET
  #
  def do_GET(self):
    # on récupère les paramètres
    self.init_params()

    # le chemin d'accès commence par : location
    if self.path_info[0] == "location":
      data = self.data_loc()
      self.send_json(data)
      
      # description
    elif self.path_info[0] == "description":
      self.send_json_country(self.path_info[1])
      
      #service
    elif self.path_info[0] == "service":
      self.send_html('<p>Path info : <code>{}</p><p>Chaîne de requête : <code>{}</code></p>'.format('/'.join(self.path_info),self.query_string));
    
   
    else:
      self.send_static()

      


  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

    
  
  def do_POST(self):
    self.init_params()
    if self.path_info[0] == "service":
      self.send_html(('<p>Path info : <code>{}</code></p><p>Chaîne de requête : <code>{}</code></p><p>Corps :</p><pre>{}</pre>').format('/'.join(self.path_info),self.query_string,self.body));
    else:
      self.send_error(405)
      
  #
  # On envoie le document statique demandé
  #
  def send_static(self):

    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
        
  def send_html(self,content):
     headers = [('Content-Type','text/html;charset=utf-8')]
     html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}'.format(self.path_info[0],content)
     self.send(html,headers)
      
  def send_json(self,data,headers=[]):
     body = bytes(json.dumps(data),'utf-8') # encodage en json et UTF-8
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
  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    print('path_info =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)

  # On renvoie la liste des pays avec leurs coordonnées
  #
  def send_json_countries(self,continent):

    # on récupère la liste de pays depuis la base de données
    r = self.db_get_countries(continent)

    # on renvoie une liste de dictionnaires au format JSON
    if r == None:
      self.send_error(404,'Country not found')
    else: 
      data = {k:r[k] for k in r.keys()}
      json_data = json.dumps(data, indent=4)
      headers = [('Content-Type','application/json')]
      self.send(json_data,headers)

  def data_loc(self) :
      c = conn.cursor()
      sql = 'SELECT * from countries'
      c.execute(sql)
      r = c.fetchall()
      data = []
      for i in r :
          wp = i['wp']
          name = i['name']
          capital = i['capital']
          lat = i['latitude']
          lon = i['longitude']
          continent=i['continent']
          Population=i['Population']
          Superficie=i['Superficie']
          drapeau = i['drapeau']
          data.append({'wp': wp, 'name' : name, 'capital' : capital, 'lat': lat, 'lon': lon, 'continent' : continent, 'Population' : Population, 'Superficie' : Superficie, 'drapeau' : drapeau})
          print(data)
      return data

  def db_get_countries(self,country):
    c = conn.cursor()
    sql = 'SELECT * from countries WHERE wp=?'
    c.execute(sql,(country,))
    return c.fetchone()


# Ouverture d'une connexion avec la base de données
conn = sqlite3.connect('countries.sqlite') 
# Pour accéder au résultat des requêtes sous forme d'un dictionnaire
conn.row_factory = sqlite3.Row
#
# Instanciation et lancement du serveur
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
