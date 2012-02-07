
from timeit import Timer

"""
args = ["import urllib2 ",
"urllib2.urlopen('http://localhost:8000').read()"]

timer1 = Timer(stmt=args[1], setup=args[0])

print "100 requests, 3 times:", timer1.repeat(repeat=3, number=100)
"""

from django.conf import settings
from django.template import Template,Context
def setup():
    import os
    import os.path
    import sys

    parent = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, parent)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'hallsurfing.settings'

html = """
{% load rewritejs %}
{% js %} script 1 {% endjs %}
{% js 'js/custom.js' %} 
{% js %} script 2 - last {% endjs %}
"""
def render():
    template = Template(html)
    template.render(Context())

def inlined():
    settings.REWRITE_JS_COLLATE_TAGS_TO_LAST = True
    render()

def uninlined():
    settings.REWRITE_JS_COLLATE_TAGS_TO_LAST = False
    render()

timer1 = Timer(stmt=inlined, setup=setup)
timer2 = Timer(stmt=uninlined, setup=setup)

print "Inlined: ", timer1.repeat(repeat=3, number=10000)
print "Uninlined: ", timer2.repeat(repeat=3, number=10000)
