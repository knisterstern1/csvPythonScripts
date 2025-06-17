import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session
from zetcom_session import SchemaItem
from getty_artist import Getty
from artist_api import Artist
from wikidata_artist import Wikidata 
from typing import List


class TestWikidata(unittest.TestCase):

    @unittest.skip('Resources')
    def test_process_qetty(self):
        artist = Artist('Elisàr von Kupffer', None, False)
        artist.addDate('1923-1939')
        getty = Getty()
        getty.query_artist(artist)
        wikidata = Wikidata()
        wikidata.query_artist(artist)
        self.assertEqual(artist.surename, 'Kupffer')
        self.assertEqual(artist.death, '31.10.1942')
        row = artist.asrow([ SchemaItem('forename', 'forename'), SchemaItem('surename','surename')])
        self.assertEqual(row['forename'], 'Elisar von')

    @unittest.skip('Resources')
    def test_process_response(self):
        artist = Artist('Adhemar Gonzaga', None, False)
        response = {'head': {'vars': ['item', 'itemLabel', 'birth', 'VornameLabel', 'FamiliennameLabel', 'death', 'genderLabel', 'placeOfBirthLabel', 'placeOfDeathLabel']}, 'results': {'bindings': [{'item': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q9582671'}, 'birth': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime', 'type': 'literal', 'value': '1901-08-26T00:00:00Z'}, 'death': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime', 'type': 'literal', 'value': '1978-01-29T00:00:00Z'}, 'itemLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Adhemar Gonzaga'}, 'VornameLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Ademar'}, 'genderLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'male'}, 'placeOfBirthLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Rio de Janeiro'}, 'placeOfDeathLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Rio de Janeiro'}}]}}
        wikidata = Wikidata()
        wikidata._process_response(response, artist)
        wikidata.query_artist(artist)
        self.assertEqual(artist.surename, 'Gonzaga')

    def test_family_name(self):
        artist = Artist('Stanisław Ignacy Witkiewicz', None, False)
        getty = Getty()
        getty.query_artist(artist)
        artist.addDate('1912-1913')
        artist.addDate('1917')
        wikidata = Wikidata()
        wikidata.query_artist(artist)
        self.assertEqual(artist.forename, 'Stanisław Ignacy')

if __name__ == "__main__":
    unittest.main()
