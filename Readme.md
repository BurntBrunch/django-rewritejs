# django-rewritejs

## Overview

`django-rewritejs` provides simple utilities to make handling multiple
JavaScript files in Django templates a breeze. It is by no means meant to
replace proper minification and unification in high-throughput scenarios but
should be Good Enough™ for everyone else. 

It has two separate (but not mutually exclusive) modes of operation -
middleware- and template tags-based. 

**THIS IS HIGHLY EXPERIMENTAL SOFTWARE. CALLING IT AN ALPHA WOULD BE AN INSULT
TO SOFTWARE IN ACTUAL ALPHA STATE. IF IT BITES OFF YOUR HEAD, 1) CALL AN
AMBULANCE AND 2) DON'T BLAME ME**

## The middleware

By adding `rewritejs.middleware.RewriteJavascriptInlineMiddleware` to
`MIDDLEWARE_CLASSES` (add near the end, since it operates on responses), 
you'll enable a the inliner middleware. It can be disabled by setting
`REWRITE_JS_MIDDLEWARE_INLINE` to False in your settings.

It works as follows:

1. If the response has Content-Type text/html, parse it to a DOM tree
2. Find all `<script>` tags that refer to JavaScript
3. Retain just the local ones (nested at `MEDIA_URL`, or inlined in the HTML)
4. Extract the actual script content (from files or between tags)
5. Remove all but the last script tag
6. Replace the remaining script tag with the content of all the scripts on that
page, in the order in which they appear

This has the effect that if you have scripts on your page and at least one of
them is near the end of the document, they will all be moved there. The
downside is that the external files get inlined (clustering without inlining is 
something that will be configurable in the future)

*Result* :  Your page and JavaScript get served with one request, optimized for
render speed (given that you have a script tag near the end of the document)

*Major downside*: This middleware works after the page has been rendered,
and thus no caching. Therefore, you have extra disk I/O in your render pipeline

## The template tags

### Basic mode

Since the middleware is so crude and unsatisfactory, we now move to
finer-grained method that operates *before* the response is assembled.

There are 2 new tags:

1. {% js %} *your JavaScript code* {% endjs %}
2. {% js 'file.js' 'file2.js' %}
3. {% js 'http://remote\_server/script.js' %}

They can be loaded by adding `{% load rewritejs %}`.

The first marks the code inside as inline JavaScript and by default just wraps
it in `<script>` tags.

The second adds a `<script>` tag referencing `MEDIA_URL/<file>.js` for each
argument passed to it.

The third adds a `<script>` tag referencing the remote URL.

### Clustering mode

As with the middleware, you can set `REWRITE_JS_COLLATE_TAGS_TO_LAST` to True
to enable page rewriting where all the JavaScript content, including the referenced files,
gets moved to the last `<script>` tag. Again, not inlining local files will be
an option in the future.

### Redirect mode

The culmination of all this effort is redirect mode (requires
`REWRITE_JS_COLLATE_TAGS_TO_LAST` and `REWRITE_JS_REDIRECT_TAGS_TO_CACHE`).
This mode does the same as the clustering one, except instead of inlining the
scripts in the HTML, it caches them in the Django cache framework and replaces
the last `<script>` with one that references a local url *unique for this set
of scripts*. This way, all the scripts on the page can be automatically
compiled into one script, cached, and served from the cached from then on. This
mode assumes that no external script is modifying the files in
`MEDIA_ROOT`. Modification from Django templates is allowed.

## Examples

The whitespacing in these examples is not the actual whitespacing produced by
the templates

### Basic mode

    {% load rewritejs %}
    {% js 'http://remote/js' %}
    {% js %} script1(); {% endjs %}
    {% js 'file1.js' %}
    SOME AWESOME HTML
    {% js %} script2(); {% endjs %}
    {% js 'file2.js %}

The above would be processed to:
    
    <script type="text/javascript" src="http://remote/js"></script>
    <script type="text/javascript">script1();</script>
    <script type="text/javascript" src="MEDIA_URL/file1.js"></script>
    SOME AWESOME HTML
    <script type="text/javascript">script2();</script>
    <script type="text/javascript" src="MEDIA_URL/file2.js"></script>

    
### Clustering/middleware mode

    {% load rewritejs %}
    {% js 'http://remote/js' %}
    {% js 'file1.js' %}
    SOME AWESOME HTML
    {% js %} script2(); {% endjs %}
    {% js 'file2.js %}

The above would be processed to:

    <script type="text/javascript" src="http://remote/js"></script>
    
    SOME AWESOME HTML

    <script type="text/javascript">
    script1();
    [contents of MEDIA_ROOT/file1.js]
    script2();
    [contents of MEDIA_ROOT/file2.js]
    </script>

### Redirect mode

    {% load rewritejs %}
    {% js 'http://remote/js' %}
    {% js 'file1.js' %}
    SOME AWESOME HTML
    {% js %} script2(); {% endjs %}
    {% js 'file2.js %}

The above would be processed to:

    SOME AWESOME HTML
    <script type="text/javascript" src="/js/<hash>"></script>

where `/js/<hash>` would serve
    
    script1();
    [contents of MEDIA_ROOT/file1.js]
    script2();
    [contents of MEDIA_ROOT/file2.js]

## Installation

1. Copy to your project
2. Add to `INSTALLED_APPS`
3. To use the tags, make sure `django.template.loaders.app_directories.Loader`
   is in `TEMPLATE_LOADERS`
4. To use redirect mode, `include()` the urls.py
5. To use the middleware, add `rewritejs.middleware.RewriteJavascriptInlineMiddleware` to your `MIDDLEWARE_CLASSES`
