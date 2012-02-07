# coding: utf-8
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
import os.path

register = template.Library()

@register.tag(name="js")
def js_tag(parser, token):
    js_args = token.split_contents()
    js_args = js_args[1:]
    js_args = map(lambda x: x.strip('"\''), js_args)

    if len(js_args) == 0:
        nodelist = parser.parse(['endjs'])
        parser.delete_first_token()
        
        return InlineJsNode(nodelist, js_args)
    else:
        is_remote_path = lambda x: (x.startswith("http://") or
                               x.startswith("https://") or
                               x.startswith("://"))
        is_local_path = lambda x: not is_remote_path(x)

        if all(map(is_remote_path, js_args)):
            return StaticJsNode(js_args)
        elif all(map(is_local_path, js_args)):
            return ExternalJsNode(js_args)
        else:
            raise ValueError("Cannot mix remote and local paths in the same tag!")

class Script(object):
    def __init__(self, name=None, data=None, other_scripts=tuple(), is_file=False,):
        self.is_file = is_file

        if hasattr(data, 'read'):
            self.data = None
            with data as f:
                self.data = f.read()
        else:
            self.data = data

        self.scripts = other_scripts
        self.name = name
        self.last = False

    def get_content(self):
        return self.data

    def _collate_previous_scripts(self):
        if self.last:
            # The last tag needs to collate all the previous ones
            res = u""
            for script in self.scripts: # includes self
                res += u"// included from %s\n" % (script.name, )
                res += u"%s\n" % (script.get_content().strip(),)
            # put it in a script tag
            return mark_safe(u"""<script type="text/javascript">%s</script>""" % (res,))
        else:
            return mark_safe(u'')

    def __str__(self):
        if hasattr(settings, 'REWRITE_JS_COLLATE_TAGS_TO_LAST') and settings.REWRITE_JS_COLLATE_TAGS_TO_LAST:
            return self._collate_previous_scripts()
        else:
            if self.is_file:
                return mark_safe(u"""<script type="text/javascript" src="%s"></script>""" % (self.name,))
            else:
                return mark_safe(u"""<script type="text/javascript">%s</script>""" % (self.get_content(),))

    def __unicode__(self):
        return str(self)
    
    def __repr__(self):
        return "<Script '%s'>" % (self.name,)

    def __hash__(self):
        if self.is_file:
            return hash(self.name)
        else:
            return hash(self.data)

class MultipleExternalScripts(Script):
    def __init__(self, scripts, other_scripts=tuple()):
        self.scripts = scripts
        self.other_scripts = other_scripts
        self.name = " ".join((x.name for x in self.scripts))
        self.last = False

    def get_content(self):
        res = u""
        for script in self.scripts:
            res += script.get_content() + "\n"
        return res
    
    def __repr__(self):
        return "<MultipleScripts '%s'>" % (self.name,)

    def __hash__(self):
        return reduce(lambda x,y: x*hash(y), self.scripts, initial=1)

    def __str__(self):
        if hasattr(settings, 'REWRITE_JS_COLLATE_TAGS_TO_LAST') and settings.REWRITE_JS_COLLATE_TAGS_TO_LAST:
            return self._collate_previous_scripts()
        else:
            res = u""
            for script in self.scripts:
                res += u"""<script type="text/javascript" src="%s"></script>\n""" % (script.name,)

            return mark_safe(res.rstrip())

def reset_last_flag(scripts):
    def clear_last(x): 
            x.last = False
            return x
    scripts = map(clear_last, scripts)
    scripts[-1].last = True
    return scripts

class StaticJsNode(template.Node):
    def __init__(self, paths):
        self.paths = paths

    def render(self, context):
        res = u""
        for path in self.paths:
            res += u"""<script type="text/javascript" src="%s"></script>\n""" % (path,)
        return mark_safe(res)


class ExternalJsNode(template.Node):
    def __init__(self, files):
        self.files = files

    def render(self, context):
        if 'scripts' not in context.render_context:
            context.render_context['scripts'] = []
        scripts = context.render_context['scripts']
        
        referenced_scripts = []
        for f in self.files:
            full_path = os.path.join(settings.MEDIA_ROOT, f)
            
            with open(full_path, 'r') as opened:
                referenced_scripts.append(Script(name=f,
                                      data=opened, 
                                      other_scripts=context.render_context['scripts'],
                                      is_file=True))

        scripts.append(MultipleExternalScripts(referenced_scripts,
                                               other_scripts=scripts))

        context.render_context['scripts'] = reset_last_flag(context.render_context['scripts'])

        return context.render_context['scripts'][-1]

class InlineJsNode(template.Node):
    def __init__(self, nodelist, args):
        self.nodelist = nodelist
        self.args = args

    def render(self, context):
        if 'scripts' not in context.render_context:
            context.render_context['scripts'] = []
        scripts = context.render_context['scripts']

        js_content = self.nodelist.render(context).strip()
        scripts.append(Script(name='local script', 
                              data=js_content, 
                              other_scripts=context.render_context['scripts']))

        context.render_context['scripts'] = reset_last_flag(context.render_context['scripts'])
        return context.render_context['scripts'][-1]
