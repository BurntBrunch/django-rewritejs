from parse import rewrite_page

from django.conf import settings

class RewriteJavascriptInlineMiddleware(object):
    def __init__(self):
        pass
    
    def process_response(self, request, response):
        if settings.REWRITE_JS_MIDDLEWARE_INLINE and response.has_header('content-type'):
            if "text/html" in response['Content-Type']:
                rewritten = rewrite_page(response.content)
                response.content = rewritten['rewritten']

        return response
