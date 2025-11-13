from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from .base_response import (
    success_response, 
    error_response, 
    created_response,
    not_found_response,
    unauthorized_response,
    validation_error_response
)
from .models import *
from .mixins import AnonymousSessionTrackingMixin
from rest_framework import generics, filters
from django.utils import timezone
from .filters import * 
from django.db.models import F
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
import logging
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)  
            
            return created_response(
                data={
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data
                },
                message="User registered successfully"
            )
        return validation_error_response(
            errors=serializer.errors,
            message="Validation failed"
        )


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
        return unauthorized_response(message="Invalid credentials")


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Current user info"
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,  
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return success_response(
                data=serializer.data,
                message="Profile updated successfully"
            )
        return error_response(
            message="Failed to update profile",
            errors=serializer.errors,
            status=400
        )

class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return validation_error_response(
                errors={"refresh": ["Refresh token is required"]},
                message="Validation failed"
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(
                message="Successfully logged out"
            )
        except TokenError:
            return error_response(
                message="Invalid or expired token"
            )
    

class AnimeListView(AnonymousSessionTrackingMixin, generics.ListAPIView):
    queryset = Anime.objects.filter(is_published=True)
    serializer_class = AnimeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnimeFilter
    search_fields = ['title', 'english_title', 'russian_title', 'uzbek_title', 'description', 'type', 'status', 'season']
    ordering_fields = ['release_year', 'total_views', 'rating', 'created_at']

    def list(self, request, *args, **kwargs):
        self.track_anonymous_session()

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data.get('results'),
                message="Anime list retrieved",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous')
                }
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Anime list retrieved"
        )
    

class AnimeDetailView(generics.RetrieveAPIView):
    queryset = Anime.objects.filter(is_published=True)
    serializer_class = AnimeSerializer
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(
                data=serializer.data,
                message="Anime details retrieved"
            )
        except Anime.DoesNotExist:
            return not_found_response(message="Anime not found")


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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if not queryset.exists():
            return not_found_response(message="No episodes found for this anime")
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data.get('results'),
                message="Episodes retrieved",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous')
                }
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Episodes retrieved"
        )

class EpisodeDetailView(AnonymousSessionTrackingMixin, generics.RetrieveAPIView):
    serializer_class = EpisodeDetailSerializer

    def get_object(self):
        anime_identifier = self.kwargs.get('anime_identifier')
        episode_identifier = self.kwargs.get('episode_identifier')

        anime_filter = (
            {'anime__id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'anime__slug__iexact': anime_identifier}
        )
        episode_filter = (
            {'id': int(episode_identifier)}
            if episode_identifier.isdigit()
            else {'slug__iexact': episode_identifier}
        )

        try:
            obj = Episode.objects.filter(
                **anime_filter,
                **episode_filter,
                anime__is_published=True,
                is_published=True
            ).first()
            if not obj:
                raise NotFound("Episode not found")
            return obj
        except Exception as e:
            logger.error(f"Error retrieving episode: {str(e)}")
            raise NotFound("Episode not found")

    def check_premium_access(self, user, episode):
        if not episode.is_premium_only and not episode.anime.is_premium_only:
            return True
        
        if not user:
            return False
        
        if not user.is_premium:
            return False

        if user.premium_expires_at and user.premium_expires_at < timezone.now():
            return False
        
        return True

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user, anon_session = self.get_user_or_session()

            if not self.check_premium_access(user, instance):
                return error_response(
                    message="This episode requires a premium subscription. Please upgrade to premium to watch this content.",
                    status=status.HTTP_403_FORBIDDEN,
                    errors={
                        'is_premium_only': True,
                        'anime_premium': instance.anime.is_premium_only,
                        'episode_premium': instance.is_premium_only
                    }
                )

            view_exists = False
            if user:
                view_exists = WatchHistory.objects.filter(
                    user=user,
                    anime=instance.anime,
                    episode=instance
                ).exists()
            elif anon_session:
                view_exists = WatchHistory.objects.filter(
                    anonymous_session=anon_session,
                    anime=instance.anime,
                    episode=instance
                ).exists()

            if not view_exists:
                Episode.objects.filter(pk=instance.pk).update(total_views=F('total_views') + 1)
                Anime.objects.filter(pk=instance.anime.pk).update(total_views=F('total_views') + 1)

                watch_history_data = {
                    'anime': instance.anime,
                    'episode': instance,
                    'watched_at': timezone.now(),
                    'ip_address': self.get_client_ip(),
                    'device_type': request.headers.get('User-Agent', 'unknown'),
                    'country': request.headers.get('X-Country', 'UZ')
                }
                if user:
                    watch_history_data['user'] = user
                elif anon_session:
                    watch_history_data['anonymous_session'] = anon_session

                try:
                    WatchHistory.objects.create(**watch_history_data)
                except Exception as e:
                    logger.warning(f"Failed to create watch history: {str(e)}")

            serializer = self.get_serializer(instance, context={'request': request})
            logger.debug(f"Serialized episode: {instance}")
            return success_response(
                data=serializer.data,
                message="Episode details retrieved"
            )
        except NotFound:
            return not_found_response(message="Episode not found")
        except Exception as e:
            logger.error(f"Error in get method: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to retrieve episode details",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
               
class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_ru', 'description']
    ordering_fields = ['name', 'name_ru', 'created_at']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data.get('results'),
                message="Genres retrieved",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous')
                }
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Genres retrieved"
        )


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
                raise NotFound("Genre not found")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(
                data=serializer.data,
                message="Genre details retrieved"
            )
        except NotFound:
            return not_found_response(message="Genre not found")


