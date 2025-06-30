import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session
from zetcom_session import SchemaItem
from artist_api import Artist
from typing import List


class TestArtistApi(unittest.TestCase):

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
        artist.update()
        self.assertEqual(artist.livedBefore, '1908')
        self.assertEqual(artist.livedAfter, '1939')
        artist.addDate('early 20th century')
        artist.update()
        self.assertEqual(artist.livedAfter, '1939')
        zsession.close()

    def test_artist_epoche(self):
        artist = Artist('Test Test', None, False)
        artist.birth = '01.12.1888'
        artist.death = '12/12/1938'
        artist._set_epoche()
        self.assertEqual(artist.epoche, '20. Jh.')
        self.assertEqual(artist.life_data, '1888–1938')

if __name__ == "__main__":
    unittest.main()
