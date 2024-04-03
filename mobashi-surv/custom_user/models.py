from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from pgcrypto import fields


class User(AbstractUser):
    # Replace fields with encrypted versions
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = fields.CharPGPPublicKeyField(
        _("first name"), max_length=150, blank=True)
    last_name = fields.CharPGPPublicKeyField(
        _("last name"), max_length=150, blank=True)
    email = fields.EmailPGPPublicKeyField(_("email address"), blank=True)
