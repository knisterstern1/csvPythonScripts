import unittest
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_address_update
from zetcom_address_update import AddressItem
from zetcom_address_update import SchemaItem 
from zetcom_address_update import address_parse_title
from typing import List


class TestZetcomAddress(unittest.TestCase):
    @unittest.skip('Resources')
    def test_address_id(self):
        address = zetcom_address_update.ZetcomAddressUpdates([])
        items: List[AddressItem] = [ AddressItem('AdrOrganisationTxt','Kunstmuseum Basel'), AddressItem('AdrSurNameTxt', 'Selz'), AddressItem('AdrForeNameTxt', 'Christian') ] 
        address_id = address.address_id(items)
        self.assertEqual(address_id, '19964')
        address.close()

    @unittest.skip('Resources')
    def test_process_file(self):
        schemas: List[SchemaItem] = [ SchemaItem('Institution', 'AdrOrganisationTxt')]
        address = zetcom_address_update.ZetcomAddressUpdates([])
        address.process_file('TFH.csv')
        address.close()

    @unittest.skip('Resources')
    def test_parse(self):
        addressList: List[AddressItem] = []
        address_parse_title('Dr. Christian', addressList)
        self.assertEqual(len(addressList), 2)
        self.assertEqual(addressList[0].fieldPath, 'AdrAcademicTitleVoc')
        self.assertEqual(addressList[0].operand, 'Dr.')
        self.assertEqual(addressList[1].operand, 'Christian')

    def test_append_address_item(self):
        testRow = {'Institution': 'The Metropolitan Museum of Art', 'First_Name': 'Irene Miller', 'Last_Name': 'and Kim Harding', 'Title': 'Associate Curator', 'Address': '1000 Fifth Avenue \nNew York, NY 10028', 'Country': 'USA', 'Email': 'Ashley.Dunn@metmuseum.org'}
        address = zetcom_address_update.ZetcomAddressUpdates([])
        addressList: List[AddressItem] = []
        for schema in address.schemas:
            address.append_address_item(testRow, schema, addressList)
        self.assertEqual(len(addressList), 6)
        address.append_address_type(addressList)
        #self.assertEqual(len([item for item in addressList if item.fieldPath == 'AdrPersonTypeVoc' and item.operand == 'Einzelperson']), 1)
        #zetcom_address_update.print_address_fields(0, addressList)
        searchItems = address.get_search_items(addressList)
        address_id = address.address_id(searchItems)
        zetcom_address_update.print_address_fields(0, searchItems)
        address.close()

if __name__ == "__main__":
    unittest.main()
