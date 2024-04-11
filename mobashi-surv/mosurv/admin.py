# Django Admin
from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from rules.contrib.admin import ObjectPermissionsModelAdmin
from .models import Campaign, School, Survey


#################################################
# Copied from: https://bitbucket.org/caipirginka/django-oicom/src/master/oidjutils/utils.py
# Added support for "want_no_link"
def field_link(obj, field=None, target=None, textfield=None, want_no_link=False):
    if obj.pk:
        if field:  # if requested
            # build link for an object pointed to the specified field, instead
            obj = getattr(obj, field)
        link = reverse(
            'admin:' + '_'.join([obj._meta.app_label, obj._meta.model_name, 'change']), args=(obj.pk,)
        )
        target = f' target="{target}"' if target else ''
        text = getattr(obj, textfield, 'Modifica')
        if callable(text):
            text = text()
        return text if want_no_link else f'<a href="{link}"{target}>{text}</a>'
    return ''
#################################################


class BaseAdmin(ObjectPermissionsModelAdmin):
    save_on_top = True


class CampaignInline(admin.TabularInline):
    model = Campaign.schools.through
    extra = 1


class SchoolAdmin(BaseAdmin):
    inlines = [CampaignInline]
    list_display = ("name", "uuid", "code", "address")
    search_fields = ("name", "uuid", "code", "address")


admin.site.register(School, SchoolAdmin)


class CampaignAdmin(BaseAdmin):
    def school_links(self, obj):
        if not obj or not obj.pk:
            return None
        res = []
        for school in obj.schools.all():
            res.append(field_link(
                school, target='_blank', textfield='__str__'))
        return mark_safe(u'<br />'.join(res))
    school_links.short_description = _('Schools')

    def get_status(self, obj):
        return obj and obj.status

    list_display = ("__str__", "uuid", "school_links",
                    "stamp_start", "stamp_end", "get_status")
    search_fields = ("name", "uuid",
                     "schools__name", "schools__uuid",
                     )
    autocomplete_fields = ("schools",)


admin.site.register(Campaign, CampaignAdmin)


class SurveyAdmin(BaseAdmin):
    list_display = ("__str__", 'status', 'stamp')
    search_fields = ("campaign__name", "campaign__uuid",
                     "school__name", "school__uuid",
                     "user__username", "user__email", 
                     "user__first_name", "user__last_name",
                     )
    list_filter = ('status', 'kind', )
    readonly_fields = ('stamp', )


admin.site.register(Survey, SurveyAdmin)
