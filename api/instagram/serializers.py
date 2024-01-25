# serializers.py

from rest_framework import serializers
from .models import Score, QualificationAlgorithm, Scheduler, LeadSource

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'

class QualificationAlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualificationAlgorithm
        fields = '__all__'

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = '__all__'

class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = '__all__'
