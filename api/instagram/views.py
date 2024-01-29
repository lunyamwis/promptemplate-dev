import yaml
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .tasks import scrap_followers_similar_accounts,process_followers_dry
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

class GetFollowersOrSimilarAccounts(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        scrap_followers_similar_accounts.delay(accounts,followers)
        return Response({"success":True},status=status.HTTP_200_OK)



class GetFollowersToCSV(APIView):
    def post(self, request):
        client = login_user(username='matisti96', password='luther1996-')
        _, cursor = client.user_followers_gql_chunk(client.user_id_from_username(request.data.get('username')), max_amount=100)
        process_followers_dry.delay(cursor,request.data.get('username'))
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
            for source in sources:
                if source.criterion == 0 or source.criterion == 1:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapFollowersOrSimilarAccounts/",
                        "info":{
                            "accounts": source.account_usernames,
                            "get_followers": source.criterion 
                        }
                    }
                if collect_as_csv:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapFollowersOrSimilarAccounts/",
                        "info":{
                            "accounts": source.account_usernames,
                            "get_followers": source.criterion 
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