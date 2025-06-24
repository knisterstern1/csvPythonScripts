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
from typing import List

DEBUG = False 
       

class AnnotationUpdate:
    """This class can be used to update artists 
    """

    def __init__(self, csv_file: str, debug=False):
        self.objects = {}
        if not debug:
            print(Fore.LIGHTBLUE_EX + f'Initializing objects from {csv_file} ...' + Style.RESET_ALL)
            with open(csv_file, newline='') as openFile: 
                reader = csv.DictReader(openFile)
                counter = 0
                for row in reader:
                    counter += 1
                    key = "{:07d}".format(int(row["ID"]))
                    link = row["Picturepark IIIF URL"].replace('<','').replace('>','')
                    print(Fore.CYAN + f'{key} -> {link}' + Style.RESET_ALL)
                    self.objects[key] = link
            print(Fore.LIGHTBLUE_EX + f' ...{counter} initialized' + Style.RESET_ALL)

    def _get_object_id(self, link) ->str:
        file_name = link.split('/')[-1]
        if len([ i for i in file_name.split('_') if re.match(r'^[0-9]{7}$', i) ]) > 0:        
            obj_id = [ i for i in file_name.split('_') if re.match(r'^[0-9]{7}$', i) ][0]
            return obj_id
        return ''

    def _is_link_valid(self, link: str) ->bool:
        """Tests if a link is valid.
        """
        try: 
            response = requests.get(link + '/info.json')
            if response.text == 'Not found':
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    def _update_links(self, links: dict, new_link: str):
        """Update the links
        """
        for key in links.keys():
            options = links[key].split('?')[-1]
            links[key] = new_link + '?' + options

    def _process_array(self, exhibits: List[dict], not_found: List[dict]):
        """Process exhibits.
        """
        for exhibit in exhibits:
            if "link" in exhibit.keys() and "de" in exhibit["link"].keys() and '?' in exhibit["link"]["de"]:
                link = exhibit["link"]["de"].split('?')[0]
                if not self._is_link_valid(link):
                    print(Fore.LIGHTBLUE_EX + f'unsupported link found: {link}' + Style.RESET_ALL)
                    obj_id = self._get_object_id(link)
                    if obj_id != '' and obj_id in self.objects.keys() and self._is_link_valid(self.objects[obj_id]):
                        new_link = self.objects[obj_id]
                        self._update_links(exhibit["link"], new_link)
                        print(f'new_link: {new_link}' + Style.RESET_ALL)
                    else:
                        key = obj_id if obj_id != '' else link.split('/')[-1]
                        not_found.append({ 'ID': key, 'URL': link})
                
    def process_file(self, json_file: str, output_file: str):
        """Process json file.
        """
        not_found = []
        unkown_iiif = 'unkown_iiif.csv'
        with open(json_file) as jf:
            data = json.load(jf)
            if 'exhibits' in data.keys():
                self._process_array(data['exhibits'], not_found)
                print(Fore.LIGHTBLUE_EX + f'Writing new json file {output_file}' + Style.RESET_ALL)
                with open(output_file, 'w') as jf_out:
                    json.dump(data, jf_out)
        if len(not_found) > 0:

            with open(unkown_iiif, 'w', newline='') as writeFile:
                print(Fore.LIGHTBLUE_EX + f'Writing objects not found to  {unkown_iiif}' + Style.RESET_ALL)
                fieldnames = [ "ID", "URL" ] 
                writer = csv.DictWriter(writeFile, fieldnames=fieldnames)
                writer.writeheader()
                for item in not_found:
                    writer.writerow(item)

       
def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to get or post data to a M+ ria application.

    annotations_update.py [OPTIONS] --json json_file --csv csv_file

        OPTIONS:
        -h|--help                    show help
        -c|--csv                input csv file
        -j|--json                    input json file 
        -o|--output                  output json file
    
        :return: exit code (int)
    """
    csv_file = ''
    json_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv, "hc:j:o:", ["help", "csv=","json=","output="])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-c', '--csv'):
            csv_file = arg
        elif opt in ('-j', '--json'):
            json_file = arg
        elif opt in ('-o', '--output'):
            output_file = arg
    exit_code = 0
    if json_file != '' and csv_file != '':
        output_file = output_file if output_file != '' else json_file.replace('.json','_out.json')
        annotations_update = AnnotationUpdate(csv_file)
        exit_code = annotations_update.process_file(json_file, output_file)
        #return process_file(csv_file)
    else:
        usage()
    return exit_code 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

