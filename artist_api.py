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
from abc import ABC, abstractmethod
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
    def __init__(self, input_name: str, zsession: zetcom_session.ZetcomSession, init_id=True):
        self.input_name = input_name
        self.name = self.parse_name(input_name)
        self.forename = ''
        self.surename = ''
        self.ulan = ''
        self.wikidata = ''
        self.link = ''
        self.gender = ''
        self.birth = ''
        self.death = ''
        self.placeOfBirth = ''
        self.placeOfDeath = ''
        self.dates = []
        self.livedBefore = ''
        self.livedAfter = ''
        self.epoche = ''
        self.nationalities = []
        self.query_failed = False
        self.zsession = zsession
        self.id = None
        if init_id:
            self._update_id()

    def asrow(self, schema: List[SchemaItem]) ->dict:
        """Return Artist as row for csv writing
        """
        self.update()
        output = {}
        for item in schema:
            if self.__dict__[item.fieldPath] != '':
                output[item.csvField] = self.__dict__[item.fieldPath]
        return output

    def _set_epoche(self):
        """Set epoche
        """
        if self.birth != '':
            year = self.birth.split('.')[-1]
            add_to_year = 2 if int(year[2:]) >= 80 else 1
            ep_year = int(year[0:2]) + add_to_year
            self.epoche = str(ep_year) + '. Jh.'

    def update(self):
        """Set the live span inforamtion
        """
        self.livedBefore = self.updateLivedBefore()
        self.livedAfter = self.updateLivedAfter()
        self.link = self.wikidata if self.wikidata != '' else self.ulan
        self._set_epoche()

    def updateLivedBefore(self) ->str:
        if len(self.dates) > 0:
            return self.dates[0]
        return ''

    def updateLivedAfter(self) ->str:
        if len(self.dates) > 0:
            return self.dates[-1]
        return ''

    @classmethod
    def parse_name(cls, input_name) -> str:
        name = input_name.replace('"','').strip()
        if '(' in name:
            name = name.split('(')[0].strip()
        return name 

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

class ArtistAPI(ABC):
    """This class can be used to update artists 
    """

    def __init__(self, endpoint): 
        self.sparql = SPARQLWrapper(endpoint, "")
        self.sparql.setReturnFormat(JSON)

    @abstractmethod
    def _create_query(self, artist: Artist) ->str:
        """Abstract method: create the query
        """
        pass

    @abstractmethod
    def _process_response(self, response: dict, artist: Artist):
        """Abstract method: process result 
        """
        pass

    @abstractmethod
    def _process_exception(self, e: Exception, artist: Artist) ->int:
        """Abstract method: process result 
        """
        pass

    def query_artist(self, artist: Artist) ->int:
        query = self._create_query(artist)
        self.sparql.setQuery(query)
        try:
            response = self.sparql.queryAndConvert()
            self._process_response(response, artist)
            artist.query_failed = False
            return 0
        except Exception as e:
            self._process_exception(e, artist)
