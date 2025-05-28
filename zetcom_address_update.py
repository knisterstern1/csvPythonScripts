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
from typing import List

DEBUG = False 


class AddressItem:
    def __init__(self, fieldPath: str, operand: str):
        self.fieldPath = fieldPath
        self.operand = operand
        self.addr_id = None

    def add(addr_id: str):
        self.addr_id = addr_id

    def __str__(self):
        return f'fieldPath: {self.fieldPath}, operand: {self.operand}, addr_id: {self.addr_id}'

class SchemaItem:
    def __init__(self, csvField: str, fieldPath: str, testFunction=None):
        self.fieldPath = fieldPath
        self.csvField = csvField
        self.testFunction = testFunction

def address_parse_title(content, addressList: List[AddressItem]):
    p = re.compile('[A-Z][a-z]+\.\s') 
    if p.match(content):
        split_content = content.split(' ')
        title = split_content[0].replace('a','')
        forename = split_content[1]
        addressList.append(AddressItem('AdrAcademicTitleVoc',title)) 
        addressList.append(AddressItem('AdrForeNameTxt',forename)) 

class ZetcomAddressUpdates:
    """This class can be used to update address
    """
    DEFAULT_SCHEMA: List[SchemaItem] = [ SchemaItem('Institution', 'AdrOrganisationTxt'), SchemaItem('First_Name', 'AdrForeNameTxt', address_parse_title),\
            SchemaItem('Last_Name', 'AdrSurNameTxt'), SchemaItem('Country', 'AdrCountryVoc')
            ]
    XML_SEARCH = b'<?xml version="1.0" encoding="UTF-8"?> \
    <application xmlns="http://www.zetcom.com/ria/ws/module/search" \
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                 xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"> \
                 <modules> \
                    <module name="Address"> \
                        <search limit="10" offset="0"> \
                            <select><field fieldPath="__id"/></select> \
                            <expert><and/></expert> \
                        </search> \
                    </module> \
                </modules> \
    </application>' 

    def __init__(self, schemas: List[SchemaItem], username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        if len(schemas) > 0:
            self.schemas = schemas
        else:
            self.schemas = self.DEFAULT_SCHEMA
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()
        
    def address_id(self, addressItems: List[AddressItem]) ->str:
        """Get address id or None if it does not exist
        """
        namespaces = {}
        search_tree = LET.fromstring(self.XML_SEARCH)
        namespaces['search'] =  search_tree.nsmap[None]
        andNode = search_tree.xpath('//search:expert/search:and', namespaces=namespaces)[0]
        for item in addressItems:
            element = LET.Element("equalsField")
            element.attrib['fieldPath'] = item.fieldPath
            element.attrib['operand'] = item.operand
            andNode.append(element)
        xml_string = LET.tostring(search_tree, encoding='UTF-8')
        xml = self.zsession.post('/ria-ws/application/module/Address/search', xml_string) 
        namespaces['module'] = xml.nsmap[None] 
        if len(xml.xpath('//module:module/module:moduleItem', namespaces=namespaces)) > 0:
            return xml.xpath('//module:module/module:moduleItem/@id', namespaces=namespaces)[0]
        else:
            return None

    def close(self):
        self.zsession.close()

    def append_address_item(self, row: dict, schema: SchemaItem, addressList: List[AddressItem]):
        operand = row[schema.csvField]
        fieldPath = schema.fieldPath
        addressList.append(AddressItem(fieldPath, operand))

    def process_file(self, csvFile: str, targetFile='') ->int:
        with open(csvFile, newline='') as openFile: 
            reader = csv.DictReader(openFile)
            ignoreString = 'Source not yet identified'
            lastInstitution = ''
            lastName = ''
            for row in reader:
                addressList: List[AddressItem] = []
                if not row['Institution'].startswith(ignoreString) and row['Institution'] != lastInstitution and row['First_Name'].strip() + row['Last_Name'].strip() != lastName:
                    lastInstitution = row['Institution']
                    lastName = row['First_Name'].strip() + row['Last_Name'].strip()
                    for schema in self.schemas:
                        self.append_address_item(row, schema, addressList)
                    for item in addressList:
                        print(item)
        return 0

def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get or post data to a M+ ria application.

    zetcom_test.py [OPTIONS] 

        OPTIONS:
        -h|--help                      show help
        -s|--server + zetcom_server:   provide dsp_server address
        -u|--user:                     provide username as email address
    
        :return: exit code (int)
    """
    username = 'SimpleUserTest'
    zetcom_server = 'https://mptest.kumu.swiss'
    xml_file = ''
    try:
        opts, args = getopt.getopt(argv, "hs:u:x:", ["help", "server=", "user=", "xml="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-s', '--server'):
            dsp_server = arg
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-x', '--xml'):
            xml_file = arg
    return process_file()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

