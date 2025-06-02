import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_address_update
from zetcom_address_update import AddressItem
from zetcom_address_update import SchemaItem 
from zetcom_address_update import address_parse_title, parse_address_parts, print_address_fields
from typing import List


class TestZetcomAddress(unittest.TestCase):
    def test_create_addr_type_dict(self):
        address = zetcom_address_update.ZetcomAddressUpdates([])
        address._init_addr_type_dict()
        self.assertEqual(len(address.addr_type_dict.keys()), 3)
        address.close()

    @unittest.skip('Resources')
    def test_parse_address(self):
        institution = 'Amgueddfa Cymru National Museum Wales'
        addressList: List[AddressItem] = []
        with open('TFH.csv', newline='') as openFile: 
            reader = csv.DictReader(openFile)
            for row in reader:
                if row['Institution'] == institution:
                    parse_address_parts(row['Address'], addressList)
        self.assertEqual(len(addressList), 3)
        institution = 'Deutsches Historisches Museum'
        addressList: List[AddressItem] = []
        with open('TFH.csv', newline='') as openFile: 
            reader = csv.DictReader(openFile)
            for row in reader:
                if row['Institution'] == institution:
                    parse_address_parts(row['Address'], addressList)
        self.assertEqual(len(addressList), 3)
        print_address_fields(0, addressList)

    @unittest.skip('Resources')
    def test_address_id(self):
        address = zetcom_address_update.ZetcomAddressUpdates([])
        items: List[AddressItem] = [ AddressItem('AdrOrganisationTxt','Kunstmuseum Basel'), AddressItem('AdrSurNameTxt', 'Selz'), AddressItem('AdrForeNameTxt', 'Christian') ] 
        address_id = address.address_id(items)
        self.assertEqual(address_id, '19964')
        items: List[AddressItem] = [ AddressItem('AdrOrganisationTxt','Kunstmuseum Basel') ] 
        address_id = address.address_id(items)
        self.assertEqual(address_id, '11099')
        items: List[AddressItem] = [ AddressItem('AdrOrganisationTxt','Kunstmuseum Basel') ] 
        address.close()

    @unittest.skip('Resources')
    def test_process_file(self):
        address = zetcom_address_update.ZetcomAddressUpdates([])
        address.process_file('TFH.csv', 'test.csv')
        address.close()

    @unittest.skip('Resources')
    def test_parse(self):
        addressList: List[AddressItem] = []
        address_parse_title('Dr. Christian', addressList)
        self.assertEqual(len(addressList), 2)
        self.assertEqual(addressList[0].fieldPath, 'AdrAcademicTitleVoc')
        self.assertEqual(addressList[0].operand, 'Dr.')
        self.assertEqual(addressList[1].operand, 'Christian')

    @unittest.skip('Resources')
    def test_append_address_item(self):
        testRow = {'Institution': 'The Metropolitan Museum of Art', 'First_Name': 'Irene Miller', 'Last_Name': 'and Kim Harding', 'Title': 'Associate Curator', 'Address': '1000 Fifth Avenue \nNew York, NY 10028', 'Country': 'USA', 'Email': 'Ashley.Dunn@metmuseum.org'}
        address = zetcom_address_update.ZetcomAddressUpdates([])
        addressList: List[AddressItem] = []
        for schema in address.schemas:
            address.append_address_item(testRow, schema, addressList)
        self.assertEqual(len(addressList), 6)
        address.close()

if __name__ == "__main__":
    unittest.main()
