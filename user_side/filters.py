from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, CharFilter, BooleanFilter
from .models import Anime, Episode

class AnimeFilter(FilterSet):
    release_year_gte = NumberFilter(field_name='release_year', lookup_expr='gte')
    release_year_lte = NumberFilter(field_name='release_year', lookup_expr='lte')
    season = CharFilter(field_name='season', lookup_expr='iexact')
    type = CharFilter(field_name='type', lookup_expr='iexact')
    is_premium_only = BooleanFilter(field_name='is_premium_only')
    genre = CharFilter(method='filter_by_genres', label='Genres (comma-separated IDs)')

    class Meta:
        model = Anime
        fields = []

    def filter_by_genres(self, queryset, name, value):
        genre_ids = [int(g) for g in value.split(',') if g.isdigit()]
        if genre_ids:
            queryset = queryset.filter(genres__id__in=genre_ids).distinct()  
        return queryset
    

class EpisodeFilter(FilterSet):
    is_premium_only = BooleanFilter(field_name='is_premium_only')
    episode_number = NumberFilter(field_name='episode_number')
    
    class Meta:
        model = Episode
        fields = []