import yaml
import os
import pandas as pd

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .tasks import scrap_followers,scrap_info,scrap_users,insert_and_enrich
from boostedchatScrapper.spiders.instagram import InstagramSpider
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from api.helpers.dag_generator import generate_dag
from api.helpers.date_helper import datetime_to_cron_expression
# Create your views here.
# views.py

from rest_framework import viewsets
from .models import Score, QualificationAlgorithm, Scheduler, LeadSource
from .serializers import ScoreSerializer, QualificationAlgorithmSerializer, SchedulerSerializer, LeadSourceSerializer, SetupScrapperSerializer

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


class ScrapFollowers(APIView):
    def post(self, request):
        username = request.data.get("username")
        delay = request.data.get("delay")
        if isinstance(username,list):
            for account in username:
                scrap_followers.delay(account,delay)
        else:
            scrap_followers.delay(username,delay)
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapUsers(APIView):
    def post(self,request):
        query = request.data.get("query")
        scrap_users.delay(query)
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapInfo(APIView):
    def post(self,request):
        delay_before_requests = request.data.get("delay_before_requests",[])
        delay_after_requests = request.data.get("delay_after_requests")
        step = request.data.get("step")
        accounts = request.data.get("accounts")
        round = request.data.get("round")
        scrap_info.delay(delay_before_requests,delay_after_requests,step,accounts,round)
        return Response({"success":True},status=status.HTTP_200_OK)

class InsertAndEnrich(APIView):
    def post(self,request):
        account_data = request.data.get("account_data",[])
        outsourced_data = request.data.get("outsourced_data")
        keywords_to_check = request.data.get("keywords_to_check")
        insert_and_enrich.delay(account_data,outsourced_data,keywords_to_check)
        return Response({"success":True},status=status.HTTP_200_OK)
    

class SetupScrapper(APIView):
    def post(self, request):
        
        try:
            request.data
        except Exception as error:
            return Response({'error': str(error)}, status=400)
        serializer = SetupScrapperSerializer(data=request.data)
        if serializer.is_valid():
            data_dict = serializer.data
            try:
                qualification_algorithm = get_object_or_404(QualificationAlgorithm, id = data_dict.get('qualification_algorithm'))
            except QualificationAlgorithm.DoesNotExist as error:
                return Response({'error': str(error)}, status=400)
            try:
                schedule = get_object_or_404(Scheduler, id = data_dict.get('schedule'))
            except QualificationAlgorithm.DoesNotExist as error:
                return Response({'error': str(error)}, status=400)

            try:
                sources = LeadSource.objects.filter(id__in = data_dict.get('source'))
            except LeadSource.DoesNotExist as error:
                return Response({'error': str(error)}, status=400)
            try:
                collect_as_csv = data_dict.get('collect_as_csv')
            except Exception as error:
                return Response({'error': str(error)}, status=400)
            try:
                make_infinite = data_dict.get('make_infinite')
            except Exception as error:
                return Response({'error': str(error)}, status=400)
            # Create a dictionary from the serializer data
            print(data_dict)
            data = None
            for i,source in enumerate(sources):
                if source.criterion == 0 or source.criterion == 1 and not make_infinite:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapFollowers/",
                        "info":{
                            "username": source.account_usernames,
                            "delay": source.criterion or 5
                        }
                    }
                
                
            # Write the dictionary to a YAML file
            yaml_file_path = os.path.join(settings.BASE_DIR, 'api','helpers',
                            'include','dag_configs', f"{source.name}_config.yaml")
            with open(yaml_file_path, 'w') as yaml_file:
                try:
                    yaml.dump(data, yaml_file, default_flow_style=False)
                except Exception as error:
                    return Response({'error': str(error)}, status=400)

            try:
                generate_dag()
            except Exception as error:
                return Response({'error': str(error)}, status=400)
            return Response({'status': 'success', 'message': 'DAG config created and YAML file saved'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'Invalid input data'}, status=400)