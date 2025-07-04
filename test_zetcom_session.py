import unittest
from os import sep, path
import lxml.etree as ET
import sys
import zetcom_session

class TestZetcomTest(unittest.TestCase):
    def test_check_init(self):
        zsession = zetcom_session.ZetcomSession()
        self.assertEqual(zsession.server,'https://mptest.kumu.swiss')
        self.assertEqual(zsession.username,'SimpleUserTest')
        zsession.close()

    def test_get_json(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        response = zsession.get_json('/ria-ws/application/module/Object/0054240/export/95025')
        self.assertTrue(len(response) > 0)
        self.assertEqual(response[0]["ID"], '54240')
        zsession.close()

    def test_check_get(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        xml = zsession.get("/ria-ws/application/vocabulary/instances/AdrPersonTypeVgr/nodes/search")
        self.assertEqual(xml.nsmap[None], "http://www.zetcom.com/ria/ws/vocabulary")
        zsession.close()

    def test_check_open(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        self.assertTrue(zsession.session.auth[1].startswith('session'))
        zsession.close()

    def test_check_post(self):
        zsession = zetcom_session.ZetcomSession()
        zsession.open()
        xml_string = '<?xml version="1.0" encoding="UTF-8"?><application xmlns="http://www.zetcom.com/ria/ws/module/search" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://www.zetcom.com/ria/ws/module/search/search_1_1.xsd"><modules><module name="Address"><search limit="10" offset="0"><select><field fieldPath="__id"/></select><expert><equalsField fieldPath="__id" operand="11099"/></expert></search></module></modules></application>'
        xml = zsession.post('/ria-ws/application/module/Address/search', xml_string)
        namespaces = { 'module': xml.nsmap[None] }
        self.assertEqual(len(xml.xpath('//module:module', namespaces=namespaces)), 1)
        self.assertEqual(xml.xpath('//module:module/@totalSize', namespaces=namespaces)[0], '1')
        zsession.close()


if __name__ == "__main__":
    unittest.main()
