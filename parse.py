# coding: utf-8

import lxml.etree as ET
import lxml.html
import os.path

from django.conf import settings

def find_scripts(data):
    if hasattr(data, 'read'):
        data = data.read()
    
    root = ET.HTML(data)

    scripts = root.xpath("//script")
    javascripts = []

    for script in scripts:
        keys = script.keys()
        if ( ('type' in keys and script.get('type').lower() == "text/javascript") or 
             ('language' in keys and script.get('language').lower() == 'javascript') or
             ('src' in keys and script.get('src').lower().endswith('js')) or
             ('type' not in keys and 'language' not in keys) ):
            # the last condition assumes javascript is the default browser
            # language (which it should be!)
            javascripts.append(script)
    
    return {'rootnode': root, 'scripts': javascripts}

def is_local_script(script):
    if 'src' in script.keys():
        src = script.get('src')
        return src.startswith(settings.MEDIA_URL)
    else:
        return True

def filter_local_scripts(scripts):
    return filter(is_local_script, scripts)

def find_local_scripts(data):
    parsed = find_scripts(data)
    parsed['localscripts'] = filter_local_scripts(parsed['scripts'])
    return parsed

def collate_scripts(scripts):
    parts = []
    local_script_string = 'page-local script'
    files = []

    for script in scripts:
        text = script.text

        if 'src' not in script.keys():
            parts.append((local_script_string, text))
        else:
            url = script.get('src')
            rel_path = url.replace(settings.MEDIA_URL, "") # remove the web prefix
            path = os.path.join(settings.MEDIA_ROOT, rel_path) # convert to local path
            
            try:
                # read the actual .js file
                with open(path, 'rt') as f:
                    files.append(rel_path)
                    parts.append((rel_path, f.read()))

            except IOError as e:
                raise IOError("Could not process script '%s': %s" % (rel_path,
                                                                     e))

    result = u""""""
    for source, part in parts:
        result += u"""// Imported %s\n""" % (source,)

        part = part.decode('utf-8').strip().replace(u"\r", u"")
        # carriage returns mess up the output, since lxml encodes
        # them as HTML entity &#13;

        result += part + u"\n\n"

    return {'collated': result,
            'files': files,
            'scripts': scripts
           }

def rewrite_page(data, pretty_print=False):
    parsed = find_local_scripts(data)
    collation = collate_scripts(parsed['localscripts'])
    parsed['collation'] = collation
    collated_scripts = collation['scripts'] # the scripts that were unified

    """
    A major assumption here is that the XPath evaluator returns the scripts
    in document order. This assumption is tested in the code below and turns
    out to be true. If not, uncomment the code below and use
    collated_scripts_doc_order to determine which the last script in the
    document is

    unknown_doc_order = list(collated_scripts)
    collated_scripts_doc_order = [] # the unified scripts in document order
    for script in parsed['rootnode'].iter():
        if script in unknown_doc_order:
            idx = unknown_doc_order.index(script)
            collated_scripts_doc_order.append(script)
            del unknown_doc_order[idx]
    
    assert all(map(lambda (x,y): x is y, zip(collated_scripts,
                                            collated_scripts_doc_order)))
    """
    
    # remove all but the last script
    for script in collated_scripts[:-1]:
        script.getparent().remove(script)

    # do the last script, if any
    if len(collated_scripts) > 0:
        script = collated_scripts[-1]
        
        new_script = """<script type="text/javascript">\n%s\n</script>""" % (collation['collated'],)
        new_script = lxml.html.fragments_fromstring(new_script)[0] # select the script tag

        script.getparent().replace(script, new_script)

    parsed['rewritten'] = ET.tostring(parsed['rootnode'],
                                      pretty_print=pretty_print,
                                      encoding=unicode,
                                      method='html')
    return parsed
