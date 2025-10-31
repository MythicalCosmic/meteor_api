from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from .models import Anime, Episode, Genre

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['register', 'login']

    def location(self, item):
        return reverse(item)

class AnimeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Anime.objects.all()

    def location(self, obj):
        return reverse('anime-detail', args=[obj.pk])

class EpisodeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Episode.objects.all()

    def location(self, obj):
        return reverse(
            'episode-detail',
            args=[obj.anime.identifier, obj.identifier]
        )

class GenreSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Genre.objects.all()

    def location(self, obj):
        return reverse('genre-detail', args=[obj.identifier])
