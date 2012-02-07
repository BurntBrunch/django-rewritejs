from django.conf import settings

defaults = {'REWRITE_JS_REDIRECT_TAGS_TO_CACHE': False,
            'REWRITE_JS_MIDDLEWARE_INLINE': True,
            'REWRITE_JS_COLLATE_TAGS_TO_LAST': True,
            'REWRITE_JS_CACHE_PREFIX': "rewritejs/scripts/"}

for key, val in defaults.items():
    if not hasattr(settings, key):
        setattr(settings, key, val)


