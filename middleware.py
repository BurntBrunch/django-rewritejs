from parse import rewrite_page

class RewriteJavascriptMiddleware(object):
    def __init__(self):
        pass
    
    def process_response(self, request, response):
        if response.has_header('content-type'):
            if "text/html" in response['Content-Type']:
                rewritten = rewrite_page(response.content)
                response.content = rewritten['rewritten']

        return response
