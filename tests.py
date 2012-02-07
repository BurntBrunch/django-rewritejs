import parse

from django.conf import settings
from django.template import Template, Context
from django.test import TestCase

class ParserTests(TestCase):
    def test_find_scripts(self):
        import urllib2

        data = urllib2.urlopen("http://localhost:8000", timeout=10).read()

        scripts = parse.find_scripts(data)['scripts']

        self.assertGreater(len(scripts), 0)
        
        data = """
<html>
<head>
    <script>
        $.magic();
    </script>
    <script type="text/javascript">
        $.magic();
    </script>
    <script language="JavaScript">
        $.magic();
    </script>
</head>
</html>
        """
        scripts = parse.find_scripts(data)['scripts']
        self.assertEquals(len(scripts), 3)

        data = """
<html>
<head>
    <script type="text/coffeescript">
        $.magic();
    </script>
</head>
</html>
        """
        scripts = parse.find_scripts(data)['scripts']

        self.assertEquals(len(scripts), 0)

    def test_local_scripts(self):
        
        data = """
<html>
<head>
    <script>
        $.magic();
    </script>
    <script type="text/javascript">
        $.magic();
    </script>
    <script language="JavaScript">
        $.magic();
    </script>
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
    <script src="%sjquery.min.js"></script>
</head>
</html>
        """ % settings.MEDIA_URL
        scripts = parse.find_local_scripts(data)['localscripts']
        self.assertEquals(len(scripts), 4)

    def test_collate_scripts(self):

        data = """
<html>
<head>
    <script>
        part1();
    </script>
    <script type="text/javascript">
        part2();
    </script>
    <script language="JavaScript">
        part3();
    </script>
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js">
        must_not_be_included();
    </script>
    <script src="%sjs/custom.js">
        must_not_be_included();
    </script>
</head>
</html> """ % settings.MEDIA_URL
        
        scripts = parse.find_local_scripts(data)['localscripts']
        result = parse.collate_scripts(scripts)
        self.assertTrue('js/custom.js' in result['files'])
        self.assertTrue('must_not_be_included' not in result['collated'])
        self.assertTrue('part1' in result['collated'])
        self.assertTrue('part2' in result['collated'])
        self.assertTrue('part3' in result['collated'])
        self.assertEqual(set(scripts), set(result['scripts']))
        

        data = """
<html>
<head>
    <script src="%sjs/non-existent-script.js">
        part1();
    </script>
</head>
</html> """ % settings.MEDIA_URL
        self.assertRaises(IOError, 
                          lambda: parse.collate_scripts(parse.find_local_scripts(data)['localscripts']))

    def test_rewrite_page(self):
        data = """
<html>
<head>
    <script>
        part1();
    </script>
    <script type="text/javascript">
        part2();\r
    </script>
    <script language="JavaScript">
        part3();\r
        part4();
    </script>
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js">
        must_not_be_included();
    </script>
    <script src="%sjs/custom.js">
        must_not_be_included();
    </script>
</head>
</html> """ % settings.MEDIA_URL
       
        result = parse.rewrite_page(data)
        scripts = result['rootnode'].xpath('//script')
        self.assertEquals(len(scripts), 2)
        self.assertFalse('src' in scripts[-1].keys())
        self.assertFalse("\r" in scripts[-1].text)

class TagsTests(TestCase):
    def test_tags_substitution(self):
        html = """
{% load rewritejs %}

Local script below:
{% js %} $.magic(); {% endjs %}
End local script

External script below:
{% js 'js/custom.js' 'js/custom.js' %}
End external script

Last script below:
{% js %} $.end(); {% endjs %}
End last script
"""

        settings.REWRITE_JS_COLLATE_TAGS_TO_LAST = True

        template = Template(html)
        rendered = template.render(Context())
        self.assertTrue(len(rendered.split("<script")) == 2) # there's only one <script occurrence

        settings.REWRITE_JS_COLLATE_TAGS_TO_LAST = False

        template = Template(html)
        rendered = template.render(Context())
        self.assertTrue(len(rendered.split("<script")) == 5) # there are 4 <script occurrences
        
