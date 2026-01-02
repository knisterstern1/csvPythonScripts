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
from lxml.etree import Element
import zetcom_session
from zetcom_session import DataItem, SchemaItem
from typing import List

DEBUG = False 


class ZetcomVocUpdate:
    """This class can be used to update vocabulary 
    """
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

    def __init__(self, vocabulary: str, filter_term: str, replace_term: str, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.vocabulary = vocabulary
        self.filter_term = filter_term
        self.replace_term = replace_term
        self.zsession.open()

    def get_nodes(self) -> LET:
        """GET a xml response for all nodes of vocabulary that conform to filter term
        """
        url = '/ria-ws/application/vocabulary/instances/' + self.vocabulary + '/nodes/search/?nodeName=' + self.filter_term 
        return self.zsession.get(url)

    def update_node(self, node: Element, namespaces: dict) ->LET:
        logicalName = node.get('logicalName').replace(self.filter_term, self.replace_term)
        node.set('logicalName', logicalName)
        record_id = node.get('id')
        for content in node.xpath('collection:terms/collection:term/collection:content', namespaces=namespaces):
            content.text = content.text.replace(self.filter_term, self.replace_term)
            term = content.getparent()
            term_id = term.get('id')
            url = '/ria-ws/application/vocabulary/instances/' + self.vocabulary + '/nodes/' + record_id + '/terms/' + term_id
            xml_string = LET.tostring(content.getparent(), encoding='UTF-8')
            self.zsession.put(url, xml_string)
        xml_string = LET.tostring(node, encoding='UTF-8')
        url = '/ria-ws/application/vocabulary/instances/' + self.vocabulary + '/nodes/' + record_id 
        return self.zsession.put(url, xml_string)

    def update(self, xml_tree: LET) ->int:
        namespaces = {}
        namespaces['collection'] = xml_tree.nsmap[None]
        for node in xml_tree.xpath('//collection:collection/collection:node', namespaces=namespaces):
            xml = self.update_node(node, namespaces)    
            print(xml.get('logicalName'))
        return 0
       
    def close(self):
        self.zsession.close()


def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to update a vocabulary from a M+ ria application.

    zetcom_voc_update.py [OPTIONS] 

        OPTIONS:
        -h|--help                      show help
        -f|--filter                    provide a filter term
        -r|--replace                   provide a replace term
        -s|--server + mplus:           provide mplus address
        -u|--user:                     provide username as email address
        -v|--vocabulary:               provide the vocabulary name
    
        :return: exit code (int)
    """
    username = 'SimpleUserTest'
    zetcom_server = 'https://mptest.kumu.swiss'
    vocabulary = 'PerRightsHolderVgr'
    filter_term = '2025'
    replace_term = '2026'
    try:
        opts, args = getopt.getopt(argv, "hf:r:s:u:v:", ["help", "filter=","replace=","server=", "user=", "vocabulary="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-f', '--filter'):
            filter_term = arg
        elif opt in ('-r', '--replace'):
            replace_term = arg
        elif opt in ('-s', '--server'):
            zetcom_server = arg
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-v', '--vocabulary'):
            vocabulary = arg
    voc = ZetcomVocUpdate(vocabulary, filter_term, replace_term, username, zetcom_server)
    xml_tree = voc.get_nodes()
    voc.update(xml_tree)
    voc.close()
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

