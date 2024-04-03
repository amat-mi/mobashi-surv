# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

import os
from django.conf import settings

with open(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       os.getenv('DJANGO_DATABASE_PASSWORD_FILE')))) as f:
    DJANGO_DATABASE_PASSWORD = f.read().strip()

DATABASES = {
    "default": {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DJANGO_DATABASE_NAME'),
        'USER': os.getenv('DJANGO_DATABASE_USER'),
        'PASSWORD': DJANGO_DATABASE_PASSWORD,
        'HOST': 'db',  # use service name from docker-compose.yml
        'PORT': '5432',  # MUST use the "internal" service port, not the published one!!!
    }
}

settings.DJOSER['WEBAUTHN'] = {
    'RP_NAME': "Mobashi SURV",
    'RP_ID': 'localhost',
    'ORIGIN': [
        "http://localhost:4102",
        "https://localhost:4102",
    ]
}
