from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from moviepy.video.io.VideoFileClip import VideoFileClip

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    avatar = models.FileField(upload_to='media/avatars/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=['email'], name='user_email_index'),
            models.Index(fields=['full_name'], name='user_full_name_index'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['email'], name='user_email_unique')
        ]

class AnonymousSession(models.Model):
    session_token = models.CharField(max_length=100)
    fingerprint_hash = models.TextField()
    ip_address = models.TextField()
    country = models.TextField(default='UZ')
    city = models.TextField()
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    total_visits = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session_token'], name='anonymoussession_session_token_unique')
        ]

class Genre(models.Model):
    name = models.CharField(max_length=100) 
    name_ru = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=100)  
    description = models.TextField(blank=True, default='') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='genre_name_unique'),
        ]

class Anime(models.Model):
    TYPE_CHOICES = (
        ('TV', 'TV Series'),
        ('MOVIE', 'Movie'),
        ('OVA', 'Original Video Animation'),
        ('ONA', 'Original Net Animation'),
        ('SPECIAL', 'Special'),
    )
    STATUS_CHOICES = (
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('ANNOUNCED', 'Announced'),
        ('HIATUS', 'Hiatus'),
        ('CANCELLED', 'Cancelled'),
    )
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    english_title = models.CharField(max_length=50)
    russian_title = models.CharField(max_length=50, null=True, blank=True)
    uzbek_title = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TV') 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ONGOING')
    total_episodes = models.IntegerField()
    duration_minutes = models.IntegerField()
    release_year = models.IntegerField()
    season = models.TextField()
    poster_url = models.FileField(upload_to='media/anime/posters/')
    banner_url = models.FileField(upload_to='media/anime/banners/')
    trailer_url = models.FileField(upload_to='media/anime/trailers/')
    rating = models.FloatField()
    total_views = models.IntegerField()
    total_favorites = models.IntegerField()
    total_likes = models.IntegerField()
    total_comments = models.IntegerField()
    is_premium_only = models.BooleanField(default=False) 
    is_published = models.BooleanField(default=False)  
    published_at = models.DateTimeField()
    genres = models.ManyToManyField(Genre, related_name='animes') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['title', 'english_title', 'uzbek_title', 'type', 'status', 'release_year', 'is_premium_only', 'created_at', 'updated_at'], name='anime_name_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['slug'], name='anime_slug_unique')
        ]

class Episode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    episode_number = models.IntegerField()
    title = models.CharField(max_length=50)
    title_ru = models.CharField(max_length=50, blank=True, null=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    total_likes = models.IntegerField()
    thumbnail_url = models.FileField(upload_to='media/episodes/thumbnails/')
    duration_seconds = models.BigIntegerField()
    air_date = models.DateTimeField()
    is_premium_only = models.BooleanField(default=False) 
    total_views = models.IntegerField()
    is_published = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['anime', 'episode_number'], name='episode_number_unique_per_anime')
        ]

