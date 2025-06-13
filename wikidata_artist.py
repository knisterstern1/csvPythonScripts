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
from SPARQLWrapper import SPARQLWrapper, JSON
import sys
import urllib.parse
import xml.dom.minidom as MD
from xml.etree import ElementTree
import lxml.etree as LET
import time
from artist_api import Artist, ArtistAPI
import zetcom_session
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 
QUERY = """
SELECT DISTINCT ?item ?itemLabel ?birth ?VornameLabel ?FamiliennameLabel ?death ?genderLabel ?placeOfBirthLabel ?placeOfDeathLabel WHERE {
  hint:Query hint:optimizer "None".
  SERVICE wikibase:mwapi {
    bd:serviceParam wikibase:api "Search";
      wikibase:endpoint "www.wikidata.org";
      mwapi:srsearch "'#NAME#' haswbstatement:P31=Q5".
    ?item wikibase:apiOutputItem mwapi:title.
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],de,en". }
  OPTIONAL { ?item wdt:P735 ?Vorname. }
  OPTIONAL { ?item wdt:P734 ?Familienname. }
  #VALUES ?livedBefore {"+#LIVEDBEFORE#-01-01"^^xsd:dateTime} 
  #VALUES ?livedAfter {"+#LIVEDAFTER#-01-01"^^xsd:dateTime} 
  ?item wdt:P569 ?birth;
    wdt:P570 ?death.
  #filter((YEAR(?birth)) < YEAR(?livedBefore))
  #filter(YEAR(?death) >= YEAR(?livedAfter))
  OPTIONAL { ?item wdt:P21 ?gender. }
  OPTIONAL { ?item wdt:P20 ?placeOfDeath. }
  OPTIONAL { ?item wdt:P19 ?placeOfBirth. }
}
    """
       
class Wikidata(ArtistAPI):
    """This class can be used to update artists 
    """

    def __init__(self, endpoint='https://query.wikidata.org/sparql'): 
        super().__init__(endpoint)

    def _parse_date(self, date_str: str) ->str:
        """Parses a date and returns it in the format 'dd.mm.yyyy'
        """
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        date_parts = date_str.split('-')
        if len(date_parts) > 2: 
            return f'{date_parts[2]}.{date_parts[1]}.{date_parts[0]}'
        elif len(date_parts) > 1:
            return f'{date_parts[1]}.{date_parts[0]}'
        else:
            return f'{date_parts[0]}'

    def _create_query(self, artist: Artist) ->str:
        """Create the query
        """
        query = QUERY.replace('#NAME#', artist.name)
        artist.update()
        if artist.livedBefore != '':
            query = query.replace('#filter', 'filter').replace('#VALUES','VALUES').replace('#LIVEDBEFORE#', artist.livedBefore).replace('#LIVEDAFTER#', artist.livedAfter)
        return query

    def _process_response(self, response: dict, artist: Artist):
        """Process result 
        """
        if len(response["results"]["bindings"]) > 0:
            artist_data = response["results"]["bindings"][0]
            artist.wikidata = artist_data["item"]["value"]
            label = artist_data["itemLabel"]["value"]
            alt_forename = artist.forename 
            if "VornameLabel" in artist_data.keys():
                if artist.forename != '':
                    artist.forename = alt_forename
                    alt_forename = artist_data["VornameLabel"]["value"]
                else:
                    artist.forename = artist_data["VornameLabel"]["value"]
            if "FamiliennameLabel" in artist_data.keys():
                artist.surename = artist_data["FamiliennameLabel"]["value"]
            elif len(label.split(artist.forename + ' ')) > 1 or len(label.split(alt_forename + ' ')) > 1:
                split_str = artist.forename \
                            if (len(label.split(artist.forename + ' ')) >= len(label.split(alt_forename + ' '))) \
                            else alt_forename
                artist.surename = ' '.join(label.split(split_str + ' ')[1:])
                if artist.forename == '':
                    artist.forename = label.split(' ')[0]
            if "genderLabel" in artist_data.keys():
                artist.gender = artist_data["genderLabel"]["value"] 
            if "birth" in artist_data.keys():
                artist.birth = self._parse_date(artist_data["birth"]["value"])
            if "death" in artist_data.keys():
                artist.death = self._parse_date(artist_data["death"]["value"])
            if "placeOfBirthLabel" in artist_data.keys():
                artist.placeOfBirth = self._parse_date(artist_data["placeOfBirthLabel"]["value"])
            if "placeOfDeathLabel" in artist_data.keys():
                artist.placeOfDeath = self._parse_date(artist_data["placeOfDeathLabel"]["value"])

    def _process_exception(self, e: Exception, artist: Artist) ->int:
        """Process exception 
        """
        status = '429' in e and not artist.query_failed
        print(Fore.RED + f'With artist {artist.name} there was a exception from getty: {e}! {status}' + Style.RESET_ALL)
        if status:
            sleep = 70
            print(Fore.BLUE + f'Query the api again for  in {sleep}s ...' + Style.RESET_ALL)
            artist.query_failed = True
            for i in reversed(range(0, sleep)):
                print(Fore.MAGENTA + f"{i}s" + Style.RESET_ALL, end="\r", flush=True)
                sleep(1)
            return self.query_artist(artist)
        elif artist.query_failed:
            return 429
        else:
            return 1
