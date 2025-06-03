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

TITLE_DICT = {"Dr.": "30134", }
COUNTRY_DICT = {"Argentina": "Argentinien", "Australia": "Australien", "Brazil": "Brasilien", "Canada": "Kanada", "Chile": "Chile", "Colombia": "Kolumbien", "Croatia": "Kroatien", "Denmark": "Dänemark", "Ecuador": "Ecuador", "Finland": "Finnland", "France": "Frankreich", "Germany": "Deutschland", "Italy": "Italien", "Japan": "Japan", "Mexico": "Mexiko", "Monaco": "Monaco", "Netherlands": "Niederlande", "Peru": "Peru", "Slovakia": "Slovakei", "Spain": "Spanien", "Sweden": "Schweden", "Switzerland": "Schweiz", "UK": "Vereinigtes Königreich, Großbritannien", "USA": "Vereinigte Staaten von Amerika", "Wales": "Vereinigtes Königreich, Großbritannien"}
DEBUG = False 

class AddressItem(DataItem):
    def __init__(self, fieldPath: str, operand: str):
        super().__init__(fieldPath, operand)


    def __str__(self):
        return f'{self.fieldPath}: {self.operand}|'


def fix_forename(addressList: List[AddressItem], surnameFieldName='AdrSurNameTxt'):
    lastItem = addressList.pop()
    last_split_content = lastItem.operand.split(' ')
    lastItem.operand = last_split_content[0]
    addressList.append(lastItem)
    addressList.append(AddressItem(surnameFieldName,' '.join(last_split_content[1:]).strip()))

def address_parse_pairs(content, addressList: List[AddressItem]):
    p = re.compile('\s*and\s')
    if p.match(content):
        fix_forename(addressList)
        m = p.match(content)
        address_parse_title(content[m.end():], addressList, 'AdrAcademicTitlePartnerVoc', 'AdrForeNamePartnerTxt')
        fix_forename(addressList, 'AdrSurNamePartnerTxt')
    else:
        addressList.append(AddressItem('AdrSurNameTxt', content.strip())) 

def address_parse_title(content, addressList: List[AddressItem], titleFieldName='AdrAcademicTitleVoc', fornameFieldName='AdrForeNameTxt'):
    p = re.compile('[A-Z][a-z]+\.\s') 
    if p.match(content):
        split_content = content.split(' ')
        title = split_content[0].replace('a','')
        forename = ' '.join(split_content[1:])
        addressList.append(AddressItem(titleFieldName, title)) 
        addressList.append(AddressItem(fornameFieldName, forename.strip())) 
    else:
        addressList.append(AddressItem(fornameFieldName, content.strip())) 

def parse_address_parts(content, addressList: List[AddressItem]):
    p = re.compile('.*\n.*')
    q = re.compile('.*,.*')
    if not p.match(content) and not q.match(content):
        addressList.append(AddressItem('AdrCityTxt', content.strip()))
    else:
        lines = [ line for line in content.split('\n') if line != ''] \
                if p.match(content) and len([ line for line in content.split('\n') if line != '']) > 1\
                else [ line for line in content.split(',') if line != '']
        plz_ort = re.compile('([A-Z]-)*(.*\d)(\s)(\w*)')
        if len(lines) == 2:
            addressList.append(AddressItem('AdrStreeTxt', lines[0]))
            if plz_ort.match(lines[1]):
                plz_ort_groups = plz_ort.match(lines[1]).groups()
                addressList.append(AddressItem('AdrPostcodeTxt', plz_ort_groups[1]))
                addressList.append(AddressItem('AdrCityTxt', plz_ort_groups[-1]))
            else:
                addressList.append(AddressItem('AdrCityTxt', lines[1]))
        else:
            plz = re.compile('.*\d.*')
            if plz.match(lines[-1]):
                addressList.append(AddressItem('AdrPostcodeTxt', lines[-1]))
                addressList.append(AddressItem('AdrCityTxt', lines[-2]))
                addressList.append(AddressItem('AdrStreeTxt','\n'.join(lines[0:-2])))
            elif plz.match(lines[-2]):
                addressList.append(AddressItem('AdrPostcodeTxt', lines[-2]))
                addressList.append(AddressItem('AdrCityTxt', lines[-1]))
                addressList.append(AddressItem('AdrStreeTxt','\n'.join(lines[0:-2])))
            else:
                if plz_ort.match(lines[-1]):
                    plz_ort_groups = plz_ort.match(lines[1]).groups()
                    addressList.append(AddressItem('AdrPostcodeTxt', plz_ort_groups[1]))
                    addressList.append(AddressItem('AdrCityTxt', plz_ort_groups[-1]))
                else:
                    addressList.append(AddressItem('AdrCityTxt', lines[-1]))
                addressList.append(AddressItem('AdrStreeTxt','\n'.join(lines[0:-1])))

