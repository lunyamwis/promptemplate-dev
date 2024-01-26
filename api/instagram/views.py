import yaml
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .tasks import scrap_instagram,process_followers_dry
from boostedchatScrapper.spiders.helpers.instagram_login_helper import login_user
from api.helpers.dag_generator import generate_dag
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

class InstagramScrapper(APIView):
    def post(self,request):
        accounts = request.data.get("accounts",[])
        followers = request.data.get("get_followers")
        scrap_instagram.delay(accounts,followers)
        return Response({"success":True},status=status.HTTP_200_OK)

# airflow_integration/views.py


class InstagramMoxieCsv(APIView):
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
            # Create a dictionary from the serializer data
            data_dict = serializer.data
            print(data_dict)
            # import pdb;pdb.set_trace()
            # Write the dictionary to a YAML file
            yaml_file_path = os.path.join(settings.BASE_DIR, 'api','helpers',
                            'include','dag_configs', f"{data_dict['dag_id']}_config.yaml")
            with open(yaml_file_path, 'w') as yaml_file:
                try:
                    yaml.dump(data_dict, yaml_file, default_flow_style=False)
                except Exception as error:
                    return Response({'error': str(error)}, status=400)

            try:
                generate_dag()
            except Exception as error:
                return Response({'error': str(error)}, status=400)
            return Response({'status': 'success', 'message': 'DAG config created and YAML file saved'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'Invalid input data'}, status=400)