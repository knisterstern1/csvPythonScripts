#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program can be used to check whether the filename of files accords with the mediastandard.
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
import json
import os
from pathlib import Path, PosixPath
import re
import requests
import sys
import urllib
from typing import List

DEBUG = False 

class Result:
    """This class represents the result of the Mediastandard check
    """
    def __init__(self, check_passed=True, error_msg="", groups=None): 
        self.check_passed = check_passed
        self.error_msg = error_msg
        self.groups = groups

    def addMessage(self, message: str, m: re.Match):
        """Adds a error message
        """
        if len(m.groupdict()):
            self.groups = m.groupdict()
        if ":" in self.error_msg:
            self.error_msg = self.error_msg + " " + message
        else:
            self.error_msg = self.error_msg + ": " + message

    def getFilenameInfo(self, file_path: PosixPath, color: str) ->str:
        """Get graphical information about filename
        """
        if file_path.exists():
            if not self.check_passed and self.groups:
                return color + f'{file_path.parent.absolute()}{os.sep}{self.groups["before"]}' + Fore.RED + f'{self.groups["error"]}' + Style.RESET_ALL + color + f'{self.groups["after"]}' + Style.RESET_ALL
            return file_path.absolute()
        else:
            if not self.check_passed and self.groups:
                return color + f'{self.groups["before"]}' + Fore.RED + f'{self.groups["error"]}' + Style.RESET_ALL + color + f'{self.groups["after"]}' + Style.RESET_ALL
            return file_path.name

class Rule:
    """This class represents a rule of the mediastandard
    """
    def __init__(self, rule: dict): 
        self.pattern = re.compile(urllib.parse.unquote(rule['regex']))
        self.error = rule['error']
        self.onErrorRules = []
        if 'onError' in rule.keys():
            for errorRule in rule['onError']:
                self.onErrorRules.append(Rule(errorRule))

    def applies(self, filename: str) ->Result:
        """Check if rule applies, return Result
        """
        if self.pattern.match(filename):
            return Result()
        errorResult = Result(False, self.error)
        for onErrorRule in self.onErrorRules:
            m = onErrorRule.findError(filename)
            if m:
                errorResult.addMessage(onErrorRule.error, m)
        return errorResult

    def findError(self, filename: str) ->re.Match:
        """Return true if pattern matches
        """
        return self.pattern.match(filename)

class MediaStandard:
    """This class represents a certain version of the mediastandard
    """

    def __init__(self): 
        self.version = "3.0"
        self.rules = []

    def check_filename(self, path: PosixPath) ->Result: 
        """Check if filename conforms to rules
        """
        result = None
        for rule in self.rules:
            result = rule.applies(path.name) 
            if not result.check_passed:
                return result
        m = self.pattern.match(path.name)
        if m is not None:
            result = Result(True, '',m.groupdict())
        return result

    def check_content(self, result: Result) ->Result: 
        """Check if filename conforms to rules
        """
        for key in result.groups.keys():
            if key in self.content.keys():
                label = self.vocabulary[key] if key in self.vocabulary.keys() else key
                print(f'{label}: {self.content[key][result.groups[key]]}')
        return result


    def load(self, json_file, verbose=False):
        """Load a specific standard
        """
        with open(json_file) as json_ref:
            data = json.load(json_ref)
            self.version = data['info']['version']
            self.year = data['info']['year']
            self.pattern = re.compile(urllib.parse.unquote(data['pattern']))
            self.content = data['content']
            self.vocabulary = data['vocabulary']
            for rule in data['rules']:
                self.rules.append(Rule(rule))
        print(Fore.MAGENTA + f"Medienstandard Version {self.version}, {self.year} geladen ..." + Style.RESET_ALL)
        if verbose:
            print(Fore.MAGENTA + data['comment'] + Style.RESET_ALL)

def usage():
    """prints information on how to use the script
    """
    print(main.__doc__)

def main(argv):
    """This program can be used to check whether filenames accord with a media standard.

    mediastandard_validation.py [OPTIONS] file1 file2 ... | directory

        OPTIONS:
        -h|--help       show help
        -j|--json=file  json file
        -v|--verbose    print infomation about json
    
        :return: exit code (int)
    """
    json="medienstandard_v3_regex.json"
    verbose = False
    try:
        opts, args = getopt.getopt(argv, "hj:v", ["help","json=", "verbose"])
    except getopt.GetoptError:
        usage()
        return 2
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            return 0
        elif opt in ('-v', '--verbose'):
            verbose = True 
        elif opt in ('-j', '--json'):
            json = arg
    checker = MediaStandard()
    checker.load(json, verbose)
    filenames = get_filenames([ Path(arg) for arg in args ])
    
    print(Fore.MAGENTA + f'Checking {len(filenames)} filename{"s" if len(filenames) > 1 else ""}.' + Style.RESET_ALL)
    if len(filenames) < 1:
        print('Nothing to do ...')
        usage()
    for file_path in filenames: 
        result = checker.check_filename(file_path)
        if not result.check_passed:
            filename = result.getFilenameInfo(file_path, Fore.LIGHTBLUE_EX)
            if verbose:
                print(f'{filename}\t[' + Fore.RED + 'FAIL' + Style.RESET_ALL + f']: {result.error_msg}')
            else:
                print(f'{filename}\t[' + Fore.RED + 'FAIL' + Style.RESET_ALL + f']')
        else:
            filename = Fore.LIGHTBLUE_EX + file_path.absolute() + Style.RESET_ALL if file_path.exists() else Fore.LIGHTBLUE_EX + file_path.name + Style.RESET_ALL
            if verbose:
                print(f'Informationen zu {filename}: ')
                checker.check_content(result)
            else:
                print(f'{filename}\t[OK]')
    return 0 

def get_filenames(paths: List[PosixPath]) -> List[PosixPath]:
    """Get a list of filenames from input arguments
    """
    filenames = []
    for file_path in paths:
        if file_path.is_dir():
            for filename in get_filenames(list(file_path.glob('*'))):
                filenames.append(filename)
        else:
            filenames.append(file_path)
    return filenames

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

