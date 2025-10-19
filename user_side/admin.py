from django.contrib import admin
from .models import (
    User,
    AnonymousSession,
    Anime,
    Episode,
    EpisodeLanguage,
    Genre,
    WatchHistory,
    Like,
    Comment,
    AnimeView,
    Subscription,
    Payment,
    Advertisement,
    AdImpression,
)

admin.site.register(User)
admin.site.register(AnonymousSession)
admin.site.register(Anime)
admin.site.register(Episode)
admin.site.register(EpisodeLanguage)
admin.site.register(Genre)
admin.site.register(WatchHistory)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(AnimeView)
admin.site.register(Subscription)
admin.site.register(Payment)
admin.site.register(Advertisement)
admin.site.register(AdImpression)
