from django.utils import timezone
from django.db.models import F
from .models import AnonymousSession
from rest_framework import generics
from .base_response import success_response, not_found_response


class AnonymousSessionTrackingMixin:
    def get_client_ip(self):
        request = self.request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def track_anonymous_session(self):
        request = self.request
        
        if request.user.is_authenticated:
            return None
        
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            return None
        
        anon_session, created = AnonymousSession.objects.get_or_create(
            session_token=session_token,
            defaults={
                'fingerprint_hash': request.headers.get('X-Fingerprint', ''),
                'ip_address': self.get_client_ip(),
                'country': request.headers.get('X-Country', 'UZ'),
                'city': request.headers.get('X-City', ''),
                'first_seen_at': timezone.now(),
                'last_seen_at': timezone.now(),
                'total_visits': 1,
            }
        )
        
        if not created:
            anon_session.total_visits = F('total_visits') + 1
            anon_session.last_seen_at = timezone.now()
            anon_session.save(update_fields=['total_visits', 'last_seen_at'])
            anon_session.refresh_from_db()
        
        return anon_session

    def get_user_or_session(self):
        if self.request.user.is_authenticated:
            return self.request.user, None
        return None, self.track_anonymous_session()
    


class PaginatedResponseMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if not queryset.exists():
            return not_found_response(message=f"No {self.serializer_class.Meta.model._meta.model_name}s found")
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return success_response(
                data=paginated_response.data.get('results'),
                message=f"{self.serializer_class.Meta.model._meta.model_name.capitalize()}s retrieved",
                meta={
                    "count": paginated_response.data.get('count'),
                    "next": paginated_response.data.get('next'),
                    "previous": paginated_response.data.get('previous')
                }
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message=f"{self.serializer_class.Meta.model._meta.model_name.capitalize()}s retrieved"
        )