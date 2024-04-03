from dateutil import tz
from dateutil.parser import parse
from dateutil.utils import default_tzinfo
from rest_framework import serializers
from .models import Campaign, School, Cascho, Survey


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'


class GeoSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['name', 'address', 'lat', 'lng']


class CampaignSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Campaign
        fields = '__all__'


class CaschoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cascho
        fields = '__all__'


class SurveySerializer(serializers.ModelSerializer):
    campaign = CampaignSerializer(many=False, read_only=True)
    school = SchoolSerializer(many=False, read_only=True)
    def_orig = GeoSchoolSerializer(source='school', many=False, read_only=True)
    def_dest = GeoSchoolSerializer(source='school', many=False, read_only=True)
    status = serializers.SerializerMethodField()
    must_fillout = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = '__all__'

    def get_status(self, obj):
        return obj.Status.CANCELLED if obj.status in [obj.Status.EMPTY, obj.Status.FILLED] and not obj.campaign.is_active else obj.status

    def get_must_fillout(self, obj):
        return obj.status == obj.Status.EMPTY and obj.campaign.is_active

    def get_can_edit(self, obj):
        return obj.status in [obj.Status.EMPTY, obj.Status.FILLED] and obj.campaign.is_active


class SurveyContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Survey
        fields = ['content']


class SurveyStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Survey
        fields = ['status']


class HarvestSerializer(serializers.ModelSerializer):
    campaign = serializers.ReadOnlyField(source='campaign.uuid')
    school = serializers.ReadOnlyField(source='school.uuid')
    def_orig = GeoSchoolSerializer(source='school', many=False, read_only=True)
    def_dest = GeoSchoolSerializer(source='school', many=False, read_only=True)

    class Meta:
        model = Survey
        fields = [
            'id',
            'campaign', 'school',
            'kind',
            'stamp',
            'def_orig', 'def_dest',
            'content'
        ]


class TripSerializer(serializers.ModelSerializer):
    campaign = serializers.ReadOnlyField(source='campaign.uuid')
    school = serializers.ReadOnlyField(source='school.uuid')
    stages = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = [
            'id',
            'campaign', 'school',
            'kind',
            'stamp',
            'stages'
        ]

    def get_stages(self, obj):
        res = []
        content = obj.content
        if type(obj.content) is dict:
            tzone = tz.gettz(content.get('TZ'))
            def_orig = GeoSchoolSerializer(
                instance=obj.school, many=False, read_only=True).data
            def_dest = GeoSchoolSerializer(
                instance=obj.school, many=False, read_only=True).data
            orig = content.get('orig') or def_orig or None
            orig_stamp = content.get('orig_stamp') or None
            for stage in content.get('stages', []):
                if not orig or not orig_stamp:
                    continue
                if not type(stage) is dict:
                    continue
                stage.setdefault('orig', orig)
                stage.setdefault('orig_stamp', orig_stamp)
                stage.setdefault('dest', def_dest)
                orig = stage.get('dest') or None
                orig_stamp = stage.get('dest_stamp') or None
                stage['orig_stamp'] = default_tzinfo(
                    parse(stage['orig_stamp']), tzone).isoformat()
                stage['dest_stamp'] = default_tzinfo(
                    parse(stage['dest_stamp']), tzone).isoformat()
                res.append(stage)
        return res
