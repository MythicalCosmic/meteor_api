from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
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

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'premium_badge', 'role', 'is_staff', 'created_at')
    list_filter = ('is_premium', 'is_staff', 'role', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Login Information', {'fields': ('email', 'password')}),
        ('Personal Details', {'fields': ('full_name', 'avatar', 'role')}),
        ('Premium Status', {'fields': ('is_premium', 'premium_expires_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login_at', 'created_at'), 'classes': ('collapse',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'role', 'is_premium'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login_at')
    
    def premium_badge(self, obj):
        if obj.is_premium:
            return format_html('<span style="color: gold;">⭐ Premium</span>')
        return format_html('<span style="color: gray;">Regular</span>')
    premium_badge.short_description = 'Account Type'

class AnonymousSessionAdmin(admin.ModelAdmin):
    list_display = ('short_token', 'ip_address', 'country', 'city', 'total_visits', 'last_seen_at')
    search_fields = ('session_token', 'ip_address', 'city')
    list_filter = ('country',)
    readonly_fields = ('session_token', 'fingerprint_hash', 'first_seen_at', 'last_seen_at', 'total_visits')
    
    fieldsets = (
        ('Session Information', {'fields': ('session_token', 'fingerprint_hash')}),
        ('Location', {'fields': ('ip_address', 'country', 'city')}),
        ('Activity', {'fields': ('first_seen_at', 'last_seen_at', 'total_visits')}),
    )
    
    def has_add_permission(self, request):
        return False
    
    def short_token(self, obj):
        return f"{obj.session_token[:12]}..."
    short_token.short_description = 'Session Token'

class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'slug', 'anime_count', 'created_at')
    search_fields = ('name', 'name_ru')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Names', {'fields': ('name', 'name_ru', 'slug')}),
        ('Details', {'fields': ('description',)}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def anime_count(self, obj):
        count = obj.animes.count()
        return format_html('<strong>{}</strong> anime', count)
    anime_count.short_description = 'Total Anime'

class EpisodeLanguageInline(admin.TabularInline):
    model = EpisodeLanguage
    extra = 1
    fields = ('language', 'video_quality', 'video_url', 'file_size_display', 'is_default')
    readonly_fields = ('file_size_display',)
    
    def file_size_display(self, obj):
        if obj.file_size_mb:
            try:
                size = float(obj.file_size_mb)
                if size > 1024:
                    return f"{size/1024:.2f} GB"
                return f"{size:.2f} MB"
            except:
                return obj.file_size_mb
        return "N/A"
    file_size_display.short_description = 'File Size'

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('episode_number', 'anime', 'title', 'status_badge', 'duration_display', 'views_display', 'air_date')
    list_filter = ('is_published', 'is_premium_only', 'anime')
    search_fields = ('title', 'title_ru', 'anime__title')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('duration_seconds', 'total_views', 'total_likes', 'created_at')
    
    fieldsets = (
        ('Episode Information', {'fields': ('anime', 'episode_number', 'title', 'title_ru', 'slug')}),
        ('Content', {'fields': ('description', 'thumbnail_url')}),
        ('Settings', {'fields': ('air_date', 'is_premium_only', 'is_published')}),
        ('Statistics', {'fields': ('duration_seconds', 'total_views', 'total_likes'), 'classes': ('collapse',)}),
        ('Dates', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    inlines = [EpisodeLanguageInline]
    
    def status_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color: green;">✓ Published</span>')
        return format_html('<span style="color: orange;">⏳ Draft</span>')
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        if obj.duration_seconds is not None:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "N/A"
    duration_display.short_description = 'Duration'
    
    def views_display(self, obj):
        if obj.total_views is not None:
            return f"{obj.total_views:,}"
        return "0"
    views_display.short_description = 'Views'

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0
    fields = ('episode_number', 'title', 'is_published', 'air_date', 'total_views')
    readonly_fields = ('total_views',)
    show_change_link = True

class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status_badge', 'release_year', 'rating_display', 'episodes_count', 'views_display', 'is_published')
    list_filter = ('status', 'type', 'is_published', 'release_year', 'is_premium_only', 'genres')
    search_fields = ('title', 'english_title', 'uzbek_title', 'russian_title')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres',)
    readonly_fields = ('total_views', 'total_likes', 'total_favorites', 'total_comments', 'rating', 'published_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Title Information', {'fields': ('title', 'english_title', 'uzbek_title', 'russian_title', 'slug')}),
        ('Content', {'fields': ('description', 'genres')}),
        ('Details', {'fields': ('type', 'status', 'season', 'release_year', 'duration_minutes', 'total_episodes')}),
        ('Media Files', {'fields': ('poster_url', 'banner_url', 'trailer_url')}),
        ('Publication', {'fields': ('is_published', 'published_at', 'is_premium_only')}),
        ('Statistics', {'fields': ('rating', 'total_views', 'total_likes', 'total_favorites', 'total_comments'), 'classes': ('collapse',)}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    inlines = [EpisodeInline]
    
    def status_badge(self, obj):
        colors = {
            'ONGOING': 'blue',
            'COMPLETED': 'green',
            'ANNOUNCED': 'orange',
            'HIATUS': 'gray',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">●</span> {}', color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def rating_display(self, obj):
        stars = '⭐' * int(obj.rating)
        return format_html('{} {}', stars, obj.rating)
    rating_display.short_description = 'Rating'
    
    def episodes_count(self, obj):
        published = obj.episodes.filter(is_published=True).count()
        total = obj.total_episodes
        return format_html('{}/{}', published, total)
    episodes_count.short_description = 'Episodes'
    
    def views_display(self, obj):
        return f"{obj.total_views:,}"
    views_display.short_description = 'Views'

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_badge', 'status_badge', 'price_display', 'starts_at', 'expires_at', 'auto_renew_badge')
    list_filter = ('status', 'plan_type', 'auto_renew')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Plan Details', {'fields': ('plan_type', 'price', 'currency', 'status')}),
        ('Duration', {'fields': ('starts_at', 'expires_at', 'auto_renew')}),
        ('Dates', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    def plan_badge(self, obj):
        return format_html('<strong>{}</strong>', obj.get_plan_type_display())
    plan_badge.short_description = 'Plan'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'gray',
            'pending': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">●</span> {}', color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def price_display(self, obj):
        return f"{obj.price:,.0f} {obj.currency}"
    price_display.short_description = 'Price'
    
    def auto_renew_badge(self, obj):
        if obj.auto_renew:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: gray;">✗ No</span>')
    auto_renew_badge.short_description = 'Auto-Renew'

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount_display', 'status_badge', 'payment_method', 'paid_at')
    list_filter = ('status', 'currency', 'payment_gateway')
    search_fields = ('user__email', 'transaction_id')
    readonly_fields = ('paid_at', 'created_at')
    
    fieldsets = (
        ('Transaction', {'fields': ('user', 'subscription', 'transaction_id')}),
        ('Payment Details', {'fields': ('payment_gateway', 'payment_method', 'amount', 'currency', 'status')}),
        ('Dates', {'fields': ('paid_at', 'created_at'), 'classes': ('collapse',)}),
    )
    
    def amount_display(self, obj):
        return format_html('<strong>{:,.0f}</strong> {}', obj.amount, obj.currency)
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
            'refunded': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">●</span> {}', color, obj.get_status_display())
    status_badge.short_description = 'Status'

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type_badge', 'position', 'active_badge', 'priority', 'impressions_display', 'clicks_display', 'ctr_display')
    list_filter = ('type', 'position', 'is_active')
    search_fields = ('title',)
    readonly_fields = ('total_impressions', 'total_clicks', 'created_at')
    
    fieldsets = (
        ('Ad Information', {'fields': ('title', 'type', 'position', 'priority')}),
        ('Content', {'fields': ('content_url', 'html_code', 'duration_seconds', 'click_url')}),
        ('Status', {'fields': ('is_active',)}),
        ('Performance', {'fields': ('total_impressions', 'total_clicks'), 'classes': ('collapse',)}),
        ('Dates', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    def type_badge(self, obj):
        return obj.get_type_display()
    type_badge.short_description = 'Type'
    
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">🟢 Active</span>')
        return format_html('<span style="color: red;">🔴 Inactive</span>')
    active_badge.short_description = 'Status'
    
    def impressions_display(self, obj):
        return f"{obj.total_impressions:,}"
    impressions_display.short_description = 'Impressions'
    
    def clicks_display(self, obj):
        return f"{obj.total_clicks:,}"
    clicks_display.short_description = 'Clicks'
    
    def ctr_display(self, obj):
        if obj.total_impressions > 0:
            ctr = (obj.total_clicks / obj.total_impressions) * 100
            return format_html('{}%', round(ctr, 2))
        return "0%"
    ctr_display.short_description = 'CTR'

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class WatchHistoryAdmin(ReadOnlyAdmin):
    list_display = ('user_display', 'anime', 'episode', 'progress_bar', 'watched_at', 'country')
    list_filter = ('completed', 'country', 'device_type')
    search_fields = ('user__email', 'anime__title', 'episode__title')
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: gray;">Guest</span>')
    user_display.short_description = 'User'
    
    def progress_bar(self, obj):
        if obj.completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        if obj.watch_duration_seconds and obj.episode.duration_seconds:
            percent = (obj.watch_duration_seconds / obj.episode.duration_seconds) * 100
            return format_html('{}%', round(percent))
        return "Started"
    progress_bar.short_description = 'Progress'

class LikeAdmin(ReadOnlyAdmin):
    list_display = ('user_display', 'target', 'reaction', 'created_at')
    list_filter = ('is_like',)
    search_fields = ('user__email', 'anime__title', 'episode__title')
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: gray;">Guest</span>')
    user_display.short_description = 'User'
    
    def target(self, obj):
        if obj.episode:
            return f"{obj.episode.anime.title} - Ep {obj.episode.episode_number}"
        return obj.anime.title
    target.short_description = 'Target'
    
    def reaction(self, obj):
        if obj.is_like:
            return format_html('<span style="color: green;">👍 Like</span>')
        return format_html('<span style="color: red;">👎 Dislike</span>')
    reaction.short_description = 'Reaction'

class CommentAdmin(ReadOnlyAdmin):
    list_display = ('author_display', 'target', 'comment_preview', 'approved_badge', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('comment', 'user__email', 'guest_name', 'anime__title', 'episode__title')
    
    def author_display(self, obj):
        if obj.user:
            return obj.user.full_name or obj.user.email
        return obj.guest_name or format_html('<span style="color: gray;">Guest</span>')
    author_display.short_description = 'Author'
    
    def target(self, obj):
        if obj.episode:
            return f"{obj.episode.anime.title} - Ep {obj.episode.episode_number}"
        return obj.anime.title if obj.anime else "N/A"
    target.short_description = 'On'
    
    def comment_preview(self, obj):
        preview = obj.comment[:60] + "..." if len(obj.comment) > 60 else obj.comment
        return preview
    comment_preview.short_description = 'Comment'
    
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">⏳</span>')
    approved_badge.short_description = 'Approved'

class AdImpressionAdmin(ReadOnlyAdmin):
    list_display = ('ad', 'user_display', 'anime', 'episode', 'interaction', 'viewed_at')
    list_filter = ('clicked',)
    search_fields = ('ad__title', 'user__email', 'anime__title')
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: gray;">Guest</span>')
    user_display.short_description = 'User'
    
    def interaction(self, obj):
        if obj.clicked:
            return format_html('<span style="color: blue;">🖱️ Clicked</span>')
        return format_html('<span style="color: gray;">👁️ Viewed</span>')
    interaction.short_description = 'Action'

class FavoriteAdmin(ReadOnlyAdmin):
    list_display = ('user_display', 'anime', 'added_at')
    search_fields = ('user__email', 'anime__title')
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: gray;">Guest</span>')
    user_display.short_description = 'User'

admin.site.site_header = 'Anime Platform Administration'
admin.site.site_title = 'Anime Admin'
admin.site.index_title = 'Welcome to Anime Platform Admin'

admin.site.register(User, CustomUserAdmin)
admin.site.register(AnonymousSession, AnonymousSessionAdmin)
admin.site.register(Anime, AnimeAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(EpisodeLanguage)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)
admin.site.register(WatchHistory, WatchHistoryAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(AdImpression, AdImpressionAdmin)
admin.site.register(Favorite, FavoriteAdmin)