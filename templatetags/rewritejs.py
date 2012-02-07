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

    if len(js_args) == 0:
        nodelist = parser.parse(['endjs'])
        parser.delete_first_token()
        
        return InlineJsNode(nodelist, js_args)
    else:
        return ExternalJsNode(js_args)

class Script(object):
    def __init__(self, name, data, other_scripts, is_file=False,):
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

    def __str__(self):
        if hasattr(settings, 'REWRITE_JS_COLLATE_TAGS_TO_LAST') and settings.REWRITE_JS_COLLATE_TAGS_TO_LAST:
            if self.last:
                # The last tag needs to collate all the previous ones
                res = u""
                for script in self.scripts: # includes self
                    res += u"// included from %s\n" % (script.name, )
                    res += u"%s\n" % (script.data.strip(),)
                # put it in a script tag
                return mark_safe(u"""<script type="text/javascript">%s</script>""" % (res,))

            else:
                return mark_safe(u'')
        else:
            if self.is_file:
                return mark_safe(u"""<script type="text/javascript" src="%s"></script>""" % (self.name,))
            else:
                return mark_safe(u"""<script type="text/javascript">%s</script>""" % (self.data,))

    def __unicode__(self):
        return str(self)
    
    def __repr__(self):
        return str(self)

    def __hash__(self):
        if self.is_file:
            return hash(self.name)
        else:
            return hash(self.data)

def reset_last_flag(scripts):
    def clear_last(x): 
            x.last = False
            return x
    scripts = map(clear_last, scripts)
    scripts[-1].last = True
    return scripts

class ExternalJsNode(template.Node):
    def __init__(self, files):
        self.files = files

    def render(self, context):
        if 'scripts' not in context.render_context:
            context.render_context['scripts'] = []
        scripts = context.render_context['scripts']

        for f in self.files:
            f = f.strip('"\'')

            full_path = os.path.join(settings.MEDIA_ROOT, f)
            with open(full_path, 'r') as opened:
                scripts.append(Script(f,
                                      opened, 
                                      context.render_context['scripts'],
                                      is_file=True))

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
        scripts.append(Script('local script', js_content, context.render_context['scripts']))

        context.render_context['scripts'] = reset_last_flag(context.render_context['scripts'])
        return context.render_context['scripts'][-1]
