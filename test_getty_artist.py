import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session
from zetcom_session import SchemaItem
from artist_api import Artist
from getty_artist import Getty
from typing import List


class TestGetty(unittest.TestCase):

    def test_process_qetty(self):
        artist = Artist('Elisàr von Kupffer', None, False)
        artist.addDate('1923-1939')
        getty = Getty()
        getty.query_artist(artist)
        self.assertEqual(artist.surename, 'Kupffer')
        self.assertEqual(artist.death, '1942')
        row = artist.asrow([ SchemaItem('forename', 'forename'), SchemaItem('surename','surename')])
        self.assertEqual(row['forename'], 'Elisar von')

if __name__ == "__main__":
    unittest.main()
