#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""   This program can be used to split multiple dates and create a CSV imort file for M+.
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
import getopt
from os import sep, path, listdir
from os.path import isfile, isdir, dirname, basename
from progress.bar import Bar
import re
import sys

__author__ = "Christian Steiner"
__maintainer__ = __author__
__copyright__ = __author__ 
__email__ = "christian.steiner2@bs.ch"
__status__ = "Development"
__license__ = "GPL v3"
__version__ = "0.0.1"

class DateParser:
    """This class can be used to parse date strings containing multiple dates
    """
    OUTPUT_FIELDNAMES = ['ID', 'DatBType', 'DatB']

    def __init__(self, csv_file: str, output_file: str):
        self.csv_file = csv_file
        self.output_file = output_file

    def split_dates(self):
        with open(self.csv_file, newline='') as csvfile: 
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                objId = row['ID']
                dates = row['Datierung']
                print(dates)

def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to split multiple dates and create a CSV imort file for M+.

    split_multiple_dates.py [OPTIONS] <csv-input> <csv-output> 

        <csv-input>   csv export file from M+.
        <csv-output>  csv target file name for import to M+. 

        OPTIONS:
        -h|--help:          show help

        :return: exit code (int)
    """
    try:
        opts, args = getopt.getopt(argv, "h", ["help"])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
    if len(args) < 1 :
        usage()
        return 2
    csv_file = args[0]
    output_file = 'Import_{0}'.format(csv_file) if len(args) < 2 else args[1]
    print(Fore.CYAN + f'Parse dates from  "{csv_file}" and write to "{output_file}"')
    parser = DateParser(csv_file, output_file) 
    parser.split_dates()
    return 0 


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
