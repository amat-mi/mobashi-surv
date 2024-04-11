from collections.abc import Iterable
from django.conf import settings
from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Q
from django.db import models
from uuid import uuid4
import rules
from rules.contrib.models import RulesModel
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class School(RulesModel):
    uuid = models.UUIDField(default=uuid4, null=False,
                            # let editable=True for debugging purposes, than set to False
                            blank=True, editable=True, unique=True)
    name = models.CharField(_('School'), max_length=100, unique=True,
                            help_text=_('Distinctive name of the school'))
    code = models.CharField(_('Code'), max_length=20, null=True, blank=True,
                            help_text=_('Code of the school'))
    address = models.CharField(_('Address'), max_length=300, null=True, blank=True,
                               help_text=_('Complete address of the school'))
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = _('School')
        verbose_name_plural = _('Schools')
        ordering = ['name']
        rules_permissions = {
            "add": rules.is_group_member('mosurv_admin'),
            "change": rules.is_group_member('mosurv_admin'),
            "delete": rules.is_group_member('mosurv_admin'),
            "view": rules.is_group_member('mosurv_admin')
        }

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding and not self.uuid:
            self.uuid = uuid4()
        super(School, self).save(*args, **kwargs)


class Campaign(RulesModel):
    class Status(models.IntegerChoices):
        DISABLED = -100, _('Disabled')
        ACTIVE = 0, _('Active')
        BEFORE = 50, _('Before')
        AFTER = 100, _('After')

    uuid = models.UUIDField(default=uuid4, null=False,
                            # let editable=True for debugging purposes, than set to False
                            blank=True, editable=True, unique=True)
    name = models.CharField(max_length=100, unique=True,
                            help_text='Distinctive name of the campaign')
    stamp_start = models.DateTimeField(null=True, blank=True,
                                       help_text='Instant when the campaign becomes active')
    stamp_end = models.DateTimeField(null=True, blank=True,
                                     help_text='Instant when the campaign stops to be active')
    schools = models.ManyToManyField(
        School, related_name='campaigns', blank=True,
        through='Cascho',
        help_text=_('Schools this campaign is about'))
    survey = models.JSONField(null=False, blank=True, default=dict)

    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-stamp_start', '-stamp_end']
        rules_permissions = {
            "add": rules.is_group_member('mosurv_admin'),
            "change": rules.is_group_member('mosurv_admin'),
            "delete": rules.is_group_member('mosurv_admin'),
            "view": rules.is_group_member('mosurv_admin'),
            "add_school": rules.is_group_member('mosurv_admin'),
            "remove_school": rules.is_group_member('mosurv_admin'),
        }

    def __str__(self):
        return _("%(name)s") % {
            "name": self.name
        }

    @property
    def status(self):
        if self.stamp_start and self.stamp_end:
            now = timezone.now()
            return self.Status.BEFORE if now < self.stamp_start \
                else self.Status.AFTER if now >= self.stamp_end \
                else self.Status.ACTIVE
        return self.Status.DISABLED

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def save(self, *args, **kwargs):
        if self._state.adding and not self.uuid:
            self.uuid = uuid4()
        super(Campaign, self).save(*args, **kwargs)

    def schools_abbrev(self):
        schools = self.schools.values_list("name", flat=True)
        return ', '.join([x[:15] for x in schools]) if schools else _('no school')


class Cascho(RulesModel):
    campaign = models.ForeignKey(
        Campaign, related_name='caschos', on_delete=models.CASCADE)
    school = models.ForeignKey(
        School, related_name='caschos', on_delete=models.CASCADE)

    class Meta:
        db_table = 'mosurv_campaign_schools'
        rules_permissions = {
            "add": rules.is_group_member('mosurv_admin'),
            "change": rules.is_group_member('mosurv_admin'),
            "delete": rules.is_group_member('mosurv_admin'),
            "view": rules.is_group_member('mosurv_admin')
        }


@rules.predicate
def is_survey_owner(user: settings.AUTH_USER_MODEL, obj: 'Survey') -> bool:
    if obj is None or not user.is_authenticated:
        return False
    return obj.user == user


class Survey(RulesModel):
    KIND_CHOICES = [
        ('forth', _('Forth')),
        ('back', _('Back')),
    ]

    class Status(models.IntegerChoices):
        CANCELLED = -100, _('Cancelled')
        EMPTY = 0, _('Empty')
        FILLED = 50, _('Filled')
        USED = 100, _('Used')

    kind = models.CharField(_('Kind'), max_length=50, choices=KIND_CHOICES,
                            null=False, blank=True, default='forth')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='surveys', null=False, blank=False,
        on_delete=models.CASCADE)
    campaign = models.ForeignKey(
        Campaign, related_name='surveys', null=False, blank=False,
        on_delete=models.CASCADE)
    school = models.ForeignKey(
        School, related_name='surveys', null=False, blank=False,
        on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.EMPTY)
    stamp = models.DateTimeField(null=True, blank=True, auto_now=True)
    content = models.JSONField(null=False, blank=True, default=dict)

    class Meta:
        verbose_name = _('Survey')
        verbose_name_plural = _('Surveys')
        unique_together = ['kind', 'user', 'campaign', 'school']
        ordering = ['status', 'campaign', 'school', 'kind']
        rules_permissions = {
            # "add": rules.is_group_member('mosurv_admin') | is_survey_owner,
            "add": rules.always_allow,
            "change": rules.is_group_member('mosurv_admin') | is_survey_owner,
            "delete": rules.is_group_member('mosurv_admin'),
            "view": rules.is_group_member('mosurv_admin') | is_survey_owner
        }

    def __str__(self):
        return _("%(kind)s %(user)s %(school)s in %(campaign)s") % {
            "kind": self.get_kind_display(),
            "user": self.user,
            "school": self.school,
            "campaign": self.campaign.name
        }

    def save(self, *args, **kwargs):
        # If "status" is USED or CANCELLED, "content" cannot be modified.
        # If "content" is empty, set "status" to EMPTY, otherwise to FILLED.
        if self.status in [self.Status.USED, self.Status.CANCELLED]:
            # if no field was specified to be updated (i.e. update all), use list of all fields.
            update_fields = kwargs.get('update_fields', None)
            if update_fields is None:
                update_fields = self._meta.get_fields()
            kwargs['update_fields'] = [
                f.name for f in update_fields if f.name != 'content' and not f.auto_created]
        else:
            self.status = self.Status.FILLED if self.content else self.Status.EMPTY
        return super().save(*args, **kwargs)

    @classmethod
    def by_user(cls, queryset: QuerySet[Any], user: settings.AUTH_USER_MODEL) -> QuerySet[Any]:
        if not user.is_authenticated:
            return queryset.model.objects.none()
        if rules.is_superuser(user) | rules.is_group_member('mosurv_admin')(user):
            return queryset
        return queryset.filter(user=user)
