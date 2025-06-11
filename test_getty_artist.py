import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session
from zetcom_session import SchemaItem
from getty_artist import Artist, Getty
from typing import List


class TestGetty(unittest.TestCase):

    def test_artist_id(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        artist = Artist('Augusta Roszmann', zsession)
        self.assertTrue(artist.id is not None)
        zsession.close()
        
    def test_artist_add_date(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        artist = Artist('Elisàr von Kupffer', zsession)
        artist.addDate('c. 1923-1939')
        artist.addDate('Not dated')
        artist.addDate('1908')
        self.assertEqual(artist.livedBefore(), '1908')
        self.assertEqual(artist.livedAfter(), '1939')
        artist.addDate('early 20th century')
        self.assertEqual(artist.livedAfter(), '1939')
        zsession.close()

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
