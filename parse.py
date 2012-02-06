import lxml.etree as ET
from StringIO import StringIO

def find_scripts(data):
    parser = None
    if not hasattr(data, 'read'):
        parser = ET.parse(StringIO(data))
    else:
        parser = ET.parse(data)

    root = parser.getroot()
    print dir(root)

    return

