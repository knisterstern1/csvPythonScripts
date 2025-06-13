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
from artist_api import Artist, ArtistAPI
import zetcom_session
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 
QUERY = """
select distinct * {
  ?g skos:exactMatch [ rdfs:label "#NAME#" ];
     foaf:focus/gvp:biographyPreferred ?bio;
      gvp:prefLabelGVP [xl:literalForm ?label ].

     ?bio
       gvp:estStart ?birth;
       gvp:estEnd ?death;

   optional { ?bio  schema:gender [ rdfs:label ?gender ]
      filter langMatches(lang(?gender), "en")
   }
   #filter (  ?birth < "#LIVEDBEFORE#"^^xsd:gYear && ?death >= "#LIVEDAFTER#"^^xsd:gYear)
}
    """
      

class Getty(ArtistAPI):
    """This class can be used to update artists 
    """
    gender_dict = { 'male': 'männlich', 'female': 'weiblich', 'divers': 'divers' }

    def __init__(self, endpoint='https://vocab.getty.edu/sparql.json'): 
        super().__init__( endpoint)

    def _create_query(self, artist: Artist) ->str:
        """Create the query
        """
        query = QUERY.replace('#NAME#', artist.name)
        artist.update()
        if artist.livedBefore != '':
            query = query.replace('#filter', 'filter').replace('#LIVEDBEFORE#', artist.livedBefore).replace('#LIVEDAFTER#', artist.livedAfter)
        return query

    def _process_response(self, response: dict, artist: Artist):
        """Process result 
        """
        if len(response["results"]["bindings"]) > 0:
            artist_data = response["results"]["bindings"][0]
            artist.ulan = artist_data["g"]["value"]
            label = artist_data["label"]["value"]
            if "," in label:
                artist.surename = label.split(',')[0]
                artist.forename = label.split(',')[1].strip()
            else:
                artist.surename = label
            if "gender" in artist_data.keys() and artist_data["gender"]["value"] in self.gender_dict.keys():
                artist.gender = self.gender_dict[artist_data["gender"]["value"]] 
            if "birth" in artist_data.keys():
                artist.birth = artist_data["birth"]["value"]
            if "death" in artist_data.keys():
                artist.death = artist_data["death"]["value"]

    def _process_exception(self, e: Exception, artist: Artist) ->int:
        """Process exception 
        """
        print(Fore.RED + f'With artist {artist.name} there was a exception from getty: {e.message}!' + Style.RESET_ALL)
        return 1
