# Django Rest Framework view
import base64
from uuid import uuid4
from urllib.parse import unquote_plus
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseServerError, HttpResponseBadRequest, Http404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.conf import settings
from .models import Campaign, School, Cascho, Survey
from .serializers import CampaignSerializer, SchoolSerializer, CaschoSerializer, \
    SurveyStatusSerializer, SurveyContentSerializer, SurveySerializer, HarvestSerializer, TripSerializer
from rules.contrib.rest_framework import AutoPermissionViewSetMixin


class SchoolViewSet(AutoPermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'  # instances are modified by the MAIN server

    def get_queryset(self):
        return School.objects.all()


class SpecialAutoPermissionViewSetMixin(AutoPermissionViewSetMixin):
    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        "add_school": "add_school",
        "remove_school": "remove_school"
    }


class CampaignViewSet(SpecialAutoPermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'  # instances are modified by the MAIN server

    def get_queryset(self):
        return Campaign.objects.exclude(stamp_start__isnull=True).exclude(stamp_end__isnull=True)

    def _get_objs(self, request, uuid=None):
        school_uuid = request.data.get('school_uuid', '')
        if not school_uuid:
            raise Http404
        campaign = super().get_object()
        try:
            school = get_object_or_404(School, uuid=school_uuid)
            return (campaign, school)
        except:
            raise Http404

    @action(detail=True, methods=['patch'])
    def add_school(self, request, uuid=None):
        campaign, school = self._get_objs(request, uuid)
        cascho, created = Cascho.objects.get_or_create(
            campaign=campaign, school=school)
        serializer = CaschoSerializer(cascho, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def remove_school(self, request, uuid=None):
        campaign, school = self._get_objs(request, uuid)
        cascho = get_object_or_404(Cascho, campaign=campaign, school=school)
        cascho.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaschoViewSet(AutoPermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = CaschoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cascho.objects.all()


class SurveyViewSet(AutoPermissionViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SurveySerializer
    # create() MUST be accessible by anonymous
    # and other methods are already protected by get_queryset(), that filters by user
    permission_classes = []

    def get_queryset(self):
        # will return [] if user not authenticated
        return Survey.by_user(Survey.objects.all(), self.request.user)

    def get_content_serializer(self, *args, **kwargs):
        # Copied and modified from UpdateModelMixin
        # to use a serializer that only saves the "content" field
        serializer_class = SurveyContentSerializer
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Copied and modified from UpdateModelMixin
        instance = self.get_object()  # will raise 404, if get_queryset() returns []
        # use specific serializer for saving only the content field
        serializer = self.get_content_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # pass the updated instance to the standard serializer (to send back all fields)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_data(self, request, name):
        encoded = request.data.get(name, '')
        try:
            # base64url decode
            padding = '=' * (4 - (len(encoded) % 4))
            res = base64.urlsafe_b64decode(encoded + padding).decode()
        except Exception as e:
            try:
                res = unquote_plus(encoded)
            except Exception as e:
                return None
        return res

    # Can create Surveys only by sending code from Client
    def create(self, request, *args, **kwargs):
        try:
            code = self.get_data(request, 'code')
            error = 'Invalid code'
            while True:
                if not code:
                    break

                parts = code.split('@')
                if len(parts) != 2:
                    break

                campaign = get_object_or_404(Campaign, uuid=parts[0])
                school = get_object_or_404(School, uuid=parts[1])

                if not school in campaign.schools.all():
                    break

                # if user is authenticated, its "username" must coincide with the one specified and it must have a token
                # if it's not authenticated and a username is specified, get the corresponding user, that must exists and have a token
                # if a username is not specified, create a new user and corresponding token
                # in any case do not let an admin or inactive User in
                username = self.get_data(request, 'username')
                user = request.user
                token = None
                if user.is_authenticated:
                    if user.username != username:
                        raise PermissionDenied
                    token = get_object_or_404(settings.TOKEN_MODEL, user=user)
                else:
                    User = get_user_model()
                    if username:
                        user = get_object_or_404(User, username=username)
                        token = get_object_or_404(
                            settings.TOKEN_MODEL, user=user)
                    else:
                        username = uuid4()
                        user = User.objects.create_user(username)
                        token = settings.TOKEN_MODEL.objects.create(user=user)

                if user.is_staff or user.is_superuser or not user.is_active:
                    raise PermissionDenied

                forth, forth_created = Survey.objects.get_or_create(
                    kind='forth', user=user, campaign=campaign, school=school)
                back, back_created = Survey.objects.get_or_create(
                    kind='back', user=user, campaign=campaign, school=school)

                context = self.get_serializer_context()
                serializer_class = self.get_serializer_class()
                serializer = serializer_class(
                    [forth, back], many=True, context=context)
                data = {
                    'surveys': serializer.data,
                    'token': token.key if token else None
                }
                return Response(data)

            if error:
                raise ValueError(f'{error}')
        except PermissionDenied:
            raise  # do NOT trap this
        except Exception as exc:
            return Response({
                'error': 'GENERIC_ERROR',
                'message': '{}'.format(str(exc)).encode("utf-8")
            }, status=HttpResponseServerError.status_code)


class HarvestViewSet(AutoPermissionViewSetMixin, viewsets.ModelViewSet):
    # serializer_class = HarvestSerializer
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        res = Survey.by_user(Survey.objects.all(), self.request.user)
        return res.filter(status=Survey.Status.FILLED)

    def get_status_serializer(self, *args, **kwargs):
        # Copied and modified from UpdateModelMixin
        # to use a serializer that only saves the "status" field
        serializer_class = SurveyStatusSerializer
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Copied and modified from UpdateModelMixin
        instance = self.get_object()  # will raise 404, if get_queryset() returns []
        # use specific serializer for saving only the status field
        serializer = self.get_status_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # pass the updated instance to the standard serializer (to send back all fields)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
