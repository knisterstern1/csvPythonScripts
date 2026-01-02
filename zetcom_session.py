#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program can be used to exchange data between topoTEI and the dsp stack.
"""
#    Copyright (C) University of Basel 2024  {{{1
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
import getpass
import getopt
import glob
import json
import keyring
import keyring.util.platform_ as keyring_platform
import os
import requests
import sys
import urllib.parse
import xml.dom.minidom as MD
from xml.etree import ElementTree
import lxml.etree as LET
from typing import List

DEBUG = False 
GENDER_DICT = { 'male': 'männlich',\
                'female': 'weiblich',\
                'divers': 'divers',\
                'non-binary': 'divers',\
                'trans woman': 'weiblich',\
                'trans man': 'männlich',\
                'trans male': 'männlich',\
                'trans female': 'weiblich'}

def get_mplus_gender(gender_in: str) ->str:
    """Return german gender from mplus voc
    """
    if gender_in in GENDER_DICT.keys():
        return GENDER_DICT[gender_in]
    return gender_in

class DataItem:
    def __init__(self, fieldPath: str, operand: str):
        self.fieldPath = fieldPath
        self.operand = operand.strip()


    def __str__(self):
        return f'{self.fieldPath}: {self.operand}|'

class SchemaItem:
    def __init__(self, csvField: str, fieldPath: str, testFunction=None):
        self.fieldPath = fieldPath
        self.csvField = csvField
        self.testFunction = testFunction

class ZetcomSession:
    """A zetcom session class.
    """
    def __init__(self, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.server = server
        self.username = username
        self.session = requests.Session()
        self.key = None

    def get_json(self, url: str) ->List[dict]:
        """GET a json and return a List of dictonaries 
        """
        get_url = self.server + url
        response = self.session.get(get_url)
        if response.status_code == 200:
           return json.loads(response.content) 
        else:
            raise Exception(response.status_code)

    def get(self, url: str) -> LET:
        """GET a xml response
        """
        get_url = self.server + url
        response = self.session.get(get_url)
        if response.status_code == 200:
           return LET.fromstring(response.content) 
        else:
            raise Exception(response.status_code)

    def open(self, attempt=0):
        """Open a session on the server
        """
        auth_url = self.server + '/ria-ws/application/session'
        headers = {"Content-Type": "application/xml"}
        try:
            credentials = keyring.get_credential(self.server, self.username)
            self.session.auth = (f'user[{credentials.username}]', f'password[{credentials.password}]')
        except Exception:
            print(f'Insert password for user {self.username} on server {self.server}')
            password = getpass.getpass()
            keyring.set_password(self.server, self.username, password)
            self.session.auth = (f'user[{self.username}]', f'password[{password}]')
        response = self.session.get(auth_url)
        if response.status_code == 200:
           xml_response = LET.fromstring(response.content) 
           namespaces = { 'session': xml_response.nsmap[None] }
           if len(xml_response.xpath('//session:key', namespaces=namespaces)) > 0:
               self.key = xml_response.xpath('//session:key', namespaces=namespaces)[0].text
               self.session.auth = (f'user[{self.username}]', f'session[{self.key}]')
           else:
               raise Exception('No session key found!')
        elif attempt < 3:
            attempt += 1
            keyring.delete_password(self.server, self.username)
            print(f'Wrong password for {self.username} on server {self.server}, attempt {attempt}')
            self.open(attempt)
        else:
            raise Exception(r.status_code)

    def post(self, url: str, xml_string: str) -> LET:
        """Post to ria application and receive a xml response
        """
        headers = {'Content-Type':'application/xml; charset=UTF-8'}
        response = self.session.post(self.server + url, data=xml_string, headers=headers) 
        if response.status_code == 200:
            return LET.fromstring(response.content)
        else:
            raise Exception(response.status_code)

    def put(self, url: str, xml_string: str) -> LET:
        """Put to ria application and receive a xml response
        """
        headers = {'Content-Type':'application/xml; charset=UTF-8', 'Accept':'application/xml'}
        response = self.session.put(self.server + url, data=xml_string, headers=headers) 
        if response.status_code == 200:
            return LET.fromstring(response.content)
        else:
            raise Exception(response.status_code)


    def close(self):
        if self.key:
            self.session.delete(self.server +  '/ria-ws/application/session/' + self.key)
        self.session.close()
