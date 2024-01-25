from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.conf import settings
from requests.auth import HTTPBasicAuth  # Import HTTPBasicAuth for basic authentication
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import scrap_instagram,process_followers_dry
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user

# Create your views here.
# views.py

from rest_framework import viewsets
from .models import Score, QualificationAlgorithm, Scheduler, LeadSource
from .serializers import ScoreSerializer, QualificationAlgorithmSerializer, SchedulerSerializer, LeadSourceSerializer

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

class QualificationAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = QualificationAlgorithm.objects.all()
    serializer_class = QualificationAlgorithmSerializer

class SchedulerViewSet(viewsets.ModelViewSet):
    queryset = Scheduler.objects.all()
    serializer_class = SchedulerSerializer

class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.all()
    serializer_class = LeadSourceSerializer

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        scrap_instagram.delay(accounts,followers)
        return Response({"success":True},status=status.HTTP_200_OK)

# airflow_integration/views.py
class AirflowIntegration(APIView):
    def post(self,request):
        # airflow_integration/views.py
        api_url = f'{settings.AIRFLOW_API_BASE_URL}/dags'

        # Define your DAG configuration
        dag_config = {
            "dag_id": "dag_test",
            "schedule_interval": "0 0 * * *",
            "default_args": {
                "owner": "airflow",
                "start_date": "2024-01-01",
                "email_on_failure": False,
                "email_on_retry": False,
                "retries": 1,
                "retry_delay": "5 minutes",
            },
            "tasks": [
                {"task_id": "start_task", "operator": "dummy_operator.DummyOperator", "depends_on_past": False},
                # Add more tasks as needed
            ],
        }
        username = "admin"
        password = "t2bwES9GP64thhsz"

        # Use basic authentication with the provided username and password
        auth = HTTPBasicAuth(username, password)


        try:
            # Make the POST request with basic authentication
            response = requests.post(api_url, json=dag_config, auth=auth)

            if response.status_code == 200:
                data = response.json()
                return JsonResponse(data, safe=False)
            else:
                return JsonResponse({'error': f'Failed to create Airflow DAG. Status code: {response.status_code}'}, status=500)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Request failed. Error: {str(e)}'}, status=500)


class InstagramMoxieCsv(APIView):
    def post(self, request):
        client = login_user(username='matisti96', password='luther1996-')
        _, cursor = client.user_followers_gql_chunk(client.user_id_from_username(request.data.get('username')), max_amount=100)
        process_followers_dry.delay(cursor,request.data.get('username'))
        return Response({"success":True},status=status.HTTP_200_OK)
