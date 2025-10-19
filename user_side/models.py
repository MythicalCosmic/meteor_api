from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

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
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)
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
    session_token = models.TextField()
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
    title = models.TextField()
    slug = models.SlugField(unique=True)
    english_title = models.TextField()
    uzbek_title = models.TextField()
    description = models.TextField()
    type = models.TextField()
    status = models.TextField()
    total_episodes = models.IntegerField()
    duration_minutes = models.IntegerField()
    release_year = models.IntegerField()
    season = models.TextField()
    poster_url = models.FileField(upload_to='anime/posters/')
    banner_url = models.FileField(upload_to='anime/banners/')
    trailer_url = models.FileField(upload_to='anime/trailers/')
    rating = models.FloatField()
    total_views = models.IntegerField()
    total_likes = models.IntegerField()
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
    title = models.TextField()
    slug = models.TextField()
    description = models.TextField()
    thumbnail_url = models.FileField(upload_to='episodes/thumbnails/')
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
    language = models.TextField(default='uzbek')
    video_url = models.FileField(upload_to='episodes/videos/')
    video_quality = models.TextField()
    file_size_mb = models.TextField()
    is_default = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous_session = models.ForeignKey(AnonymousSession, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    watch_duration_seconds = models.IntegerField()
    completed = models.BooleanField(default=False) 
    watched_at = models.DateTimeField()
    ip_address = models.TextField()
    device_type = models.TextField()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous_session = models.ForeignKey(AnonymousSession, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    is_like = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous_session = models.ForeignKey(AnonymousSession, on_delete=models.CASCADE, null=True, blank=True)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    parent_id = models.IntegerField()
    comment = models.TextField()
    guest_name = models.TextField()
    is_approved = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class AnimeView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous_session = models.ForeignKey(AnonymousSession, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField()
    ip_address = models.TextField()
    country = models.TextField(default='UZ')

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
    content_url = models.FileField(upload_to='ads/content/')
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