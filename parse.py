import lxml.etree as ET
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
    
    return javascripts

def is_local_script(script):
    if 'src' in script.keys():
        src = script.get('src')
        return src.startswith(settings.MEDIA_URL)
    else:
        return True

def filter_local_scripts(scripts):
    return filter(is_local_script, scripts)

def find_local_scripts(data):
    return filter_local_scripts(find_scripts(data))

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
                with open(path, 'r') as f:
                    files.append(rel_path)
                    parts.append((rel_path, f.read()))
            except IOError as e:
                raise IOError("Could not process script '%s': %s" % (rel_path,
                                                                     e))

    result = u""""""
    for source, part in parts:
        result += u"""// Imported %s\n""" % (source,)
        result += part.strip() + "\n\n"

    return {'collated': result,
            'files': files,
            'scripts': scripts
           }
