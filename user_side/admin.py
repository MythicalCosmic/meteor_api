from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from moviepy.video.io.VideoFileClip import VideoFileClip
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
    Subscription,
    Payment,
    Advertisement,
    AdImpression,
    Favorite,
)

# Custom Admin Classes for Clean Interface

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'is_premium', 'role', 'is_staff', 'created_at')
    list_filter = ('is_premium', 'is_staff', 'role')
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'avatar')}),
        ('Premium Status', {'fields': ('is_premium', 'premium_expires_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login_at', 'created_at')}),
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'role', 'is_premium'),
        }),
    )
    readonly_fields = ('created_at', 'last_login_at')

class AnonymousSessionAdmin(admin.ModelAdmin):
    list_display = ('session_token', 'ip_address', 'country', 'first_seen_at', 'last_seen_at', 'total_visits')
    search_fields = ('session_token', 'ip_address')
    list_filter = ('country',)
    readonly_fields = ('first_seen_at', 'last_seen_at', 'total_visits')
    def has_add_permission(self, request):
        return False  

class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description')}),
    )

class EpisodeLanguageInline(admin.TabularInline):
    model = EpisodeLanguage
    extra = 1
    fields = ('language', 'video_url', 'video_quality', 'file_size_mb', 'is_default')
    readonly_fields = ('file_size_mb',)

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('anime', 'episode_number', 'title', 'slug', 'is_published', 'air_date', 'duration_seconds')
    list_filter = ('is_published', 'is_premium_only', 'anime')
    search_fields = ('title', 'anime__title')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Info', {'fields': ('anime', 'episode_number', 'title', 'slug', 'description')}),
        ('Media', {'fields': ('thumbnail_url',)}),
        ('Details', {'fields': ('duration_seconds', 'air_date', 'is_premium_only', 'is_published')}),
        ('Stats', {'fields': ('total_views', 'total_likes'), 'classes': ('collapse',)}),
    )
    inlines = [EpisodeLanguageInline]
    readonly_fields = ('duration_seconds', 'total_views', 'total_likes')

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1
    fields = ('episode_number', 'title', 'is_published', 'air_date')
    show_change_link = True

class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'release_year', 'rating', 'is_published', 'created_at')
    list_filter = ('status', 'type', 'is_published', 'release_year', 'is_premium_only')
    search_fields = ('title', 'english_title', 'uzbek_title')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Titles', {'fields': ('title', 'english_title', 'uzbek_title', 'slug')}),
        ('Description', {'fields': ('description',)}),
        ('Details', {'fields': ('type', 'status', 'season', 'release_year', 'duration_minutes', 'total_episodes')}),
        ('Media', {'fields': ('poster_url', 'banner_url', 'trailer_url')}),
        ('Genres', {'fields': ('genres',)}),
        ('Publication', {'fields': ('is_published', 'published_at', 'is_premium_only')}),
        ('Stats', {'fields': ('rating', 'total_views', 'total_likes', 'total_favorites', 'total_comments'), 'classes': ('collapse',)}),
    )
    inlines = [EpisodeInline]
    readonly_fields = ('total_views', 'total_likes', 'total_favorites', 'total_comments', 'rating', 'published_at')

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'status', 'starts_at', 'expires_at', 'auto_renew')
    list_filter = ('status', 'auto_renew')
    search_fields = ('user__email', 'plan_type')
    fieldsets = (
        (None, {'fields': ('user', 'plan_type', 'price', 'currency', 'status')}),
        ('Dates', {'fields': ('starts_at', 'expires_at', 'auto_renew')}),
    )

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'amount', 'currency', 'status', 'paid_at')
    list_filter = ('status', 'currency')
    search_fields = ('user__email', 'transaction_id')
    fieldsets = (
        (None, {'fields': ('user', 'subscription', 'payment_gateway', 'transaction_id')}),
        ('Details', {'fields': ('amount', 'currency', 'status', 'payment_method', 'paid_at')}),
    )
    readonly_fields = ('paid_at',)

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'position', 'is_active', 'priority', 'total_impressions', 'total_clicks')
    list_filter = ('type', 'position', 'is_active')
    search_fields = ('title',)
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'type', 'position', 'priority', 'is_active')}),
        ('Content', {'fields': ('content_url', 'html_code', 'duration_seconds', 'click_url')}),
        ('Stats', {'fields': ('total_impressions', 'total_clicks'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('total_impressions', 'total_clicks')


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False  
    def has_delete_permission(self, request, obj=None):
        return False

class WatchHistoryAdmin(ReadOnlyAdmin):
    list_display = ('user', 'anonymous_session', 'anime', 'episode', 'watch_duration_seconds', 'completed', 'watched_at')
    list_filter = ('completed', 'country')
    search_fields = ('user__email', 'anime__title', 'episode__title')

class LikeAdmin(ReadOnlyAdmin):
    list_display = ('user', 'anonymous_session', 'anime', 'episode', 'is_like', 'created_at')
    list_filter = ('is_like',)
    search_fields = ('user__email', 'anime__title', 'episode__title')

class CommentAdmin(ReadOnlyAdmin):
    list_display = ('user', 'anonymous_session', 'anime', 'episode', 'comment', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('comment', 'user__email', 'anime__title', 'episode__title')

class AdImpressionAdmin(ReadOnlyAdmin):
    list_display = ('ad', 'user', 'anonymous_session', 'anime', 'episode', 'clicked', 'viewed_at')
    list_filter = ('clicked',)
    search_fields = ('ad__title', 'user__email', 'anime__title')

class FavoriteAdmin(ReadOnlyAdmin):
    list_display = ('user', 'anonymous_session', 'anime', 'added_at')
    search_fields = ('user__email', 'anime__title')

# Register models with custom admins
admin.site.register(User, CustomUserAdmin)
admin.site.register(AnonymousSession, AnonymousSessionAdmin)
admin.site.register(Anime, AnimeAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(EpisodeLanguage)  # No custom, default is fine for inline use
admin.site.register(Genre, GenreAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)

# Register read-only models
admin.site.register(WatchHistory, WatchHistoryAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(AdImpression, AdImpressionAdmin)
admin.site.register(Favorite, FavoriteAdmin)