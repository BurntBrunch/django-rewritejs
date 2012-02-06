import parse

from django.test import TestCase

class ParserTests(TestCase):
    def test_find_scripts(self):
        import urllib2

        data = urllib2.urlopen("http://localhost:8000", timeout=10)

        scripts = parse.find_scripts(data)

        self.assertGreater(len(scripts), 0)