class EpisodeLanguage(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    language = models.CharField(max_length=50, default='uzbek')
    video_url = models.FileField(upload_to='media/episodes/videos/')
    video_quality = models.CharField(max_length=50, default='1080p')
    file_size_mb = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        if self.video_url:
            try:
                self.file_size_mb = self.video_url.size / (1024 * 1024)
                
                clip = VideoFileClip(self.video_url.path)
                duration = clip.duration
                clip.close()
                if self.is_default:
                    self.episode.duration_seconds = int(duration)
                    self.episode.save(update_fields=['duration_seconds'])
            except Exception as e:
                print(f"Error processing video: {e}")  
                self.file_size_mb = 0  
            super().save(update_fields=['file_size_mb'])


class WatchHistory(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)
    anonymous_session = models.ForeignKey('AnonymousSession', on_delete=models.CASCADE, null=True, blank=True)
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE)
    episode = models.ForeignKey('Episode', on_delete=models.CASCADE)
    watch_duration_seconds = models.IntegerField(null=True, blank=True) 
    completed = models.BooleanField(default=False, null=True, blank=True)  
    watched_at = models.DateTimeField()
    ip_address = models.CharField(max_length=45)
    device_type = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='UZ')  

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False, anonymous_session__isnull=True) |
                      models.Q(user__isnull=True, anonymous_session__isnull=False),
                name='watch_history_user_or_session'
            ),
            models.UniqueConstraint(
                fields=['user', 'anime', 'episode'],
                condition=models.Q(user__isnull=False),
                name='unique_user_anime_episode'
            ),
            models.UniqueConstraint(
                fields=['anonymous_session', 'anime', 'episode'],
                condition=models.Q(anonymous_session__isnull=False),
                name='unique_session_anime_episode'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'anime', 'episode']),
            models.Index(fields=['anonymous_session', 'anime', 'episode']),
            models.Index(fields=['anime', 'watched_at']),
            models.Index(fields=['episode', 'watched_at'])
        ]

    def save(self, *args, **kwargs):
        if not self.watched_at:
            self.watched_at = timezone.now()
        super().save(*args, **kwargs)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_session = models.ForeignKey('AnonymousSession', on_delete=models.CASCADE, null=True, blank=True)
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE, null=True, blank=True)
    episode = models.ForeignKey('Episode', on_delete=models.CASCADE, null=True, blank=True)
    is_like = models.BooleanField(default=True)  
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'anime'],
                condition=models.Q(user__isnull=False, anime__isnull=False, episode__isnull=True),
                name='unique_user_anime_like'
            ),
            models.UniqueConstraint(
                fields=['user', 'episode'],
                condition=models.Q(user__isnull=False, episode__isnull=False),
                name='unique_user_episode_like'
            ),
            models.UniqueConstraint(
                fields=['anonymous_session', 'anime'],
                condition=models.Q(anonymous_session__isnull=False, anime__isnull=False, episode__isnull=True),
                name='unique_anon_anime_like'
            ),
            models.UniqueConstraint(
                fields=['anonymous_session', 'episode'],
                condition=models.Q(anonymous_session__isnull=False, episode__isnull=False),
                name='unique_anon_episode_like'
            ),
        ]
        indexes = [
            models.Index(fields=['anime', 'is_like']),
            models.Index(fields=['episode', 'is_like']),
        ]

    def __str__(self):
        target = self.episode or self.anime
        user_str = self.user.username if self.user else f"Anon-{self.anonymous_session_id}"
        return f"{user_str} {'liked' if self.is_like else 'disliked'} {target}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_session = models.ForeignKey('AnonymousSession', on_delete=models.CASCADE, null=True, blank=True)
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE, null=True, blank=True)
    episode = models.ForeignKey('Episode', on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    comment = models.TextField()
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    is_approved = models.BooleanField(default=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['anime', 'is_approved', '-created_at']),
            models.Index(fields=['episode', 'is_approved', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else (self.guest_name or f"Anon-{self.anonymous_session_id}")
        target = self.episode or self.anime
        return f"{user_str} commented on {target}"

    @property
    def author_name(self):
        if self.user:
            return self.user.username
        return self.guest_name or "Anonymous"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_type = models.TextField()
    price = models.FloatField()
    currency = models.TextField()
    status = models.TextField()
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    payment_gateway = models.TextField()
    transaction_id = models.IntegerField()
    amount = models.FloatField()
    currency = models.TextField(default='UZS')
    status = models.TextField()
    payment_method = models.TextField()
    paid_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class Advertisement(models.Model):
    title = models.TextField()
    type = models.TextField()
    content_url = models.FileField(upload_to='media/ads/content/')
    html_code = models.TextField()
    duration_seconds = models.IntegerField()
    click_url = models.URLField()
    position = models.TextField()
    is_active = models.BooleanField(default=False)  
    priority = models.IntegerField()
    total_impressions = models.IntegerField()
    total_clicks = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class AdImpression(models.Model):
    ad = models.ForeignKey(Advertisement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous_session = models.ForeignKey(AnonymousSession, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    clicked = models.BooleanField(default=False)
    viewed_at = models.DateTimeField()
    ip_address = models.TextField()


class Favorite(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)
    anonymous_session = models.ForeignKey('AnonymousSession', on_delete=models.CASCADE, null=True, blank=True)
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE, related_name='favorites')
    added_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False, anonymous_session__isnull=True) |
                      models.Q(user__isnull=True, anonymous_session__isnull=False),
                name='favorite_user_or_session'
            ),
            models.UniqueConstraint(
                fields=['user', 'anime'],
                condition=models.Q(user__isnull=False),
                name='unique_user_anime_favorite'
            ),
            models.UniqueConstraint(
                fields=['anonymous_session', 'anime'],
                condition=models.Q(anonymous_session__isnull=False),
                name='unique_session_anime_favorite'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'anime']),
            models.Index(fields=['anonymous_session', 'anime']),
            models.Index(fields=['anime', 'added_at'])
        ]

    def save(self, *args, **kwargs):
        if not self.added_at:
            self.added_at = timezone.now()
        super().save(*args, **kwargs)