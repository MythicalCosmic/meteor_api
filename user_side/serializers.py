from rest_framework import serializers
from rest_framework.serializers import Serializer, IntegerField, BooleanField
from django.contrib.auth.hashers import make_password, check_password
from .models import *


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not check_password(data['password'], user.password):
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar', 'is_premium', 'created_at']
    
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class EpisodeLanguageSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EpisodeLanguage
        fields = [
            'id', 'language', 'video_url', 'video_quality', 
            'file_size_mb', 'is_default'
        ]
    
    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video_url and request:
            return request.build_absolute_uri(obj.video_url.url)
        return None


class FirstEpisodeSerializer(serializers.ModelSerializer):
    languages = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Episode
        fields = [
            'id', 'episode_number', 'title', 'slug', 'thumbnail_url',
            'duration_seconds', 'air_date', 'is_premium_only', 'languages'
        ]
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail_url and request:
            return request.build_absolute_uri(obj.thumbnail_url.url)
        return None
    
    def get_languages(self, obj):
        request = self.context.get('request')
        episode_languages = EpisodeLanguage.objects.filter(episode=obj)
        return EpisodeLanguageSerializer(
            episode_languages, 
            many=True, 
            context={'request': request}
        ).data


class AnimeSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    first_episode = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    trailer_url = serializers.SerializerMethodField()

    class Meta:
        model = Anime
        fields = [
            'id', 'slug', 'title', 'english_title', 'uzbek_title', 'description',
            'type', 'status', 'total_episodes', 'duration_minutes', 'release_year',
            'season', 'poster_url', 'banner_url', 'trailer_url', 'rating',
            'total_views', 'total_likes', 'is_premium_only', 'is_published', 'published_at',
            'created_at', 'updated_at', 'genres', 'first_episode'
        ]
    
    def get_poster_url(self, obj):
        request = self.context.get('request')
        if obj.poster_url and request:
            return request.build_absolute_uri(obj.poster_url.url)
        return None
    
    def get_banner_url(self, obj):
        request = self.context.get('request')
        if obj.banner_url and request:
            return request.build_absolute_uri(obj.banner_url.url)
        return None
    
    def get_trailer_url(self, obj):
        request = self.context.get('request')
        if obj.trailer_url and request:
            return request.build_absolute_uri(obj.trailer_url.url)
        return None

    def get_first_episode(self, obj):
        request = self.context.get('request')
        first_episode = Episode.objects.filter(
            anime=obj, 
            is_published=True
        ).order_by('episode_number').first()
        
        if first_episode:
            return FirstEpisodeSerializer(
                first_episode, 
                context={'request': request}
            ).data
        return None


class AnonymousSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousSession
        fields = '__all__'


class EpisodeSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    anime_title = serializers.CharField(source='anime.title', read_only=True)
    languages = serializers.SerializerMethodField()
    
    class Meta:
        model = Episode
        fields = [
            'id', 'anime_title', 'episode_number', 'title', 'slug',
            'description', 'thumbnail_url', 'duration_seconds',
            'air_date', 'is_premium_only', 'total_views', 'is_published',
            'languages'
        ]
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail_url and request:
            return request.build_absolute_uri(obj.thumbnail_url.url)
        return None
    
    def get_languages(self, obj):
        request = self.context.get('request')
        episode_languages = EpisodeLanguage.objects.filter(episode=obj)
        return EpisodeLanguageSerializer(
            episode_languages,
            many=True,
            context={'request': request}
        ).data


class EpisodeDetailSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    anime = serializers.SerializerMethodField()
    next_episode = serializers.SerializerMethodField()
    previous_episode = serializers.SerializerMethodField()
    
    class Meta:
        model = Episode
        fields = [
            'id', 'episode_number', 'title', 'slug', 'description',
            'thumbnail_url', 'duration_seconds', 'air_date',
            'is_premium_only', 'total_views', 'languages',
            'anime', 'next_episode', 'previous_episode'
        ]
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail_url and request:
            return request.build_absolute_uri(obj.thumbnail_url.url)
        return None
    
    def get_languages(self, obj):
        request = self.context.get('request')
        episode_languages = EpisodeLanguage.objects.filter(episode=obj)
        return EpisodeLanguageSerializer(
            episode_languages,
            many=True,
            context={'request': request}
        ).data
    
    def get_anime(self, obj):
        return {
            'id': obj.anime.id,
            'title': obj.anime.title,
            'slug': obj.anime.slug,
            'poster_url': self.context['request'].build_absolute_uri(obj.anime.poster_url.url) if obj.anime.poster_url else None
        }
    
    def get_next_episode(self, obj):
        next_ep = Episode.objects.filter(
            anime=obj.anime,
            episode_number__gt=obj.episode_number,
            is_published=True
        ).order_by('episode_number').first()
        
        if next_ep:
            return {
                'id': next_ep.id,
                'episode_number': next_ep.episode_number,
                'title': next_ep.title,
                'slug': next_ep.slug
            }
        return None
    
    def get_previous_episode(self, obj):
        prev_ep = Episode.objects.filter(
            anime=obj.anime,
            episode_number__lt=obj.episode_number,
            is_published=True
        ).order_by('-episode_number').first()
        
        if prev_ep:
            return {
                'id': prev_ep.id,
                'episode_number': prev_ep.episode_number,
                'title': prev_ep.title,
                'slug': prev_ep.slug
            }
        return None
    

