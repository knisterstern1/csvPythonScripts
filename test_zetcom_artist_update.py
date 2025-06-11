import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_artist_update
from typing import List


class TestZetcomArtist(unittest.TestCase):
    def test_process_file(self):
        artist_update = zetcom_artist_update.ZetcomArtistUpdate()
        artist_update.close()



if __name__ == "__main__":
    unittest.main()
