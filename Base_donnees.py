#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 1 08:42:19 2020

@author: elmehdibelabied
"""

import wptools 
import re 
import sqlite3

#page= wptools.page('Bresil')
#page.get_parse(False)
#page.data['infobox']



def get_info(country): #récupération de l'infobox d'un pays sur wikipedia
    page = wptools.page(country,silent=True) #pour eviter un message au fond rose
    page.get_parse(False)
    return page.data['infobox'] # on renvoie l'infobox 
    
def print_capital(info): 
    print('{},capital:{}-{}'.format(info['conventional_long_name'],info['capital'],info['coordinates']))

#teste des deux fonctions avec le pays suivant :'canada'     
#jb = get_info('Canada')
#print_capital(jb)



#cette fonction retourne le nom complet de pays à partir de wikipedia 
def get_name(wp_info):
    
    # cas général
    if 'conventional_long_name' in wp_info:
        name = wp_info['conventional_long_name']
        

        m = re.match("([\w, -]+?)\s*{{",name)
        if m:
            name = m.group(1)
            
        # si le nom est situé entre {{ }} avec un caractère séparateur |
        # on conserve la partie après le |
        m = re.match("{{.*\|([\w, -]+)}}",name)
        if m:
            name = m.group(1)           
        return name

    # FIX manuel (l'infobox ne contient pas l'information)
    if 'common_name' in wp_info and wp_info['common_name'] == 'Singapore':
        return 'Republic of Singapore'
    
    # S'applique uniquement au Vanuatu
    if 'common_name' in wp_info:
        name = wp_info['common_name']
        print( 'using common name {}...'.format(name),end='')
        return name

   
    print('Could not fetch country name {}'.format(wp_info))
    return None

# test de la fonction get_name : 
    
#mex = get_info('mexique')
#mexi= get_name(mex)


# recuperation de la capitale d'un pay à partir de wikipedia 
def get_capital(wp_info):
    
    # cas général
    if 'capital' in wp_info:
        
        # parfois l'information récupérée comporte plusieurs lignes
        # on remplace les retours à la ligne par un espace
        capital = wp_info['capital'].replace('\n',' ')
        
        # le nom de la capitale peut comporter des differents caracteres 
        m = re.match(".*?\[\[([\w\s',.()|-]+)\]\]", capital)
        
        # on récupère le contenu des accolades
        capital = m.group(1)
        
        
        # on prend le premier terme quand on rencontre un separateur
        if '|' in capital:
            capital = capital.split('|').pop()
            
        # Cas particulier : Singapour, Monaco, Vatican
        if ( capital == 'city-state' ):
            capital = wp_info['common_name']
        
        # Cas particulier : Suisse
        if ( capital == 'de jure' and wp_info['common_name'] == 'Switzerland'):
            capital = 'Bern'

        return capital
  
    # FIX manuel (l'infobox ne contient pas l'information)
    if 'common_name' in wp_info and wp_info['common_name'] == 'Palestine':
        return 'Ramallah'
 
    # message d'echec à transmettre 
    print(' Could not fetch country capital {}'.format(wp_info))
    return None

#test de la fonction gat_capital():
#can = get_info('canada')
#cana = get_capital(can)

# cette fonction  recupere les coordonnées des capitales des pays : 

def get_coords(wp_info):

    # S'il existe des coordonnées dans l'infobox du pays (cas le plus courant)
    if 'coordinates' in wp_info:


        #on commance dés le terme "{{coord" suivi d'un zero ou plusieurs espaces puis | , 
        #à partir de ce terme on memorise la chaine la plus longue possible qui ne contient pas le } .
        m = re.match('(?i).*{{coord\s*\|([^}]*)}}', wp_info['coordinates'])

        # l'expression régulière ne colle pas, on affiche la chaîne analysée pour nous aider
        # mais c'est un aveu d'échec, on ne doit jamais se retrouver ici
        if m == None :
            print(' Could not parse coordinates info {}'.format(wp_info['coordinates']))
            return None

        

        str_coords = m.group(1)

        # on renvoie apres la conversion au numerique : 
        if str_coords[0:1] in '0123456789':
            return cv_coords(str_coords)

    # FIX manuel (l'infobox ne contient pas d'information directement exploitable)
    if 'common_name' in wp_info and wp_info['common_name'] == 'the Philippines':
        return cv_coords('14|35|45|N|120|58|38|E')
    if 'common_name' in wp_info and wp_info['common_name'] == 'Tanzania':
        return cv_coords('6|10|23|S|35|44|31|E')

    # On n'a pas trouvé de coordonnées dans l'infobox du pays
    # on essaie avec la page de la capitale 
    capital = get_capital(wp_info)
    if capital:
        print(' Fetching capital coordinates...')
        return get_coords(get_info(capital))

    # Aveu d'échec, on ne doit jamais se retrouver ici
    print(' Could not fetch country coordinates')
    return None

#cette fonction étudie la conversion d'une chaine de caractéres décrivant une position géographique
# en coordonées numériques latitude et longitude . 

def cv_coords(str_coords):
    # on découpe au niveau des "|" 
    c = str_coords.split('|')

    # on extrait la latitude en tenant compte des divers formats
    lat = float(c.pop(0))
    if (c[0] == 'N'):
        c.pop(0)
    elif ( c[0] == 'S' ):
        lat = -lat
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'N' ):
        lat += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'S' ):
        lat += float(c.pop(0))/60
        lat = -lat
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'N' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'S' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        lat = -lat
        c.pop(0)

    # on fait de même avec la longitude
    lon = float(c.pop(0))
    if (c[0] == 'W'):
        lon = -lon
        c.pop(0)
    elif ( c[0] == 'E' ):
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'W' ):
        lon += float(c.pop(0))/60
        lon = -lon
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'E' ):
        lon += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'W' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        lon = -lon
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'E' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        c.pop(0)
    
    # on renvoie un dictionnaire avec les deux valeurs
    return {'lat':lat, 'lon':lon }



#test de la fonction 
#can = get_info('canada')
#cana = get_coords(can)
    



##Mise de place d'une base de données : 
    



conn = sqlite3.connect('countries.sqlite')

#donner le nom de fichier contenant le drapeau du pays 

def get_flag(pays):
    return pays+'.png'
#cette colonne permet de recupérer plus facilement le nom de fichier png contenant le drapeau pour l'afficher.

#ecriture dans la base de données :
    
def save_country(conn,country,info):
    
    # présentation de la commande SQL :
    c = conn.cursor()
    sql = 'INSERT OR REPLACE INTO countries VALUES (?, ?, ?, ?, ?,?,? )'




    #data to save : 
    name = get_name(info)
    capital = get_capital(info)
    coords = get_coords(info)
    flag = get_flag(country)
    continent = 'Amérique du nord'
    c.execute(sql,(country,name,capital,coords['lat'],coords['lon'],flag,continent))
    conn.commit()
    

# premier test avec "jamaica"
    
Jm = get_info('jamaica')
save_country(conn,'jamaica',Jm)

#faire la meme operation pour tout les pays du continents 

north = ['canada','Antigua_and_Barbuda','barbados','belize','Costa_Rica','Cuba','dominica','Dominican_Republic','El_Salvador','Grenada','Guatemala','haiti','Honduras','jamaica','mexico','Nicaragua','panama','Saint_Kitts_and_Nevis','Saint_Lucia','Saint_Vincent_and_the_Grenadines','The_Bahamas','Trinidad_and_Tobago','United_States']

# creation de la base de données et insertion de chaque pays  : 


for l in north : 
    cn = get_info(l)
    save_country(conn,l,cn)


   
# il suffit d'ouvrir le fichier SQl "countries.sql" et visualiser les changements .

