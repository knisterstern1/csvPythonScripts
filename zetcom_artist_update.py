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
from getty_artist import Artist, Getty
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 
       

class ZetcomArtistUpdate:
    """This class can be used to update artists 
    """
    OUTPUT_SCHEMA: List[SchemaItem] = [ SchemaItem('Nachname', 'surename'), SchemaItem('Vorname','forename'),\
            SchemaItem('Daten1_Datum', 'birth'),SchemaItem('Daten2_Datum','death'),SchemaItem('Geschlecht','gender')]
    EXISTING_SCHEMA: List[SchemaItem] = [ SchemaItem('ID','id'), SchemaItem('Person','name')]

    def __init__(self, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()
        self.getty = Getty()
       
    def close(self):
        self.zsession.close()

    def process_getty(self, artist: Artist, new_artists: List[Artist]):
        self.getty.query_artist(artist)
        new_artists.append(artist)
        print(f'Getty update: {artist.__dict__}')

    def process_file(self, csvFile: str, output_file='', existing_out='') ->int:
        new_artists: List[Artist]  = []
        existing_artists: List[Artist] = []
        unknown_artists: List[Artist] = []
        with open(csvFile, newline='') as openFile: 
            reader = csv.DictReader(openFile)
            unkown = 'Unknown artist'
            currentArtist: Artist = None
            counter = 0
            for row in reader:
                name = row['Artist'].strip() if not row['Artist'].startswith(unkown) else 'unbekannt'
                if currentArtist is None:
                    currentArtist = Artist(name, self.zsession)
                elif currentArtist.input_name != name:
                    if currentArtist.id is None:
                        self.process_getty(currentArtist, new_artists)
                    else:
                        existing_artists.append(currentArtist)
                        print(f'Exists: {currentArtist.__dict__}')
                    currentArtist = Artist(name, self.zsession)
                currentArtist.addDate(row['Date'])
            if currentArtist.id is None:
                self.process_getty(currentArtist, new_artists)
            else:
                existing_artists.append(currentArtist)
                print(f'Exists: {currentArtist.__dict__}')
        if len(new_artists) > 0 and output_file != '':
            self.write_artists(new_artists, output_file, self.OUTPUT_SCHEMA, unknown_artists)
        if len(existing_artists) > 0 and existing_out != '':
            self.write_artists(existing_artists, existing_out, self.EXISTING_SCHEMA)
        if len(unknown_artists) > 0:
            self.write_artists(unknown_artists, 'unknown_artists.csv', [SchemaItem('Name','name')])
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
                if len(row.keys()):
                    writer.writerow(row)  
                elif unknown is not None:
                    print(f'Unknown artists: {artist.__dict__}')
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
    try:
        opts, args = getopt.getopt(argv, "he:f:o:s:u:x:", ["help", "existing-out=","file=","output=","server=", "user=", "xml="])
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
        elif opt in ('-o', '--output'):
            output_file = arg
        elif opt in ('-s', '--server'):
            zetcom_server = arg
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-x', '--xml'):
            xml_file = arg
    if csv_file != '':
        output_file = output_file if output_file != '' else 'artist_output_' + csv_file
        artist = ZetcomArtistUpdate(username, zetcom_server)
        artist.process_file(csv_file, output_file)
        artist.close()
        #return process_file(csv_file)
    else:
        usage()
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

