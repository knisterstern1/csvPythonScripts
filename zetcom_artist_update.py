#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program can be used to update the zetcom ria application.
"""
#    Copyright (C) Christian Steiner 2025  {{{1
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/> 1}}}
from colorama import Fore, Style
import csv
import getpass
import getopt
import glob
import json
import keyring
import keyring.util.platform_ as keyring_platform
import os
import re
import requests
import sys
import urllib.parse
import xml.dom.minidom as MD
from xml.etree import ElementTree
import lxml.etree as LET
import zetcom_session
from artist_api import Artist
from getty_artist import Getty
from wikidata_artist import Wikidata
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 
       

class ZetcomArtistUpdate:
    """This class can be used to update artists 
    """
    OUTPUT_SCHEMA: List[SchemaItem] = [ SchemaItem('Nachname', 'surename'), SchemaItem('Vorname','forename'),\
            SchemaItem('Daten1_Datum', 'birth'),SchemaItem('Daten2_Datum','death'),SchemaItem('Geschlecht','gender'),\
            SchemaItem('Daten1_Ort','placeOfBirth'),SchemaItem('Daten2_Ort','placeOfDeath'), SchemaItem('Zeitraum','epoche'),\
            SchemaItem('Lebensdaten','life_data'),SchemaItem('Input','input_name'),SchemaItem('Website', 'link')]
    EXISTING_SCHEMA: List[SchemaItem] = [ SchemaItem('ID','id'), SchemaItem('Person','name'), SchemaItem('Input','input_name')]

    def __init__(self, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()
        self.getty = Getty()
        self.wikidata = Wikidata()
       
    def close(self):
        self.zsession.close()

    def process_api(self, artist: Artist, new_artists: List[Artist]) ->int:
        exit_code = 0
        print(f'Getty update: {artist.name}')
        exit_code = self.getty.query_artist(artist)
        print(f'Wikidata update: {artist.name}')
        exit_code = self.wikidata.query_artist(artist)
        if len([ item for item in new_artists if item.name == artist.name]) == 0:
            new_artists.append(artist)
        return exit_code

    def process_file(self, csvFile: str, output_file='', existing_out='') ->int:
        new_artists: List[Artist]  = []
        existing_artists: List[Artist] = []
        unknown_artists: List[Artist] = []
        artists = {}
        with open(csvFile, newline='') as openFile: 
            reader = csv.DictReader(openFile)
            header = list(dict(next(reader)).keys())
            print('Creating dictionary ...')
            if "Name" in header and "Vor" in header and "Nach" in header:
                for row in reader:
                    name = row["Name"]
                    key = Artist.parse_name(name)
                    artists[key] = Artist(name, self.zsession)
                    artists[key].addDate(row['Vor'])
                    artists[key].addDate(row['Nach'])
            else:
                unkown = 'Unknown'
                counter = 0
                for row in reader:
                    name = row['Artist'].strip() if not row['Artist'].startswith(unkown) else 'unbekannt'
                    for input_name in name.split(' and '):
                        key = Artist.parse_name(input_name)
                        if key not in artists.keys():
                            artists[key] = Artist(input_name, self.zsession)
                            artists[key].addDate(row['Date'])
                        else:
                            artists[key].addDate(row['Date'])
            print('Processing artists ...')
            for key in sorted(artists.keys()):
                currentArtist = artists[key]
                if currentArtist.id is None:
                    exit_code = self.process_api(currentArtist, new_artists)
                    if exit_code == 429:
                        break
                else:
                    existing_artists.append(currentArtist)
                    print(f'Exists: {currentArtist.name}')
        if len(new_artists) > 0 and output_file != '':
            self.write_artists(new_artists, output_file, self.OUTPUT_SCHEMA, unknown_artists)
        if len(existing_artists) > 0 and existing_out != '':
            self.write_artists(existing_artists, existing_out, self.EXISTING_SCHEMA)
        if len(unknown_artists) > 0:
            self.write_artists(unknown_artists, 'unknown_artists.csv', [SchemaItem('Name','name'), SchemaItem('Lebte vor', 'livedBefore'), SchemaItem('Lebte nach', 'livedAfter')])
        return 0

    def update_file(self, csvFile: str) ->int:
        artists: List[Artist]  = []
        with open(csvFile, newline='') as openFile: 
            reader = csv.DictReader(openFile)
            print('Reading file ...')
            for row in reader:
                artist = Artist('', None, False)
                for schema in self.OUTPUT_SCHEMA:
                    try:
                        artist.__dict__[schema.fieldPath] = row[schema.csvField]
                    except Exception as e:
                        artist.__dict__[schema.fieldPath] = ''
                artist.update()
                artists.append(artist)
        self.write_artists(artists, csvFile, self.OUTPUT_SCHEMA)
        return 0

    def write_artists(self, artists: List[Artist], target_file: str, schema: List[SchemaItem], unknown=None):
        """Write data to csv file
        """
        with open(target_file, 'w', newline='') as writeFile:
            fieldnames = [ item.csvField for item in schema ] 
            writer = csv.DictWriter(writeFile, fieldnames=fieldnames)
            writer.writeheader()
            for artist in artists:
                row = artist.asrow(schema)
                if len([ key for key in row.keys() if key != 'Input' ]) > 0:
                    writer.writerow(row)  
                elif unknown is not None:
                    print(f'Unknown artist: {artist.name}')
                    artist.update()
                    unknown.append(artist)

def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get or post data to a M+ ria application.

    zetcom_artist_update.py [OPTIONS] 

        OPTIONS:
        -h|--help                      show help
        -e|--existing-out              output csv file for existing ids
        -f|--file                      input csv file 
        -o|--output                    output csv file
        -r|--refresh                   update csv file with missing data
        -s|--server + mplus:           provide mplus address
        -u|--user:                     provide username 
    
        :return: exit code (int)
    """
    username = 'SimpleUserTest'
    zetcom_server = 'https://mptest.kumu.swiss'
    xml_file = ''
    csv_file = ''
    output_file = ''
    existing_out = ''
    update = False
    try:
        opts, args = getopt.getopt(argv, "he:f:o:rs:u:x:", ["help", "existing-out=","file=","output=","refresh","server=", "user=", "xml="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-e', '--existing-out'):
            existing_out = arg
        elif opt in ('-f', '--file'):
            csv_file = arg
        elif opt in ('-r', '--refresh'):
            update = True
        elif opt in ('-o', '--output'):
            output_file = arg
        elif opt in ('-s', '--server'):
            zetcom_server = arg
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-x', '--xml'):
            xml_file = arg
    if csv_file != '':
        artist = ZetcomArtistUpdate(username, zetcom_server)
        if update:
            artist.update_file(csv_file)
        else:
            output_file = output_file if output_file != '' else 'artist_output_' + csv_file
            existing_out = existing_out if existing_out != '' else 'existing_' + zetcom_server.split('//')[1].replace('.','-') + '.csv'
            artist.process_file(csv_file, output_file, existing_out)
        artist.close()
        #return process_file(csv_file)
    else:
        usage()
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

