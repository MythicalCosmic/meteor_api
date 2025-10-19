from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('animes/', AnimeListView.as_view(), name='anime-list'),           
    path('animes/<int:pk>/', AnimeDetailView.as_view(), name='anime-detail'),

    path('animes/<str:anime_identifier>/episodes/', EpisodeListView.as_view(), name='episode-list'),
    path('animes/<str:anime_identifier>/episodes/<str:episode_identifier>/', EpisodeDetailView.as_view(), name='episode-detail'),

    path('genres/', GenreListView.as_view(), name='genre-list'),
    path('genres/<str:identifier>/', GenreDetailView.as_view(), name='genre-detail'),
    path('genres/<str:identifier>/animes/', GenreAnimeListView.as_view(), name='genre-animes'),
]
