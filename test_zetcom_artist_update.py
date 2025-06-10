import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_artist_update
import zetcom_session
from zetcom_artist_update import Artist
from zetcom_address_update import address_parse_title, parse_address_parts, print_address_fields
from typing import List


class TestZetcomArtist(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
