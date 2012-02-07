from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('', url('^(?P<key>.+)/$', 
                           'rewritejs.views.cached_js', 
                           name="cached_js"))
