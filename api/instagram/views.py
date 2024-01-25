from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.models import DAG
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

        try:
            # Specify the DAG ID you want to create
            dag_id = 'my_dag'

            # Instantiate a DAG
            dag = DAG(
                dag_id=dag_id,
                schedule_interval=timedelta(days=1),  # Set the schedule interval for daily execution
                default_args={
                    'owner': 'airflow',
                    'depends_on_past': False,
                    'start_date': datetime(2024, 1, 1),
                    'email_on_failure': False,
                    'email_on_retry': False,
                    'retries': 1,
                    'retry_delay': timedelta(minutes=5),
                }
            )

            # Create tasks using SimpleHttpOperator
            start_task = SimpleHttpOperator(
                task_id='start_task',
                http_conn_id='my_http_connection',  # Specify the connection ID configured in Airflow for the API endpoint
                method='POST',
                endpoint='/dags',
                data={"key":"value"},  # Convert DAG configuration to JSON and send it in the request body
                headers={"Content-Type": "application/json"},
                response_check=lambda response: True if response.status_code == 200 else False,
                dag=dag,
            )

            # Add more tasks as needed

            # Set task dependencies
            start_task

            # Trigger the DAG run by executing the first task
            start_task.execute(context={})

            return Response({'success': 'Airflow DAG creation initiated successfully'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)



class InstagramMoxieCsv(APIView):
    def post(self, request):
        client = login_user(username='matisti96', password='luther1996-')
        _, cursor = client.user_followers_gql_chunk(client.user_id_from_username(request.data.get('username')), max_amount=100)
        process_followers_dry.delay(cursor,request.data.get('username'))
        return Response({"success":True},status=status.HTTP_200_OK)
