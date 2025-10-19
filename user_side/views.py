# user_side/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import *
from .base_response import success_response, error_response
from .models import *
from rest_framework import generics, filters
from django.utils import timezone
from .filters import * 

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return success_response(
                data=UserSerializer(user).data,
                message="User registered successfully"
            )
        return error_response("Validation failed", serializer.errors)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)
            return success_response(
                data={
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data
                },
                message="Login successful"
            )
        return error_response("Invalid credentials", serializer.errors)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(
            message="Current user info",
            data=serializer.data
        )
    
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response(message="Refresh token required", errors=None, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  
        except TokenError as e:
            return error_response(message="Token invalid or already blacklisted", errors=str(e), status=400)

        return success_response(data=None, message="Successfully logged out (token blacklisted)")
    

class AnimeListView(generics.ListAPIView):
    queryset = Anime.objects.filter(is_published=True)
    serializer_class = AnimeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnimeFilter
    search_fields = ['title', 'english_title', 'uzbek_title', 'description', 'type', 'status', 'season']
    ordering_fields = ['release_year', 'total_views', 'rating', 'created_at']

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            session_token = request.headers.get('X-Session-Token')
            print(request.user.is_authenticated)
            print(session_token)
            if session_token:
                anon, created = AnonymousSession.objects.get_or_create(
                    session_token=session_token,
                    defaults={
                        'fingerprint_hash': request.headers.get('X-Fingerprint', ''),
                        'ip_address': self.get_client_ip(),
                        'country': request.headers.get('X-Country', 'UZ'),
                        'city': request.headers.get('X-City', ''),
                        'first_seen_at': timezone.now(),
                        'last_seen_at': timezone.now(),
                        'total_visits': 1
                    }
                )
                if not created:
                    anon.last_seen_at = timezone.now()
                    anon.total_visits += 1
                    anon.save()
        return super().list(request, *args, **kwargs)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
class AnimeDetailView(generics.RetrieveAPIView):
    queryset = Anime.objects.filter(is_published=True)
    serializer_class = AnimeSerializer
    lookup_field = 'pk' 

class EpisodeListView(generics.ListAPIView):
    serializer_class = EpisodeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = EpisodeFilter
    ordering_fields = ['episode_number', 'air_date', 'total_views']

    def get_queryset(self):
        anime_identifier = self.kwargs.get('anime_identifier')
        
        try:
            anime_id = int(anime_identifier)
            return Episode.objects.filter(
                anime_id=anime_id,
                anime__is_published=True,
                is_published=True
            ).order_by('episode_number')
        except ValueError:
            return Episode.objects.filter(
                anime__slug=anime_identifier,
                anime__is_published=True,
                is_published=True
            ).order_by('episode_number')


class EpisodeDetailView(generics.RetrieveAPIView):
    serializer_class = EpisodeDetailSerializer

    def get_object(self):
        anime_identifier = self.kwargs.get('anime_identifier')
        episode_identifier = self.kwargs.get('episode_identifier')

        try:
            anime_id = int(anime_identifier)
            anime_filter = {'anime_id': anime_id}
        except ValueError:
            anime_filter = {'anime__slug': anime_identifier}
        
        try:
            episode_id = int(episode_identifier)
            episode_filter = {'id': episode_id}
        except ValueError:
            episode_filter = {'slug': episode_identifier}

        queryset = Episode.objects.filter(
            **anime_filter,
            **episode_filter,
            anime__is_published=True,
            is_published=True
        )
        
        obj = queryset.first()
        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound("Episode not found")
        
        return obj
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.is_authenticated:
            user = request.user
            anon_session = None
        else:
            session_token = request.headers.get('X-Session-Token')
            if session_token:
                anon_session, _ = AnonymousSession.objects.get_or_create(
                    session_token=session_token,
                    defaults={
                        'fingerprint_hash': request.headers.get('X-Fingerprint', ''),
                        'ip_address': self.get_client_ip(),
                        'country': request.headers.get('X-Country', 'UZ'),
                        'city': request.headers.get('X-City', ''),
                        'first_seen_at': timezone.now(),
                        'last_seen_at': timezone.now(),
                        'total_visits': 1
                    }
                )
            else:
                anon_session = None
            user = None
        
        if user or anon_session:
            AnimeView.objects.create(
                user=user,
                anonymous_session=anon_session,
                anime=instance.anime,
                episode=instance,
                viewed_at=timezone.now(),
                ip_address=self.get_client_ip(),
                country=request.headers.get('X-Country', 'UZ')
            )
            
            instance.total_views += 1
            instance.save()
            instance.anime.total_views += 1
            instance.anime.save()
        
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Episode details")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    

class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class GenreDetailView(generics.RetrieveAPIView):
    serializer_class = GenreDetailSerializer
    lookup_field = 'slug'
    
    def get_object(self):
        identifier = self.kwargs.get('identifier')
        
        try:
            genre_id = int(identifier)
            return Genre.objects.get(id=genre_id)
        except (ValueError, Genre.DoesNotExist):
            try:
                return Genre.objects.get(slug=identifier)
            except Genre.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("Genre not found")


class GenreAnimeListView(generics.ListAPIView):
    serializer_class = AnimeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnimeFilter
    search_fields = ['title', 'english_title', 'uzbek_title', 'description']
    ordering_fields = ['release_year', 'total_views', 'rating', 'created_at']
    
    def get_queryset(self):
        identifier = self.kwargs.get('identifier')
        
        try:
            genre_id = int(identifier)
            genre_filter = {'genres__id': genre_id}
        except ValueError:
            genre_filter = {'genres__slug': identifier}
        
        return Anime.objects.filter(
            **genre_filter,
            is_published=True
        ).distinct().order_by('-created_at')