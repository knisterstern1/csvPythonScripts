import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session
from zetcom_session import SchemaItem
from getty_artist import Artist, Getty
from wikidata_artist import Wikidata 
from typing import List


class TestWikidata(unittest.TestCase):

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
        artist = Artist('Adhemar Gonzaga', None, False)
        artist.addDate('1923-1939')
        wikidata.query_artist(artist)

if __name__ == "__main__":
    unittest.main()
