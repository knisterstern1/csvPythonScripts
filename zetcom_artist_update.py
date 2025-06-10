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
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 
       
class Artist:
    XML_SEARCH = b'<?xml version="1.0" encoding="UTF-8"?> \
    <application xmlns="http://www.zetcom.com/ria/ws/module/search" \
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                 xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"> \
                 <modules> \
                    <module name="Person"> \
                        <search limit="10" offset="0"> \
                            <select><field fieldPath="__id"/></select> \
                            <fulltext/> \
                        </search> \
                    </module> \
                </modules> \
    </application>'
    def __init__(self, input_name: str, zsession: zetcom_session.ZetcomSession):
        self.input_name = input_name
        self.name = self._init_name()
        self.dates = []
        self.zsession = zsession
        self.id = None
        self._update_id()

    def livedBefore(self) ->str:
        if len(self.dates) > 0:
            return self.dates[0]
        return ''

    def livedAfter(self) ->str:
        if len(self.dates) > 0:
            return self.dates[-1]
        return ''

    def _init_name(self) -> str:
        return self.input_name.strip() 

    def _update_id(self):
        """Get Artist id or None
        """
        namespaces = {}
        search_tree = LET.fromstring(self.XML_SEARCH)
        namespaces['search'] =  search_tree.nsmap[None]
        fulltext = search_tree.xpath('//search:fulltext', namespaces=namespaces)[0]
        fulltext.text = self.name 
        xml_string = LET.tostring(search_tree, encoding='UTF-8')
        xml = self.zsession.post('/ria-ws/application/module/Person/search', xml_string) 
        namespaces['module'] = xml.nsmap[None] 
        if len(xml.xpath('//module:module/module:moduleItem', namespaces=namespaces)) > 0:
            self.id = xml.xpath('//module:module/module:moduleItem/@id', namespaces=namespaces)[0]

    def addDate(self, dateStr: str):
        """Add a date and sort the date list
        """
        date = re.compile('(\D+)*(\d{4})(\D\d{2,4})*(\D+)*')
        century = re.compile('(\D+)*(\d{2})(.*century.*)')
        if date.match(dateStr):
            date_group = date.match(dateStr).groups()
            self.dates.append(date_group[1])
            if date_group[2] is not None:
                second_date = date_group[2][1:]
                self.dates.append(second_date)
        elif century.match(dateStr):
            date_group = century.match(dateStr).groups()
            century_years = (int(date_group[1]) -1)*100
            years = 50
            if date_group[0] is not None and re.match(r'(?i)early', date_group[0]):
                years = 25
            elif date_group[0] is not None and re.match(r'(?i)late', date_group[0]):
                years = 75
            self.dates.append(str(century_years + years))
        self.dates.sort()




class ZetcomArtistUpdate:
    """This class can be used to update address
    """
    

    def __init__(self, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()
       
    def close(self):
        self.zsession.close()

    def process_getty(self, artist: Artist):
        print(artist.__dict__)

    def process_file(self, csvFile: str, targetFile='') ->int:
        output_rows: List[dict]  = []
        output_existing_ids = []
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
                        self.process_getty(currentArtist)
                    currentArtist = Artist(name, self.zsession)
                currentArtist.addDate(row['Date'])
            if currentArtist.id is None:
                self.process_getty(currentArtist)
        return 0


def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get or post data to a M+ ria application.

    zetcom_artist_update.py [OPTIONS] 

        OPTIONS:
        -h|--help                      show help
        -f|--file                      input csv file 
        -o|--output                    output csv file
        -s|--server + mplus:           provide mplus address
        -u|--user:                     provide username as email address
    
        :return: exit code (int)
    """
    username = 'SimpleUserTest'
    zetcom_server = 'https://mptest.kumu.swiss'
    xml_file = ''
    csv_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv, "hf:o:s:u:x:", ["help", "file=","output=","server=", "user=", "xml="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
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
        artist = ZetcomArtistUpdate([], username, zetcom_server)
        artist.process_file(csv_file, output_file)
        artist.close()
        #return process_file(csv_file)
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

