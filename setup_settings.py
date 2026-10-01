import os

settings_path = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil/Devil/settings.py'
with open(settings_path, 'r') as f:
    content = f.read()

apps_to_add = """
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'Devil.core',
    'Devil.accounts',
    'Devil.profiles',
    'Devil.discovery',
    'Devil.matching',
    'Devil.messaging',
    'Devil.moderation',
    'Devil.notifications',
    'Devil.dashboard',
"""

content = content.replace(
    "'django.contrib.staticfiles',",
    "'django.contrib.staticfiles',\n" + apps_to_add
)

auth_user_model = "\nAUTH_USER_MODEL = 'accounts.User'\n"
if "AUTH_USER_MODEL" not in content:
    content += auth_user_model

rest_framework_settings = """
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Devil API',
    'DESCRIPTION': 'Devil Application Backend API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
"""

if "REST_FRAMEWORK" not in content:
    content += rest_framework_settings

with open(settings_path, 'w') as f:
    f.write(content)

print("settings.py updated successfully.")
