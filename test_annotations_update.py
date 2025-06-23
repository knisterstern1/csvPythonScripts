import unittest
import csv
from os import sep, path
import lxml.etree as ET
import sys
import annotations_update 
from typing import List


class TestAnnotationsUpdate(unittest.TestCase):
    @unittest.skip('Resources')
    def test_process_file(self):
        annotations = annotations_update.AnnotationUpdate()
        annotations.close()

    @unittest.skip('Resources')
    def test_process_array(self):
        data = [{ "id": "1677058770774", "type": "popup", "link": { "en": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=en&info=show&copy=hide", "de": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=de&info=show&copy=hide", "fr": "https://iiif.kumu.swiss/gw11_0001540_19911118_s01?lang=fr&info=show&copy=hide"}, "openPopupOption": "modal" }]
        annotations = annotations_update.AnnotationUpdate()
        annotations._process_array(data)
        annotations.close()

    def test_get_new_link(self):
        annotations = annotations_update.AnnotationUpdate()
        annotations._get_new_link('https://iiif.kumu.swiss/gw11_0001540_19911118_s01')
        annotations.close()

if __name__ == "__main__":
    unittest.main()
