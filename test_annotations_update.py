import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import annotations_update 
from typing import List


class TestAnnotationsUpdate(unittest.TestCase):
    TEST_FILE = 'test_files/test_iiif.csv'

    @unittest.skip('Resources')
    def test_init(self):
        annotations = annotations_update.AnnotationUpdate(self.TEST_FILE)
        self.assertEqual(len(annotations.objects), 10)

    def test_process_array(self):
        data = [{ "id": "1677058770774", "type": "popup", "link": { "en": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=en&info=show&copy=hide", "de": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=de&info=show&copy=hide", "fr": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=fr&info=show&copy=hide"}, "openPopupOption": "modal" }]
        annotations = annotations_update.AnnotationUpdate(self.TEST_FILE)
        annotations._process_array(data, [])
        print(data)
  
    @unittest.skip('Resources')
    def test_get_new_link(self):
        annotations = annotations_update.AnnotationUpdate(self.TEST_FILE, True)
        self.assertEqual(annotations._get_object_id('https://iiif.kumu.swiss/gw11_0001540_19911118_s01'), '0001540')

if __name__ == "__main__":
    unittest.main()