class GenreSerializer(serializers.ModelSerializer):
    anime_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug', 'description', 'anime_count', 'created_at']
    
    def get_anime_count(self, obj):
        return obj.animes.filter(is_published=True).count()


class GenreDetailSerializer(serializers.ModelSerializer):
    anime_count = serializers.SerializerMethodField()
    top_animes = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug', 'description', 'anime_count', 'top_animes', 'created_at', 'updated_at']
    
    def get_anime_count(self, obj):
        return obj.animes.filter(is_published=True).count()
    
    def get_top_animes(self, obj):
        request = self.context.get('request')
        top_animes = obj.animes.filter(is_published=True).order_by('-rating', '-total_views')[:5]
        
        return [{
            'id': anime.id,
            'title': anime.title,
            'slug': anime.slug,
            'rating': anime.rating,
            'total_views': anime.total_views,
            'poster_url': request.build_absolute_uri(anime.poster_url.url) if anime.poster_url and request else None
        } for anime in top_animes]



class WatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchHistory
        fields = ['watch_duration_seconds', 'completed', 'country']

    def validate(self, data):
        if 'episode' not in self.context:
            raise serializers.ValidationError("Episode context is missing.")
        
        episode = self.context['episode']
        watch_duration_seconds = data.get('watch_duration_seconds')
        completed = data.get('completed', False)

        if watch_duration_seconds is not None:
            if watch_duration_seconds > episode.duration_seconds:
                raise serializers.ValidationError("Watch duration cannot exceed episode duration.")
            if completed and watch_duration_seconds < episode.duration_seconds * 0.9:
                raise serializers.ValidationError("Episode cannot be marked completed if watched less than 90%.")
        return data
    
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'is_like', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        if 'is_like' not in data:
            data['is_like'] = True
        return data


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(read_only=True)
    replies_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author_name', 'comment', 'guest_name',
            'parent', 'is_approved', 'replies_count',
            'can_edit', 'can_delete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_name', 'is_approved', 'created_at', 'updated_at']

    def get_replies_count(self, obj):
        return obj.replies.filter(is_approved=True).count()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        
        if request.user.is_authenticated and obj.user == request.user:
            return True
        anon_session = request.session.get('anonymous_session_id')
        if anon_session and obj.anonymous_session_id == anon_session:
            return True
        
        return False

    def get_can_delete(self, obj):
        return self.get_can_edit(obj)

    def validate(self, data):
        if not data.get('comment', '').strip():
            raise serializers.ValidationError({'comment': 'Comment cannot be empty'})
        
        if 'parent' in data and data['parent']:
            parent = data['parent']
            anime = self.context.get('anime')
            episode = self.context.get('episode')
            
            if anime and parent.anime != anime:
                raise serializers.ValidationError({'parent': 'Parent comment must be for the same anime'})
            if episode and parent.episode != episode:
                raise serializers.ValidationError({'parent': 'Parent comment must be for the same episode'})
        
        return data


class CommentDetailSerializer(CommentSerializer):
    replies = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']

    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True).order_by('created_at')
        return CommentSerializer(replies, many=True, context=self.context).data
    

class FavoriteSerializer(serializers.ModelSerializer):
    anime = serializers.PrimaryKeyRelatedField(queryset=Anime.objects.filter(is_published=True))

    class Meta:
        model = Favorite
        fields = ['anime', 'added_at']
        read_only_fields = ['added_at']

    def validate_anime(self, value):
        if not value.is_published:
            raise serializers.ValidationError("Cannot favorite an unpublished anime.")
        return value