def update_country_information(content, addressList: List[AddressItem]):
    country_key = content.strip() 
    if country_key in COUNTRY_DICT.keys():
        country_key = COUNTRY_DICT[country_key]
    addressList.append(AddressItem('AdrCountryVoc', country_key))

def parse_pair_emails(content, addressList: List[AddressItem]):
    k = re.compile('.*@.*,.*@.*')
    if k.match(content):
        emails = [ email.strip() for email in content.split(',') ]
        addressList.append(AddressItem('AdrContactGrp1', emails[0]))
        addressList.append(AddressItem('AdrContactGrp2', emails[1]))
    else:
        addressList.append(AddressItem('AdrContactGrp1', content))

class ZetcomAddressUpdates:
    """This class can be used to update address
    """
    OUTPUT_SCHEMA: List[SchemaItem] = [ SchemaItem('Adresstyp', 'AdrPersonTypeVoc'), SchemaItem('Institution', 'AdrOrganisationTxt'),\
            SchemaItem('Nachname', 'AdrSurNameTxt'), SchemaItem('Vorname','AdrForeNameTxt'), SchemaItem('Titel', 'AdrAcademicTitleVoc'),\
            SchemaItem('Nachname2','AdrSurNamePartnerTxt'), SchemaItem('Vorname2', 'AdrForeNamePartnerTxt'), SchemaItem('Titel2', 'AdrAcademicTitlePartnerVoc'),\
            SchemaItem('Language', 'AdrLanguageVoc'), SchemaItem('Funktion','AdrFunctionVoc'), SchemaItem('E-Mail', 'AdrContactGrp1'), SchemaItem('E-Mail2', 'AdrContactGrp2'),\
            SchemaItem('Address', 'AdrStreeTxt'), SchemaItem('PLZ', 'AdrPostcodeTxt'), SchemaItem('Ort', 'AdrCityTxt'), SchemaItem('Land', 'AdrCountryVoc')
            ]
    DEFAULT_SCHEMA: List[SchemaItem] = [ SchemaItem('Institution', 'AdrOrganisationTxt'), SchemaItem('First_Name', 'AdrForeNameTxt', address_parse_title),\
            SchemaItem('Last_Name', 'AdrSurNameTxt', address_parse_pairs), SchemaItem('Country', 'AdrCountryVoc', update_country_information), SchemaItem('Title', 'AdrFunctionVoc'),\
            SchemaItem('Address', 'AdrStreetTxt', parse_address_parts), SchemaItem('Email', 'AdrContactGrp1', parse_pair_emails)\
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
        self.address_types = {}
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()
        self._init_addr_type_dict()
       
    def _init_addr_type_dict(self):
        """Initialize the address type dictionary
        """
        self.addr_type_dict = {}
        namespaces = {}
        xml_tree = self.zsession.get("/ria-ws/application/vocabulary/instances/AdrPersonTypeVgr/nodes/search")
        namespaces['collection'] = xml_tree.nsmap[None]
        nodes = xml_tree.xpath('//collection:collection/collection:node', namespaces=namespaces)
        for node in nodes:
            self.addr_type_dict[node.attrib['logicalName']] = node.attrib['id'] 

    def address_id(self, addressItems: List[AddressItem]) ->str:
        """Get address id or None if it does not exist
        """
        namespaces = {}
        search_tree = LET.fromstring(self.XML_SEARCH)
        namespaces['search'] =  search_tree.nsmap[None]
        andNode = search_tree.xpath('//search:expert/search:and', namespaces=namespaces)[0]
        if len(addressItems) == 1:
            addressItems.append(AddressItem('AdrPersonTypeVoc', self.addr_type_dict['institution']))
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
        testFunction = schema.testFunction
        if testFunction is None:
            addressList.append(AddressItem(fieldPath, operand.strip()))
        else:
            testFunction(operand, addressList)
            
    def append_address_type(self, addressList: List[AddressItem]):
        partnerField = 'AdrForeNamePartnerTxt'
        if len([ item for item in addressList if item.fieldPath == partnerField ]) > 0:
            addressList.append(AddressItem('AdrPersonTypeVoc', 'couple'))
        elif len([ item for item in addressList if item.fieldPath == 'AdrForeNameTxt' and item.operand == '' ]) > 0 \
                and len([ item for item in addressList if item.fieldPath == 'AdrSurNameTxt' and item.operand == '' ]) > 0:
            addressList.append(AddressItem('AdrPersonTypeVoc', 'institution'))
        else:
            addressList.append(AddressItem('AdrPersonTypeVoc', 'person'))

    def get_search_items(self, addressList: List[AddressItem]) -> List[AddressItem]:
        if len([item for item in addressList if item.fieldPath == 'AdrPersonTypeVoc' and item.operand == 'institution']) == 1:
            return [item for item in addressList if item.fieldPath == 'AdrOrganisationTxt']
        else:
            fieldPaths = ['AdrOrganisationTxt', 'AdrForeNameTxt', 'AdrSurNameTxt']
            return [item for item in addressList if item.fieldPath in fieldPaths]

    def process_file(self, csvFile: str, targetFile='') ->int:
        output_rows: List[dict]  = []
        output_existing_ids = []
        with open(csvFile, newline='') as openFile: 
            reader = csv.DictReader(openFile)
            ignoreString = 'Source not yet identified'
            lastInstitution = ''
            lastName = ''
            counter = 0
            for row in reader:
                addressList: List[AddressItem] = []
                if not row['Institution'].startswith(ignoreString) and row['Institution'] != lastInstitution and row['First_Name'].strip() + row['Last_Name'].strip() != lastName:
                    lastInstitution = row['Institution']
                    lastName = row['First_Name'].strip() + row['Last_Name'].strip()
                    for schema in self.schemas:
                        self.append_address_item(row, schema, addressList)
                    self.append_address_type(addressList)
                    search_items = self.get_search_items(addressList)
                    addr_id = self.address_id(search_items)
                    if addr_id is None:
                        self.print_row(addressList, output_rows)
                    else:
                        output_existing_ids.append(addr_id)
                    counter += 1
        if targetFile != '':
            with open(targetFile, 'w', newline='') as writeFile:
                fieldnames = [ schema.csvField for schema in self.OUTPUT_SCHEMA ] 
                writer = csv.DictWriter(writeFile, fieldnames=fieldnames)
                writer.writeheader()
                for row in output_rows:
                    writer.writerow(row)
        if len(output_existing_ids) > 0:
            id_file = targetFile.replace('.csv','.txt')
            with open(id_file, 'a') as writeIdFile:
                for old_addr_id in output_existing_ids:
                    writeIdFile.write(old_addr_id + '\n')
        return 0

    def print_row(self, addressList: List[AddressItem], output_rows: List[dict]):
        addressDict = {}
        for schema in self.OUTPUT_SCHEMA:
            item = [ item for item in addressList if item.fieldPath == schema.fieldPath ]
            if len(item) > 0:
                addressDict[schema.csvField] = item[0].operand
                print(f'\"{item[0].operand}\"', end=",")
            else:
                addressDict[schema.csvField] = "" 
                print('\"\"', end=",")
        output_rows.append(addressDict)
        print()

def print_address_fields(counter, addressList: List[AddressItem]):
    print(str(counter) + "|", end='')
    for item in addressList:
        print(item, end='')
    print()

def process_file(csvFile):
    with open(csvFile, newline='') as openFile: 
        reader = csv.DictReader(openFile)
        ignoreString = 'Source not yet identified'
        lastInstitution = ''
        lastName = ''
        for row in reader:
            if not row['Institution'].startswith(ignoreString) and row['Institution'] != lastInstitution and row['First_Name'].strip() + row['Last_Name'].strip() != lastName:
                lastInstitution = row['Institution']
                lastName = row['First_Name'].strip() + row['Last_Name'].strip()
                print(row['Country'])
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
        output_file = output_file if output_file != '' else 'address_output_' + csv_file
        address = ZetcomAddressUpdates([], username, zetcom_server)
        address.process_file(csv_file, output_file)
        address.close()
        #return process_file(csv_file)
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

