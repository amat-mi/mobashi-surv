#!/bin/bash

python manage.py migrate --noinput \
    && python manage.py collectstatic --noinput \
    && exec python manage.py createsuperuser