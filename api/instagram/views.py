import yaml
import os
import pandas as pd
import subprocess

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from .tasks import scrap_followers,scrap_info,scrap_users,insert_and_enrich
from api.helpers.dag_generator import generate_dag
from api.helpers.date_helper import datetime_to_cron_expression

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
    
class ScrapGmaps(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "gmaps"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapAPI(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "api"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ScrapURL(APIView):

    def get(self,request):
        try:
            # Execute Scrapy spider using the command line
            subprocess.run(["scrapy", "crawl", "webcrawler"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ScrapUsers(APIView):
    def post(self,request):
        query = request.data.get("query")
        if isinstance(query,list):
            for name in query:
                scrap_users.delay(name)
        else:
            scrap_users.delay(query)
        return Response({"success":True},status=status.HTTP_200_OK)

class ScrapInfo(APIView):
    def post(self,request):
        delay_before_requests = int(request.data.get("delay_before_requests",[]))
        delay_after_requests = int(request.data.get("delay_after_requests"))
        step = int(request.data.get("step"))
        accounts = int(request.data.get("accounts"))
        round = int(request.data.get("round"))
        scrap_info.delay(delay_before_requests,delay_after_requests,step,accounts,round)
        return Response({"success":True},status=status.HTTP_200_OK)
    



class ScrapApi(APIView):
    def post(self,request):
        delay_before_requests = int(request.data.get("delay_before_requests",[]))
        delay_after_requests = int(request.data.get("delay_after_requests"))
        step = int(request.data.get("step"))
        accounts = int(request.data.get("accounts"))
        round = int(request.data.get("round"))
        scrap_info.delay(delay_before_requests,delay_after_requests,step,accounts,round)
        return Response({"success":True},status=status.HTTP_200_OK)

class InsertAndEnrich(APIView):
    def post(self,request):
        keywords_to_check = request.data.get("keywords_to_check")
        round_ = request.data.get("round")
        insert_and_enrich.delay(keywords_to_check,round_)
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
                enrich = data_dict.get('enrich')
            except Exception as error:
                return Response({'error': str(error)}, status=400)
            
            try:
                round_ = data_dict.get('round')
            except Exception as error:
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
                        "method": "POST",
                        "info":{
                            "username": source.account_usernames,
                            "delay": source.criterion or 5
                        }
                    }
                if source.criterion == 2:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapUsers/",
                        "method": "POST",
                        "info":{
                            "query": source.estimated_usernames
                        }
                    }
                if source.criterion == 6:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapGmaps/",
                        "method": "GET",
                        "info":{}
                    }
                if source.criterion == 7:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapURL/",
                        "method": "GET",
                        "info":{}
                    }

                if source.criterion == 8:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapAPI/",
                        "method": "GET",
                        "info":{}
                    }

                if enrich:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/scrapInfo/",
                        "method": "POST",
                        "info":{
                                "delay_before_requests":4,
                                "delay_after_requests":14,
                                "step":3,
                                "accounts":18,
                                "round":round_
                            }
                    }

                if make_infinite:
                    data = {
                        "dag_id": source.name,
                        "schedule_interval": datetime_to_cron_expression(schedule.scrapper_starttime),
                        "endpoint": "instagram/insertAndEnrich/",
                        "method": "POST",
                        "info":{
                            "keywords_to_check": qualification_algorithm.positive_keywords,
                            "round": round_
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