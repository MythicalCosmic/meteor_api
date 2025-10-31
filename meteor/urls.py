from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from user_side.sitemaps import StaticViewSitemap, AnimeSitemap, EpisodeSitemap, GenreSitemap


sitemaps = {
    'static': StaticViewSitemap,
    'animes': AnimeSitemap,
    'episodes': EpisodeSitemap,
    'genres': GenreSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('user_side.urls')), 
    path('', include('docs.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