class GenreAnimeListView(generics.ListAPIView):
    serializer_class = AnimeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnimeFilter
    search_fields = ['title', 'english_title', 'russian_title', 'uzbek_title', 'description']
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if not queryset.exists():
            return not_found_response(message="No anime found for this genre")
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data.get('results'),
                message="Anime list retrieved",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous')
                }
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Anime list retrieved"
        )
class EpisodeWatchView(AnonymousSessionTrackingMixin, APIView):
    def post(self, request, anime_identifier, episode_identifier):
        anime_filter = (
            {'id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'slug__iexact': anime_identifier}
        )
        try:
            anime = Anime.objects.get(**anime_filter, is_published=True)
        except Anime.DoesNotExist:
            return not_found_response(message="Anime not found")
        except Exception as e:
            logger.error(f"Error finding anime: {str(e)}", exc_info=True)
            return error_response(message="An error occurred while finding anime", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        episode_filter = (
            {'id': int(episode_identifier)}
            if episode_identifier.isdigit()
            else {'slug__iexact': episode_identifier}
        )
        try:
            episode = Episode.objects.get(
                anime=anime,
                **episode_filter,
                is_published=True
            )
        except Episode.DoesNotExist:
            return not_found_response(message="Episode not found")
        except Exception as e:
            logger.error(f"Error finding episode: {str(e)}", exc_info=True)
            return error_response(message="An error occurred while finding episode", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = WatchHistorySerializer(data=request.data, context={'episode': episode})
        if not serializer.is_valid():
            return validation_error_response(
                errors=serializer.errors,
                message="Invalid watch history data"
            )

        user, anon_session = self.get_user_or_session()

        lookup_filter = {
            'anime': anime,
            'episode': episode
        }
        
        if user:
            lookup_filter['user'] = user
            lookup_filter['anonymous_session__isnull'] = True
        elif anon_session:
            lookup_filter['anonymous_session'] = anon_session
            lookup_filter['user__isnull'] = True
        else:
            return error_response(
                message="Unable to track watch history without user or session",
                status=status.HTTP_400_BAD_REQUEST
            )

        view_exists = WatchHistory.objects.filter(**lookup_filter).exists()

        if not view_exists:
            Episode.objects.filter(pk=episode.pk).update(total_views=F('total_views') + 1)
            Anime.objects.filter(pk=anime.pk).update(total_views=F('total_views') + 1)

        watch_history_data = {
            'anime': anime,
            'episode': episode,
            'watched_at': timezone.now(),
            'ip_address': self.get_client_ip(),
            'device_type': request.headers.get('User-Agent', 'unknown'),
            'country': serializer.validated_data.get('country', request.headers.get('X-Country', 'UZ'))
        }
        
        if user:
            watch_history_data['user'] = user
        elif anon_session:
            watch_history_data['anonymous_session'] = anon_session
            
        if 'watch_duration_seconds' in serializer.validated_data:
            watch_history_data['watch_duration_seconds'] = serializer.validated_data['watch_duration_seconds']
        if 'completed' in serializer.validated_data:
            watch_history_data['completed'] = serializer.validated_data['completed']

        try:
            watch_history, created = WatchHistory.objects.update_or_create(
                **lookup_filter,
                defaults=watch_history_data
            )
            
            return success_response(
                message="Watch history recorded successfully",
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Failed to record watch history: {str(e)}", exc_info=True)
            return error_response(
                message=f"Failed to record watch history: {str(e)}",  
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LikeToggleView(AnonymousSessionTrackingMixin, APIView):
    
    def post(self, request, anime_identifier=None, episode_identifier=None):
        if not anime_identifier:
            return error_response(message="Anime identifier is required", status=status.HTTP_400_BAD_REQUEST)
        
        anime_filter = (
            {'id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'slug__iexact': anime_identifier}
        )
        
        try:
            anime = Anime.objects.get(**anime_filter, is_published=True)
        except Anime.DoesNotExist:
            return not_found_response(message="Anime not found")
        except Exception as e:
            logger.error(f"Error finding anime: {str(e)}", exc_info=True)
            return error_response(message="An error occurred while finding anime", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        episode = None
        if episode_identifier:
            episode_filter = (
                {'id': int(episode_identifier)}
                if episode_identifier.isdigit()
                else {'slug__iexact': episode_identifier}
            )
            
            try:
                episode = Episode.objects.get(
                    anime=anime,
                    **episode_filter,
                    is_published=True
                )
            except Episode.DoesNotExist:
                return not_found_response(message="Episode not found")
            except Exception as e:
                logger.error(f"Error finding episode: {str(e)}", exc_info=True)
                return error_response(message="An error occurred while finding episode", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = LikeSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(errors=serializer.errors, message="Invalid like data")
        
        is_like = serializer.validated_data.get('is_like', True)
        user, anon_session = self.get_user_or_session()
        
        if not user and not anon_session:
            return error_response(message="Unable to process like without user or session", status=status.HTTP_400_BAD_REQUEST)
        
        lookup_filter = {}
        if episode:
            lookup_filter['episode'] = episode
            lookup_filter['anime__isnull'] = True
        else:
            lookup_filter['anime'] = anime
            lookup_filter['episode__isnull'] = True
        
        if user:
            lookup_filter['user'] = user
            lookup_filter['anonymous_session__isnull'] = True
        elif anon_session:
            lookup_filter['anonymous_session'] = anon_session
            lookup_filter['user__isnull'] = True
        
        try:
            existing_like = Like.objects.filter(**lookup_filter).first()
            
            if existing_like:
                if existing_like.is_like == is_like:
                    existing_like.delete()
                    
                    if episode:
                        if is_like:
                            Episode.objects.filter(pk=episode.pk).update(total_likes=F('total_likes') - 1)
                        else:
                            Episode.objects.filter(pk=episode.pk).update(total_dislikes=F('total_dislikes') - 1)
                    else:
                        if is_like:
                            Anime.objects.filter(pk=anime.pk).update(total_likes=F('total_likes') - 1)
                        else:
                            Anime.objects.filter(pk=anime.pk).update(total_dislikes=F('total_dislikes') - 1)
                    
                    return success_response(
                        data={'action': 'removed', 'is_like': None},
                        message="Like removed successfully"
                    )
                else:
                    old_is_like = existing_like.is_like
                    existing_like.is_like = is_like
                    existing_like.save()
                    
                    if episode:
                        if old_is_like:
                            Episode.objects.filter(pk=episode.pk).update(
                                total_likes=F('total_likes') - 1,
                                total_dislikes=F('total_dislikes') + 1
                            )
                        else:
                            Episode.objects.filter(pk=episode.pk).update(
                                total_likes=F('total_likes') + 1,
                                total_dislikes=F('total_dislikes') - 1
                            )
                    else:
                        if old_is_like:
                            Anime.objects.filter(pk=anime.pk).update(
                                total_likes=F('total_likes') - 1,
                                total_dislikes=F('total_dislikes') + 1
                            )
                        else:
                            Anime.objects.filter(pk=anime.pk).update(
                                total_likes=F('total_likes') + 1,
                                total_dislikes=F('total_dislikes') - 1
                            )
                    
                    return success_response(
                        data={'action': 'updated', 'is_like': is_like},
                        message="Like updated successfully"
                    )
            else:
                like_data = {
                    'is_like': is_like,
                }
                
                if episode:
                    like_data['episode'] = episode
                else:
                    like_data['anime'] = anime
                
                if user:
                    like_data['user'] = user
                elif anon_session:
                    like_data['anonymous_session'] = anon_session
                
                Like.objects.create(**like_data)
                
                if episode:
                    if is_like:
                        Episode.objects.filter(pk=episode.pk).update(total_likes=F('total_likes') + 1)
                    else:
                        Episode.objects.filter(pk=episode.pk).update(total_dislikes=F('total_dislikes') + 1)
                else:
                    if is_like:
                        Anime.objects.filter(pk=anime.pk).update(total_likes=F('total_likes') + 1)
                    else:
                        Anime.objects.filter(pk=anime.pk).update(total_dislikes=F('total_dislikes') + 1)
                
                return success_response(
                    data={'action': 'created', 'is_like': is_like},
                    message="Like added successfully",
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"Failed to process like: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to process like",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommentListCreateView(AnonymousSessionTrackingMixin, generics.ListAPIView):
    serializer_class = CommentDetailSerializer
    
    def get_queryset(self):
        anime_identifier = self.kwargs.get('anime_identifier')
        episode_identifier = self.kwargs.get('episode_identifier')

        queryset = Comment.objects.filter(
            is_approved=True,
            parent__isnull=True  
        ).select_related('user', 'anonymous_session')
        if episode_identifier:
            episode_filter = (
                {'episode__id': int(episode_identifier)}
                if episode_identifier.isdigit()
                else {'episode__slug__iexact': episode_identifier}
            )
            queryset = queryset.filter(**episode_filter)
        elif anime_identifier:
            anime_filter = (
                {'anime__id': int(anime_identifier)}
                if anime_identifier.isdigit()
                else {'anime__slug__iexact': anime_identifier}
            )
            queryset = queryset.filter(**anime_filter, episode__isnull=True)
        
        return queryset.order_by('-created_at')
    
    def post(self, request, anime_identifier=None, episode_identifier=None):
        if not anime_identifier:
            return error_response(message="Anime identifier is required", status=status.HTTP_400_BAD_REQUEST)
        
        anime_filter = (
            {'id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'slug__iexact': anime_identifier}
        )
        
        try:
            anime = Anime.objects.get(**anime_filter, is_published=True)
        except Anime.DoesNotExist:
            return not_found_response(message="Anime not found")
        except Exception as e:
            logger.error(f"Error finding anime: {str(e)}", exc_info=True)
            return error_response(message="An error occurred while finding anime", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        episode = None
        if episode_identifier:
            episode_filter = (
                {'id': int(episode_identifier)}
                if episode_identifier.isdigit()
                else {'slug__iexact': episode_identifier}
            )
            
            try:
                episode = Episode.objects.get(
                    anime=anime,
                    **episode_filter,
                    is_published=True
                )
            except Episode.DoesNotExist:
                return not_found_response(message="Episode not found")
            except Exception as e:
                logger.error(f"Error finding episode: {str(e)}", exc_info=True)
                return error_response(message="An error occurred while finding episode", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = CommentSerializer(
            data=request.data,
            context={'request': request, 'anime': anime, 'episode': episode}
        )
        
        if not serializer.is_valid():
            return validation_error_response(errors=serializer.errors, message="Invalid comment data")
        
        user, anon_session = self.get_user_or_session()
        
        comment_data = {
            'comment': serializer.validated_data['comment'],
            'parent': serializer.validated_data.get('parent'),
        }
        
        if episode:
            comment_data['episode'] = episode
        else:
            comment_data['anime'] = anime
        
        if user:
            comment_data['user'] = user
            comment_data['is_approved'] = True  #
        elif anon_session:
            comment_data['anonymous_session'] = anon_session
            comment_data['guest_name'] = serializer.validated_data.get('guest_name', 'Anonymous')
            comment_data['is_approved'] = False  
        else:
            return error_response(message="Unable to post comment without user or session", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            comment = Comment.objects.create(**comment_data)
        
            if episode:
                Episode.objects.filter(pk=episode.pk).update(total_comments=F('total_comments') + 1)
            else:
                Anime.objects.filter(pk=anime.pk).update(total_comments=F('total_comments') + 1)
            
            response_serializer = CommentSerializer(comment, context={'request': request})
            
            return success_response(
                data=response_serializer.data,
                message="Comment posted successfully" if comment.is_approved else "Comment submitted for approval",
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Failed to create comment: {str(e)}", exc_info=True)
            return error_response(
            message="Failed to post comment",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class CommentDetailView(AnonymousSessionTrackingMixin, APIView):

    def get_comment(self, comment_id):
        try:
            return Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return None
    
    def check_permission(self, comment, request):
        user, anon_session = self.get_user_or_session()
        
        if user and comment.user == user:
            return True
        
        if anon_session and comment.anonymous_session == anon_session:
            return True
        
        return False
    
    def put(self, request, comment_id):
        comment = self.get_comment(comment_id)
        
        if not comment:
            return not_found_response(message="Comment not found")
        
        if not self.check_permission(comment, request):
            return error_response(message="You don't have permission to edit this comment", status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentSerializer(
            comment,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return validation_error_response(errors=serializer.errors, message="Invalid comment data")
        
        try:
            serializer.save(updated_at=timezone.now())
            return success_response(data=serializer.data, message="Comment updated successfully")
        except Exception as e:
            logger.error(f"Failed to update comment: {str(e)}", exc_info=True)
            return error_response(message="Failed to update comment", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, comment_id):
        comment = self.get_comment(comment_id)
        
        if not comment:
            return not_found_response(message="Comment not found")
        
        if not self.check_permission(comment, request):
            return error_response(message="You don't have permission to delete this comment", status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Update comment count
            if comment.episode:
                Episode.objects.filter(pk=comment.episode.pk).update(total_comments=F('total_comments') - 1)
            elif comment.anime:
                Anime.objects.filter(pk=comment.anime.pk).update(total_comments=F('total_comments') - 1)
            
            comment.delete()
            return success_response(message="Comment deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete comment: {str(e)}", exc_info=True)
            return error_response(message="Failed to delete comment", status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FavoriteView(AnonymousSessionTrackingMixin, APIView):
    def post(self, request, anime_identifier):
        logger.debug(f"Received POST request to add favorite for anime_identifier: {anime_identifier}")

        # Identify anime
        anime_filter = (
            {'id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'slug__iexact': anime_identifier}
        )
        try:
            anime = Anime.objects.get(**anime_filter, is_published=True)
            logger.debug(f"Found anime: {anime}")
        except Anime.DoesNotExist:
            logger.error(f"Anime not found for filter: {anime_filter}")
            return not_found_response(message="Anime not found")
        except Exception as e:
            logger.error(f"Unexpected error finding anime: {str(e)}")
            return error_response(message="An error occurred while finding anime", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user, anon_session = self.get_user_or_session()
        logger.debug(f"User: {user}, Anonymous session: {anon_session}")

        if not user and not anon_session:
            logger.error("Both user and anonymous_session are None, cannot create Favorite")
            return error_response(
                message="Cannot add favorite: no user or session provided",
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if favorite exists
        favorite_exists = False
        if user:
            favorite_exists = Favorite.objects.filter(
                user=user,
                anime=anime
            ).exists()
        elif anon_session:
            favorite_exists = Favorite.objects.filter(
                anonymous_session=anon_session,
                anime=anime
            ).exists()
        logger.debug(f"Favorite exists: {favorite_exists}")

        if favorite_exists:
            logger.debug(f"Anime {anime} already favorited by user or session")
            return success_response(
                message="Anime already in favorites",
                status=status.HTTP_200_OK
            )

        favorite_data = {
            'anime': anime,
            'added_at': timezone.now()
        }
        if user:
            favorite_data['user'] = user
            favorite_data['anonymous_session'] = None
        elif anon_session:
            favorite_data['anonymous_session'] = anon_session
            favorite_data['user'] = None

        try:
            favorite = Favorite.objects.create(**favorite_data)
            Anime.objects.filter(pk=anime.pk).update(total_favorites=F('total_favorites') + 1)
            logger.debug(f"Created Favorite record: {favorite}, incremented total_favorites")
            return success_response(
                message="Anime added to favorites",
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating Favorite record: {str(e)}")
            return error_response(
                message=f"Failed to add favorite: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, anime_identifier):
        logger.debug(f"Received DELETE request to remove favorite for anime_identifier: {anime_identifier}")

        anime_filter = (
            {'id': int(anime_identifier)}
            if anime_identifier.isdigit()
            else {'slug__iexact': anime_identifier}
        )
        try:
            anime = Anime.objects.get(**anime_filter, is_published=True)
            logger.debug(f"Found anime: {anime}")
        except Anime.DoesNotExist:
            logger.error(f"Anime not found for filter: {anime_filter}")
            return not_found_response(message="Anime not found")
        except Exception as e:
            logger.error(f"Unexpected error finding anime: {str(e)}")
            return error_response(message="An error occurred while finding anime", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user, anon_session = self.get_user_or_session()
        logger.debug(f"User: {user}, Anonymous session: {anon_session}")

        if not user and not anon_session:
            logger.error("Both user and anonymous_session are None, cannot remove Favorite")
            return error_response(
                message="Cannot remove favorite: no user or session provided",
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite = None
        if user:
            favorite = Favorite.objects.filter(
                user=user,
                anime=anime
            ).first()
        elif anon_session:
            favorite = Favorite.objects.filter(
                anonymous_session=anon_session,
                anime=anime
            ).first()

        if not favorite:
            logger.debug(f"No favorite found for anime {anime}")
            return not_found_response(message="Anime not in favorites")

        try:
            favorite.delete()
            Anime.objects.filter(pk=anime.pk).update(total_favorites=F('total_favorites') - 1)
            logger.debug(f"Deleted Favorite record for anime {anime}, decremented total_favorites")
            return success_response(
                message="Anime removed from favorites",
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting Favorite record: {str(e)}")
            return error_response(
                message=f"Failed to remove favorite: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FavoriteListView(AnonymousSessionTrackingMixin, generics.ListAPIView):
    serializer_class = AnimeSerializer

    def get_queryset(self):
        user, anon_session = self.get_user_or_session()
        logger.debug(f"User: {user}, Anonymous session: {anon_session}")

        if user:
            return Favorite.objects.filter(user=user).select_related('anime').order_by('-added_at')
        elif anon_session:
            return Favorite.objects.filter(anonymous_session=anon_session).select_related('anime').order_by('-added_at')
        logger.error("Both user and anonymous_session are None, returning empty queryset")
        return Favorite.objects.none()

    def list(self, request, *args, **kwargs):
        logger.debug("Received GET request for FavoriteListView")
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset.exists():
                logger.debug("No favorites found")
                return not_found_response(message="No favorite anime found")

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer([favorite.anime for favorite in page], many=True, context={'request': request})
                paginated_response = self.get_paginated_response(serializer.data)
                return success_response(
                    data=paginated_response.data.get('results'),
                    message="Favorite anime retrieved",
                    meta={
                        "count": paginated_response.data.get('count'),
                        "next": paginated_response.data.get('next'),
                        "previous": paginated_response.data.get('previous')
                    }
                )

            serializer = self.get_serializer([favorite.anime for favorite in queryset], many=True, context={'request': request})
            return success_response(
                data=serializer.data,
                message="Favorite anime retrieved"
            )
        except Exception as e:
            logger.error(f"Error retrieving favorite anime: {str(e)}")
            return error_response(
                message="Failed to retrieve favorite anime",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class DonationListView(generics.ListAPIView):
    serializer_class = DonationSerializer
    queryset = Donation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['amount', 'created_at']

    def list(self, request, *args, **kwargs):
        # Aggregate top donors
        top_donors_qs = Donation.top_donors(limit=3)
        top_serialized = DonationTopSerializer(top_donors_qs, many=True).data

        # Other donors (not aggregated for now)
        remaining_donors_qs = self.get_queryset()[3:]
        page = self.paginate_queryset(remaining_donors_qs)

        if page is not None:
            serializer_page = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer_page.data)

            return success_response(
                data={
                    "top_donors": top_serialized,
                    "other_donors": paginated_response.data.get('results')
                },
                message="Donations retrieved successfully",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous'),
                }
            )

        # If no pagination
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(
            data={"top_donors": top_serialized, "other_donors": serializer.data},
            message="Donations retrieved successfully"
        )


