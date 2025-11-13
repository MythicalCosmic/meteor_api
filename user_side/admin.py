from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter, RangeNumericFilter, ChoicesDropdownFilter
from .models import (
    User, AnonymousSession, Anime, Episode, EpisodeLanguage,
    Genre, WatchHistory, Like, Comment, Subscription, Payment,
    Advertisement, AdImpression, Favorite, Donation
)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ('email', 'display_full_name', 'display_premium_badge', 'role', 'is_staff', 'created_at')
    list_filter = (
        'is_premium', 
        'is_staff', 
        ('role', ChoicesDropdownFilter),
        'is_active',
        ('created_at', RangeDateFilter),
    )
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('Login Information', {
            'fields': ('email', 'password'),
            'description': 'User authentication credentials'
        }),
        ('Personal Details', {
            'fields': ('full_name', 'avatar', 'role')
        }),
        ('Premium Status', {
            'fields': ('is_premium', 'premium_expires_at'),
            'classes': ('tab',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('tab',)
        }),
        ('Important Dates', {
            'fields': ('last_login_at', 'created_at'),
            'classes': ('tab',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'role', 'is_premium'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login_at')
    
    @display(description='Full Name', label=True)
    def display_full_name(self, obj):
        return obj.full_name or 'No name set'
    
    @display(description='Account Type', label={'premium': 'success', 'regular': 'warning'})
    def display_premium_badge(self, obj):
        return 'premium' if obj.is_premium else 'regular'


@admin.register(AnonymousSession)
class AnonymousSessionAdmin(ModelAdmin):
    list_display = ('display_session_token', 'ip_address', 'country', 'city', 'total_visits', 'last_seen_at')
    search_fields = ('session_token', 'ip_address', 'city')
    list_filter = (
        'country',
        ('last_seen_at', RangeDateFilter),
    )
    readonly_fields = ('session_token', 'fingerprint_hash', 'first_seen_at', 'last_seen_at', 'total_visits')
    list_fullwidth = True
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_token', 'fingerprint_hash')
        }),
        ('Location', {
            'fields': ('ip_address', 'country', 'city')
        }),
        ('Activity', {
            'fields': ('first_seen_at', 'last_seen_at', 'total_visits')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    @display(description='Session Token')
    def display_session_token(self, obj):
        return f"{obj.session_token[:12]}..."


@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ('name', 'name_ru', 'slug', 'display_anime_count', 'created_at')
    search_fields = ('name', 'name_ru')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Names', {
            'fields': ('name', 'name_ru', 'slug')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('tab',)
        }),
    )
    
    @display(description='Total Anime', ordering='anime_count')
    def display_anime_count(self, obj):
        return obj.animes.count()


class EpisodeLanguageInline(TabularInline):
    model = EpisodeLanguage
    extra = 1
    fields = ('language', 'video_quality', 'video_url', 'display_file_size', 'is_default')
    readonly_fields = ('display_file_size',)
    
    @display(description='File Size')
    def display_file_size(self, obj):
        if obj.file_size_mb:
            try:
                size = float(obj.file_size_mb)
                if size > 1024:
                    return f"{size/1024:.2f} GB"
                return f"{size:.2f} MB"
            except:
                return obj.file_size_mb
        return "N/A"


@admin.register(Episode)
class EpisodeAdmin(ModelAdmin):
    list_display = ('episode_number', 'anime', 'title', 'display_status', 'display_duration', 'display_views', 'air_date')
    list_filter = (
        'is_published', 
        'is_premium_only', 
        'anime',
        ('air_date', RangeDateFilter),
        ('total_views', RangeNumericFilter),
    )
    search_fields = ('title', 'title_ru', 'anime__title')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('duration_seconds', 'total_views', 'total_likes', 'created_at')
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('Episode Information', {
            'fields': ('anime', 'episode_number', 'title', 'title_ru', 'slug')
        }),
        ('Content', {
            'fields': ('description', 'thumbnail_url')
        }),
        ('Settings', {
            'fields': ('air_date', 'is_premium_only', 'is_published'),
            'classes': ('tab',)
        }),
        ('Statistics', {
            'fields': ('duration_seconds', 'total_views', 'total_likes'),
            'classes': ('tab',)
        }),
    )
    
    inlines = [EpisodeLanguageInline]
    
    @display(description='Status', label={'published': 'success', 'draft': 'warning'})
    def display_status(self, obj):
        return 'published' if obj.is_published else 'draft'
    
    @display(description='Duration')
    def display_duration(self, obj):
        if obj.duration_seconds is not None:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "N/A"
    
    @display(description='Views', ordering='total_views')
    def display_views(self, obj):
        if obj.total_views is not None:
            return f"{obj.total_views:,}"
        return "0"


class EpisodeInline(TabularInline):
    model = Episode
    extra = 0
    fields = ('episode_number', 'title', 'is_published', 'air_date', 'total_views')
    readonly_fields = ('total_views',)
    show_change_link = True


