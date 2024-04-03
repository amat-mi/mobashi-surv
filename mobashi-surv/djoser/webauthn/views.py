import json
import secrets
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import (
    options_to_json,
    bytes_to_base64url,
    base64url_to_bytes,
)
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse,
)

from djoser import signals
from djoser.compat import get_user_email
from djoser.conf import settings
from djoser.utils import login_user

from .models import CredentialOptions
from .serializers import WebauthnLoginSerializer, WebauthnSignupSerializer


User = get_user_model()


class SingupRequestView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = WebauthnSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        co = serializer.save()

        registration_options = generate_registration_options(
            # challenge=co.challenge.encode(),
            rp_name=settings.WEBAUTHN["RP_NAME"],
            rp_id=settings.WEBAUTHN["RP_ID"],
            # user_id=co.ukey.encode(),
            user_id=secrets.token_bytes(32),
            user_name=co.username,
            user_display_name=co.display_name,
        )

        co.challenge = bytes_to_base64url(registration_options.challenge)
        co.ukey = bytes_to_base64url(registration_options.user.id)
        co.save()

        return Response(json.loads(options_to_json(registration_options)))


class SignupView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = settings.WEBAUTHN.SIGNUP_SERIALIZER

    def post(self, request, ukey):
        co = get_object_or_404(CredentialOptions, ukey=ukey)
        user_serializer = self.serializer_class(data=request.data)
        user_serializer.is_valid(raise_exception=True)

        try:
            registration_verification = verify_registration_response(
                # Supports the plain dict version of the WebAuthn response
                credential=request.data.get('attestationResponse', None),
                expected_challenge=base64url_to_bytes(co.challenge),
                expected_origin=settings.WEBAUTHN["ORIGIN"],
                expected_rp_id=settings.WEBAUTHN["RP_ID"],
                require_user_verification=True,
            )
        except InvalidRegistrationResponse:
            return Response(
                {api_settings.NON_FIELD_ERRORS_KEY: "WebAuthn verification failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = user_serializer.save()
        co.challenge = ""
        co.user = user
        co.sign_count = registration_verification.sign_count
        co.credential_id = bytes_to_base64url(
            registration_verification.credential_id)
        co.public_key = bytes_to_base64url(
            registration_verification.credential_public_key)
        co.save()
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        if settings.SEND_ACTIVATION_EMAIL:
            if not user.is_active:
                context = {"user": user}
                to = [get_user_email(user)]
                settings.EMAIL.activation(self.request, context).send(to)
        else:
            user.is_active = True
            user.save()

        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


class LoginRequestView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = WebauthnLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        co = CredentialOptions.objects.get(
            username=serializer.validated_data["username"]
        )

        authentication_options = generate_authentication_options(
            rp_id=settings.WEBAUTHN["RP_ID"],
            timeout=12000,
        )

        co.challenge = bytes_to_base64url(authentication_options.challenge)
        co.save()

        return Response(json.loads(options_to_json(authentication_options)))


class LoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = settings.WEBAUTHN.LOGIN_SERIALIZER

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        co = user.credential_options

        try:
            authentication_verification = verify_authentication_response(
                # Supports the plain dict version of the WebAuthn response
                credential=request.data.get('assertionResponse', None),
                expected_challenge=base64url_to_bytes(co.challenge),
                expected_origin=settings.WEBAUTHN["ORIGIN"],
                expected_rp_id=settings.WEBAUTHN["RP_ID"],
                credential_public_key=base64url_to_bytes(co.public_key),
                credential_current_sign_count=co.sign_count,
                require_user_verification=True,
            )
        except InvalidAuthenticationResponse:
            return Response(
                {api_settings.NON_FIELD_ERRORS_KEY: "WebAuthn verification failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        co.sign_count = authentication_verification.new_sign_count
        co.challenge = ""
        co.save()

        token_serializer_class = settings.SERIALIZERS.token
        token = login_user(request, user)
        return Response(
            token_serializer_class(token).data, status=status.HTTP_201_CREATED
        )
