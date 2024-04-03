# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

import os
from django.conf import settings

with open(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       os.getenv('PUBLIC_PGP_KEY_PATH', '../django_secrets/public.key')))) as f:
    PUBLIC_PGP_KEY = f.read().strip()

with open(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       os.getenv('PRIVATE_PGP_KEY_PATH', '../django_secrets/private.key')))) as f:
    PRIVATE_PGP_KEY = f.read().strip()

with open(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       os.getenv('DJANGO_DATABASE_PASSWORD_FILE', '../django_secrets/password.txt')))) as f:
    DJANGO_DATABASE_PASSWORD = f.read().strip()

DATABASES = {
    "default": {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DJANGO_DATABASE_NAME'),
        'USER': os.getenv('DJANGO_DATABASE_USER'),
        'PASSWORD': DJANGO_DATABASE_PASSWORD,
        'HOST': os.getenv('DJANGO_DATABASE_HOST'),
        'PORT': os.getenv('DJANGO_DATABASE_PORT'),
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
