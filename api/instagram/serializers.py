# serializers.py

from rest_framework import serializers
from .models import Score, QualificationAlgorithm, Scheduler, LeadSource

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "linear_scale_capacity": {"required": False, "allow_null": True},
        }

class QualificationAlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualificationAlgorithm
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "account_usernames":{"required": False, "allow_null": True},
            "photo_links":{"required": False, "allow_null": True},
            "hashtags":{"required": False, "allow_null": True},
            "google_maps_search_keywords":{"required": False, "allow_null": True}
        }


class SetupScrapperSerializer(serializers.Serializer):
    dag_id = serializers.CharField()
    schedule_interval = serializers.CharField()
    catchup = serializers.BooleanField()
    input = serializers.IntegerField()