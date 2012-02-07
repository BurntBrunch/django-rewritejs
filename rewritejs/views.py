from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse

def cached_js(request, key):
    cache_prefix = settings.REWRITE_JS_CACHE_PREFIX
    order = cache.get(cache_prefix + "orders/" + key,'')

    script_hashes = order.split(" ")
    res = u""
    for script_hash in script_hashes:
        res += cache.get(cache_prefix + "script/" + script_hash)
        res += "\n"

    return HttpResponse(res, content_type="text/javascript")
