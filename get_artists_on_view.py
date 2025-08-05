#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program can be used to get all artist on view.
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
from typing import List

DEBUG = False 
XML_SEARCH = b'<?xml version="1.0" encoding="UTF-8"?> \
    <application xmlns="http://www.zetcom.com/ria/ws/module/search" \
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                 xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"> \
                 <modules> \
                    <module name="Person"> \
                        <search limit="7000" offset="0"> \
                            <expert> \
                                <and> \
                                    <startsNotWithField fieldPath="PerObjectRef.ObjCurrentLocationVrt" operand="GW.Raum vis-"/> \
                                     <or> \
                                        <startsWithField fieldPath="PerObjectRef.ObjCurrentLocationVrt" operand="HB"/> \
                                        <startsWithField fieldPath="PerObjectRef.ObjCurrentLocationVrt" operand="NB"/> \
                                        <startsWithField fieldPath="PerObjectRef.ObjCurrentLocationVrt" operand="GW"/> \
                                    </or> \
                                </and> \
                            </expert> \
                            <sort> \
                                <field fieldPath="PerSurNameTxt" direction="Ascending"/> \
                            </sort> \
                        </search> \
                    </module> \
                </modules> \
    </application>'
       

def get_artists_on_view(login_data):
    session = requests.Session()
    session.auth = (f'user[{login_data["user"]}]', f'password[{login_data["password"]}]')
    headers = {'Content-Type':'application/xml; charset=UTF-8'}
    url = login_data['url'] + '/ria-ws/application/module/Person/export/' + login_data['export']
    response = session.post(url, data=XML_SEARCH, headers=headers) 
    session.close()
    if response.status_code == 200:
        return json.loads(response.content)
    else:
        raise Exception(response.status_code)

def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get all artists on view from the m+ ria applications.

    get_artists_on_view.py
    """
    login_data = { 'url': 'https://mptest.kumu.swiss', 'user': 'SimpleUserTest', 'export': '95025' }
    try:
        credentials = keyring.get_credential(login_data['url'],login_data['user'])
        login_data['password'] = credentials.password
    except Exception:
        print(f'Insert password for user {self.username} on server {self.server}')
        password = getpass.getpass()
        keyring.set_password(login_data['url'], login_data['user'], password)
        login_data['password'] = credentials.password
    artists_on_view = get_artists_on_view(login_data)
    print(artists_on_view)
    with open('artists.json', 'w') as f:
        json.dump(artists_on_view, f, ensure_ascii=False)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

