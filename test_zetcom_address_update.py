import unittest
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_address_update
from zetcom_address_update import AddressItem as Item
from typing import List


class TestZetcomAddress(unittest.TestCase):
    def test_address_id(self):
        address = zetcom_address_update.ZetcomAddressUpdates()
        items: List[Item] = [ Item('AdrOrganisationTxt','Kunstmuseum Basel'), Item('AdrSurNameTxt', 'Selz'), Item('AdrForeNameTxt', 'Christian') ] 
        address_id = address.address_id(items)
        self.assertEqual(address_id, '19964')
        address.close()


if __name__ == "__main__":
    unittest.main()
