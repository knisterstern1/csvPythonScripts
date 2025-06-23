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
       

class AnnotationUpdate:
    """This class can be used to update artists 
    """

    def __init__(self, username="SimpleUserTest", server='https://mptest.kumu.swiss'): 
        self.zsession = zetcom_session.ZetcomSession(username, server)
        self.zsession.open()

    def close(self):
        self.zsession.close()

    def _get_new_link(self, old_link: str) ->str:
        """Get a new link for old_link
        """
        file_name = old_link.split('/')[-1]
        if len([ i for i in file_name.split('_') if re.match(r'^[0-9]{7}$', i) ]) > 0:        
            obj_id = [ i for i in file_name.split('_') if re.match(r'^[0-9]{7}$', i) ][0]
            print(obj_id)
        return old_link

    def _process_array(self, exhibits: List[dict]):
        """Process exhibits.
        """
        for exhibit in exhibits:
            if "link" in exhibit.keys() and "de" in exhibit["link"].keys() and '?' in exhibit["link"]["de"]:
                link = exhibit["link"]["de"].split('?')[0]
                try: 
                    response = requests.get(link + '/info.json')
                    if response.text == 'Not found':
                        #new_link = self._get_new_link(link)
                        print(link.split('/')[-1])
                except Exception as e:
                    print(e)

    def process_file(self, json_file: str, output_file: str):
        """Process json file.
        """
        with open(json_file) as jf:
            data = json.load(jf)
            if 'annotations' in data.keys():
                self._process_array(data['exhibits'])
       
def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get or post data to a M+ ria application.

    annotations_update.py [OPTIONS] 

        OPTIONS:
        -h|--help                    show help
        -j|--json                    input json file 
        -o|--output                  output json file
        -s|--server + mplus:         provide mplus address
        -u|--user:                   provide username 
    
        :return: exit code (int)
    """
    username = 'TCH'
    zetcom_server = 'https://mpbaselkumu.zetcom.com'
    json_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv, "he:j:o:s:u:x:", ["help", "json=","output=","server=", "user="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-j', '--json'):
            json_file = arg
        elif opt in ('-o', '--output'):
            output_file = arg
        elif opt in ('-s', '--server'):
            zetcom_server = arg
        elif opt in ('-u', '--user'):
            username = arg
    exit_code = 0
    if json_file != '':
        output_file = output_file if output_file != '' else json_file.replace('.json','_out.json')
        annotations_update = AnnotationUpdate(username, zetcom_server)
        exit_code = annotations_update.process_file(json_file, output_file)
        annotations_update.close()
        #return process_file(csv_file)
    else:
        usage()
    return exit_code 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