@admin.register(Anime)
class AnimeAdmin(ModelAdmin):
    list_display = ('title', 'type', 'display_status', 'release_year', 'display_rating', 'display_episodes_count', 'display_views', 'is_published')
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('type', ChoicesDropdownFilter),
        'is_published', 
        'release_year', 
        'is_premium_only', 
        'genres',
        ('total_views', RangeNumericFilter),
    )
    search_fields = ('title', 'english_title', 'uzbek_title', 'russian_title')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres',)
    readonly_fields = ('total_views', 'total_likes', 'total_favorites', 'total_comments', 'rating', 'published_at', 'created_at', 'updated_at')
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('Title Information', {
            'fields': ('title', 'english_title', 'uzbek_title', 'russian_title', 'slug')
        }),
        ('Content', {
            'fields': ('description', 'genres')
        }),
        ('Details', {
            'fields': ('type', 'status', 'season', 'release_year', 'duration_minutes', 'total_episodes'),
            'classes': ('tab',)
        }),
        ('Media Files', {
            'fields': ('poster_url', 'banner_url', 'trailer_url'),
            'classes': ('tab',)
        }),
        ('Publication', {
            'fields': ('is_published', 'published_at', 'is_premium_only'),
            'classes': ('tab',)
        }),
        ('Statistics', {
            'fields': ('rating', 'total_views', 'total_likes', 'total_favorites', 'total_comments'),
            'classes': ('tab',)
        }),
    )
    
    inlines = [EpisodeInline]
    
    @display(description='Status', label={
        'ongoing': 'info',
        'completed': 'success',
        'announced': 'warning',
        'hiatus': 'danger',
        'cancelled': 'danger'
    })
    def display_status(self, obj):
        return obj.status.lower()
    
    @display(description='Rating', ordering='rating')
    def display_rating(self, obj):
        return f"⭐ {obj.rating}"
    
    @display(description='Episodes')
    def display_episodes_count(self, obj):
        published = obj.episodes.filter(is_published=True).count()
        total = obj.total_episodes
        return f"{published}/{total}"
    
    @display(description='Views', ordering='total_views')
    def display_views(self, obj):
        return f"{obj.total_views:,}"


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'display_plan', 'display_status', 'display_price', 'starts_at', 'expires_at', 'display_auto_renew')
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('plan_type', ChoicesDropdownFilter),
        'auto_renew',
        ('starts_at', RangeDateFilter),
        ('expires_at', RangeDateFilter),
    )
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Plan Details', {
            'fields': ('plan_type', 'price', 'currency', 'status')
        }),
        ('Duration', {
            'fields': ('starts_at', 'expires_at', 'auto_renew')
        }),
    )
    
    @display(description='Plan')
    def display_plan(self, obj):
        return obj.get_plan_type_display()
    
    @display(description='Status', label={
        'active': 'success',
        'expired': 'danger',
        'cancelled': 'warning',
        'pending': 'info'
    })
    def display_status(self, obj):
        return obj.status
    
    @display(description='Price')
    def display_price(self, obj):
        return f"{obj.price:,.0f} {obj.currency}"
    
    @display(description='Auto-Renew', boolean=True)
    def display_auto_renew(self, obj):
        return obj.auto_renew


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('transaction_id', 'user', 'display_amount', 'display_status', 'payment_method', 'paid_at')
    list_filter = (
        ('status', ChoicesDropdownFilter),
        'currency', 
        'payment_gateway',
        ('paid_at', RangeDateFilter),
    )
    search_fields = ('user__email', 'transaction_id')
    readonly_fields = ('paid_at', 'created_at')
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('Transaction', {
            'fields': ('user', 'subscription', 'transaction_id')
        }),
        ('Payment Details', {
            'fields': ('payment_gateway', 'payment_method', 'amount', 'currency', 'status')
        }),
    )
    
    @display(description='Amount')
    def display_amount(self, obj):
        return f"{obj.amount:,.0f} {obj.currency}"
    
    @display(description='Status', label={
        'completed': 'success',
        'pending': 'warning',
        'failed': 'danger',
        'refunded': 'info'
    })
    def display_status(self, obj):
        return obj.status


@admin.register(Advertisement)
class AdvertisementAdmin(ModelAdmin):
    list_display = ('title', 'display_type', 'position', 'display_active', 'priority', 'display_impressions', 'display_clicks', 'display_ctr')
    list_filter = (
        ('type', ChoicesDropdownFilter),
        ('position', ChoicesDropdownFilter),
        'is_active',
    )
    search_fields = ('title',)
    readonly_fields = ('total_impressions', 'total_clicks', 'created_at')
    list_filter_submit = True
    list_fullwidth = True
    
    fieldsets = (
        ('Ad Information', {
            'fields': ('title', 'type', 'position', 'priority')
        }),
        ('Content', {
            'fields': ('content_url', 'html_code', 'duration_seconds', 'click_url')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Performance', {
            'fields': ('total_impressions', 'total_clicks'),
            'classes': ('tab',)
        }),
    )
    
    @display(description='Type')
    def display_type(self, obj):
        return obj.get_type_display()
    
    @display(description='Status', boolean=True)
    def display_active(self, obj):
        return obj.is_active
    
    @display(description='Impressions', ordering='total_impressions')
    def display_impressions(self, obj):
        return f"{obj.total_impressions:,}"
    
    @display(description='Clicks', ordering='total_clicks')
    def display_clicks(self, obj):
        return f"{obj.total_clicks:,}"
    
    @display(description='CTR')
    def display_ctr(self, obj):
        if obj.total_impressions > 0:
            ctr = (obj.total_clicks / obj.total_impressions) * 100
            return f"{ctr:.2f}%"
        return "0%"


class ReadOnlyAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WatchHistory)
class WatchHistoryAdmin(ReadOnlyAdmin):
    list_display = ('display_user', 'anime', 'episode', 'display_progress', 'watched_at', 'country')
    list_filter = (
        'completed', 
        'country', 
        'device_type',
        ('watched_at', RangeDateFilter),
    )
    search_fields = ('user__email', 'anime__title', 'episode__title')
    list_filter_submit = True
    list_fullwidth = True
    
    @display(description='User')
    def display_user(self, obj):
        if obj.user:
            return obj.user.email
        return 'Guest'
    
    @display(description='Progress', label={'completed': 'success', 'started': 'info'})
    def display_progress(self, obj):
        if obj.completed:
            return 'completed'
        if obj.watch_duration_seconds and obj.episode.duration_seconds:
            percent = (obj.watch_duration_seconds / obj.episode.duration_seconds) * 100
            return f"{round(percent)}%"
        return 'started'


@admin.register(Like)
class LikeAdmin(ReadOnlyAdmin):
    list_display = ('display_user', 'display_target', 'display_reaction', 'created_at')
    list_filter = ('is_like', ('created_at', RangeDateFilter))
    search_fields = ('user__email', 'anime__title', 'episode__title')
    list_fullwidth = True
    
    @display(description='User')
    def display_user(self, obj):
        if obj.user:
            return obj.user.email
        return 'Guest'
    
    @display(description='Target')
    def display_target(self, obj):
        if obj.episode:
            return f"{obj.episode.anime.title} - Ep {obj.episode.episode_number}"
        return obj.anime.title
    
    @display(description='Reaction', label={'like': 'success', 'dislike': 'danger'})
    def display_reaction(self, obj):
        return 'like' if obj.is_like else 'dislike'


@admin.register(Comment)
class CommentAdmin(ReadOnlyAdmin):
    list_display = ('display_author', 'display_target', 'display_comment_preview', 'display_approved', 'created_at')
    list_filter = ('is_approved', ('created_at', RangeDateFilter))
    search_fields = ('comment', 'user__email', 'guest_name', 'anime__title', 'episode__title')
    list_fullwidth = True
    
    @display(description='Author')
    def display_author(self, obj):
        if obj.user:
            return obj.user.full_name or obj.user.email
        return obj.guest_name or 'Guest'
    
    @display(description='On')
    def display_target(self, obj):
        if obj.episode:
            return f"{obj.episode.anime.title} - Ep {obj.episode.episode_number}"
        return obj.anime.title if obj.anime else "N/A"
    
    @display(description='Comment')
    def display_comment_preview(self, obj):
        preview = obj.comment[:60] + "..." if len(obj.comment) > 60 else obj.comment
        return preview
    
    @display(description='Approved', boolean=True)
    def display_approved(self, obj):
        return obj.is_approved


@admin.register(AdImpression)
class AdImpressionAdmin(ReadOnlyAdmin):
    list_display = ('ad', 'display_user', 'anime', 'episode', 'display_interaction', 'viewed_at')
    list_filter = ('clicked', ('viewed_at', RangeDateFilter))
    search_fields = ('ad__title', 'user__email', 'anime__title')
    list_fullwidth = True
    
    @display(description='User')
    def display_user(self, obj):
        if obj.user:
            return obj.user.email
        return 'Guest'
    
    @display(description='Action', label={'clicked': 'info', 'viewed': 'warning'})
    def display_interaction(self, obj):
        return 'clicked' if obj.clicked else 'viewed'


@admin.register(Favorite)
class FavoriteAdmin(ReadOnlyAdmin):
    list_display = ('display_user', 'anime', 'added_at')
    search_fields = ('user__email', 'anime__title')
    list_filter = (('added_at', RangeDateFilter),)
    list_fullwidth = True
    
    @display(description='User')
    def display_user(self, obj):
        if obj.user:
            return obj.user.email
        return 'Guest'

@admin.register(Donation)
class DonationAdmin(ModelAdmin):
    list_display = ('display_donor', 'display_amount', 'message', 'created_at')
    list_filter = (('created_at', RangeDateFilter),)
    search_fields = ('user__full_name', 'user__email', 'name', 'message')
    readonly_fields = ('created_at',)
    list_fullwidth = True

    @display(description='Donor')
    def display_donor(self, obj):
        if obj.user:
            return obj.user.full_name or obj.user.email
        return obj.name or "Anonymous"

    @display(description='Amount (UZS)', ordering='amount')
    def display_amount(self, obj):
        return f"{obj.amount:,.0f} UZS"

admin.site.site_header = 'Meteor Anime Administration'
admin.site.site_title = 'Meteor Admin'
admin.site.index_title = 'Dashboard'