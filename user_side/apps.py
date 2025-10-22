from django.apps import AppConfig
from django.template import engines

class UserSideConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_side'

    def ready(self):
        from user_side.templatetags import compat

        django_engine = engines['django']
        if compat.register not in django_engine.engine.template_builtins:
            django_engine.engine.template_builtins.append(compat.register)
